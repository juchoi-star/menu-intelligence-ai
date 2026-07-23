"""벌툰(만화/보드게임카페, ㈜아이센스에프앤비) POS "상품별 매출" 파서.

특징:
  - .xlsx (진짜 엑셀). 용량이 커서 한 달 데이터가 여러 파일(날짜 범위)로 쪼개진다.
    예) 2026-05-01~05-14 / 2026-05-15~05-31 → 두 파일을 합쳐야 5월 전체.
  - 레이아웃: 1행 제목(기간 포함), 3행 헤더(번호·대분류·상품코드·상품명·판매수·결제합계
    ·옵션상품코드·옵션상품명·수량·금액), 4행 '합계'(제거), 5행~ 상품.
  - 상품 행 사이에 옵션 행(H~K만 존재, 번호 없음)이 섞여 있다 → 상품 행만 사용.

상품 단위(대분류/상품명/판매수/결제합계) 구조라 PC 분석기(:mod:`app.core.pc_analyzer`)를
그대로 재사용할 수 있도록 :class:`PCParsedFile` 형태로 반환한다.
"""

from __future__ import annotations

import io
import re
import warnings
from dataclasses import dataclass

from openpyxl import load_workbook

from app.core.pc_parser import PCCategory, PCParsedFile, PCProduct

warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")

# 컬럼(1-based): B..K
_COL = {
    "no": 2, "category": 3, "code": 4, "name": 5,
    "qty": 6, "sales": 7,
    "opt_code": 8, "opt_name": 9, "opt_qty": 10, "opt_amount": 11,
}


class BeltoonParserError(ValueError):
    pass


@dataclass
class _RawProduct:
    code: str
    name: str
    category: str
    qty: float
    sales: float


def _num(v) -> float:
    if v is None:
        return 0.0
    if isinstance(v, (int, float)):
        return float(v)
    text = str(v).strip().replace(",", "")
    try:
        return float(text)
    except ValueError:
        return 0.0


def _clean(v) -> str | None:
    if v is None:
        return None
    s = str(v).strip()
    return s or None


def _find_header_row(ws, max_scan: int = 10) -> int:
    for r in range(1, max_scan + 1):
        vals = {str(ws.cell(r, c).value).strip() if ws.cell(r, c).value else "" for c in range(1, 12)}
        if "상품명" in vals and "판매수" in vals:
            return r
    raise BeltoonParserError("헤더 행(상품명/판매수)을 찾지 못했습니다. 벌툰 파일이 맞는지 확인하세요.")


def _extract_period(ws) -> tuple[str | None, str | None]:
    pat = re.compile(r"(\d{4}-\d{2}-\d{2})\s*~\s*(\d{4}-\d{2}-\d{2})")
    for r in range(1, 4):
        for c in range(1, 12):
            text = ws.cell(r, c).value
            if text:
                m = pat.search(str(text))
                if m:
                    return m.group(1), m.group(2)
    return None, None


def _parse_one(source) -> tuple[list[_RawProduct], tuple[str | None, str | None]]:
    if isinstance(source, bytes):
        wb = load_workbook(io.BytesIO(source), data_only=True)
    else:
        wb = load_workbook(source, data_only=True)
    try:
        ws = wb.active
        header = _find_header_row(ws)
        period = _extract_period(ws)
        out: list[_RawProduct] = []
        for r in range(header + 1, ws.max_row + 1):
            no = ws.cell(r, _COL["no"]).value
            # 상품 행만: 번호가 숫자 (합계행 B='합계', 옵션행 B=None 은 제외)
            if not isinstance(no, (int, float)):
                continue
            name = _clean(ws.cell(r, _COL["name"]).value)
            code = _clean(ws.cell(r, _COL["code"]).value)
            if not name:
                continue
            out.append(
                _RawProduct(
                    code=code or name,
                    name=name,
                    category=_clean(ws.cell(r, _COL["category"]).value) or "미분류",
                    qty=_num(ws.cell(r, _COL["qty"]).value),
                    sales=_num(ws.cell(r, _COL["sales"]).value),
                )
            )
        if not out:
            raise BeltoonParserError("상품 데이터를 찾지 못했습니다.")
        return out, period
    finally:
        wb.close()


def parse_beltoon_files(sources: list) -> PCParsedFile:
    """여러 벌툰 파일(같은 달의 분할본)을 합쳐 하나의 :class:`PCParsedFile` 로 반환.

    상품코드 기준으로 판매수·결제합계를 합산한다. 단가는 결제합계/판매수(평균)로 산출.
    """
    if not sources:
        raise BeltoonParserError("파일이 없습니다.")

    merged: dict[str, list] = {}   # code -> [name, category, qty, sales]
    starts: list[str] = []
    ends: list[str] = []

    for src in sources:
        raws, (start, end) = _parse_one(src)
        if start:
            starts.append(start)
        if end:
            ends.append(end)
        for rp in raws:
            acc = merged.setdefault(rp.code, [rp.name, rp.category, 0.0, 0.0])
            acc[2] += rp.qty
            acc[3] += rp.sales

    products = [
        PCProduct(
            name=v[0],
            unit_price=(v[3] / v[2]) if v[2] else 0.0,
            qty=v[2],
            sales=v[3],
        )
        for v in merged.values()
    ]

    # 분류(대분류) 집계
    cat: dict[str, list[float]] = {}
    for v in merged.values():
        c = cat.setdefault(v[1], [0.0, 0.0])
        c[0] += v[2]
        c[1] += v[3]
    categories = [PCCategory(name=n, qty=q, sales=s) for n, (q, s) in cat.items()]

    period = None
    if starts and ends:
        period = f"{min(starts)} ~ {max(ends)}"

    return PCParsedFile(products=products, categories=categories, output_date=period)
