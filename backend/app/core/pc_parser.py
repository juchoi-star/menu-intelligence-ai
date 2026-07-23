"""피씨(PC방) POS "매장통계 > 상품 > 순위" 파서.

피씨 POS 는 확장자가 .xls 지만 실제로는 **HTML 표**로 내보내진다.
표준 라이브러리 html.parser 만 사용(외부 의존성 없음).

파일 구조(테이블 3개):
  - 테이블0: 매출액 기준 상품순위  → 순위·상품명·판매가격·판매개수·매출액·매출액 점유율
  - 테이블1: 판매개수 기준 상품순위 (테이블0과 동일 상품, 정렬만 다름 → 사용 안 함)
  - 테이블2: 상품분류 기준 상품순위 → 순위·상품 분류명·판매개수·매출액·매출액 점유율

특징: 전 매장 합산(모든매장), 매출 기간 표기 없음(출력일만 존재).
따라서 전월/당월 판별은 업로드 순서(슬롯)로 처리한다.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from html.parser import HTMLParser


@dataclass(frozen=True)
class PCProduct:
    name: str
    unit_price: float = 0.0
    qty: float = 0.0          # 판매개수
    sales: float = 0.0        # 매출액


@dataclass(frozen=True)
class PCCategory:
    name: str
    qty: float = 0.0
    sales: float = 0.0


@dataclass
class PCParsedFile:
    products: list[PCProduct] = field(default_factory=list)
    categories: list[PCCategory] = field(default_factory=list)
    output_date: str | None = None


class PCParserError(ValueError):
    """피씨 HTML 포맷이 예상과 다를 때."""


class _TableExtractor(HTMLParser):
    """모든 <table> 을 행렬(list[list[str]])로 추출."""

    def __init__(self) -> None:
        super().__init__()
        self.tables: list[list[list[str]]] = []
        self._cur: list[list[str]] | None = None
        self._row: list[str] | None = None
        self._cell: str | None = None

    def handle_starttag(self, tag: str, attrs: object) -> None:
        if tag == "table":
            self._cur = []
        elif tag == "tr" and self._cur is not None:
            self._row = []
        elif tag in ("td", "th") and self._row is not None:
            self._cell = ""

    def handle_endtag(self, tag: str) -> None:
        if tag == "table" and self._cur is not None:
            self.tables.append(self._cur)
            self._cur = None
        elif tag == "tr" and self._row is not None:
            self._cur.append(self._row)  # type: ignore[union-attr]
            self._row = None
        elif tag in ("td", "th") and self._cell is not None:
            self._row.append(self._cell.strip())  # type: ignore[union-attr]
            self._cell = None

    def handle_data(self, data: str) -> None:
        if self._cell is not None:
            self._cell += data


def _to_float(value: str) -> float:
    """'2,856' / '1.41%' / '28342944' → float. 실패 시 0."""
    if value is None:
        return 0.0
    text = value.strip().replace(",", "").replace("%", "").replace("₩", "")
    if not text:
        return 0.0
    try:
        return float(text)
    except ValueError:
        return 0.0


def _header_index(header: list[str], *keywords: str) -> int | None:
    """헤더에서 키워드를 포함하는 컬럼 인덱스 반환."""
    for i, col in enumerate(header):
        cell = col.replace(" ", "")
        if all(k.replace(" ", "") in cell for k in keywords):
            return i
    return None


def _extract_output_date(html: str) -> str | None:
    m = re.search(r"출력일\s*[:：]\s*(20\d\d[.\-/]\d\d?[.\-/]\d\d?)", html)
    return m.group(1) if m else None


def parse_pc_html(source: str | bytes) -> PCParsedFile:
    """피씨 POS HTML(.xls) 을 파싱한다."""
    if isinstance(source, bytes):
        html = source.decode("utf-8", errors="replace")
    elif source.lstrip().startswith("<") or "\n" in source or "<html" in source[:2000].lower():
        # 이미 HTML 문자열
        html = source
    else:
        # 파일 경로
        with open(source, encoding="utf-8", errors="replace") as f:
            html = f.read()

    extractor = _TableExtractor()
    extractor.feed(html)
    if not extractor.tables:
        raise PCParserError("HTML 표를 찾지 못했습니다. 피씨 POS 파일이 맞는지 확인하세요.")

    products: dict[str, list[float]] = {}   # name -> [price, qty, sales]
    categories: dict[str, list[float]] = {}  # name -> [qty, sales]
    products_done = False   # 테이블0/1 은 동일 상품 → 첫 상품 테이블만 사용(중복 합산 방지)

    for table in extractor.tables:
        if not table:
            continue
        header = table[0]
        # 상품 테이블: 상품명 + 판매개수 + 매출액 컬럼 보유
        i_name = _header_index(header, "상품명")
        i_cat = _header_index(header, "분류명")
        i_price = _header_index(header, "판매가격")
        i_qty = _header_index(header, "판매개수")
        i_sales = _header_index(header, "매출액")

        if i_name is not None and i_sales is not None and not products_done:  # 첫 상품 순위 테이블
            products_done = True
            for row in table[1:]:
                if len(row) <= max(i_name, i_sales):
                    continue
                name = row[i_name].strip()
                if not name:
                    continue
                price = _to_float(row[i_price]) if i_price is not None else 0.0
                qty = _to_float(row[i_qty]) if i_qty is not None else 0.0
                sales = _to_float(row[i_sales])
                acc = products.setdefault(name, [0.0, 0.0, 0.0])
                if price:
                    acc[0] = price
                acc[1] += qty
                acc[2] += sales
        elif i_cat is not None and i_sales is not None:  # 상품분류 순위 테이블
            for row in table[1:]:
                if len(row) <= max(i_cat, i_sales):
                    continue
                name = row[i_cat].strip()
                if not name:
                    continue
                qty = _to_float(row[i_qty]) if i_qty is not None else 0.0
                sales = _to_float(row[i_sales])
                acc = categories.setdefault(name, [0.0, 0.0])
                acc[0] += qty
                acc[1] += sales

    if not products:
        raise PCParserError("상품 데이터를 찾지 못했습니다.")

    return PCParsedFile(
        products=[
            PCProduct(name=n, unit_price=v[0], qty=v[1], sales=v[2])
            for n, v in products.items()
        ],
        categories=[
            PCCategory(name=n, qty=v[0], sales=v[1]) for n, v in categories.items()
        ],
        output_date=_extract_output_date(html),
    )
