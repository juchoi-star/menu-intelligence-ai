"""피씨(PC방) 파서·분석 테스트."""

from __future__ import annotations

from app.core.pc_analyzer import analyze_pc
from app.core.pc_parser import PCCategory, PCParsedFile, PCProduct, parse_pc_html


def test_whitespace_variants_merge():
    """띄어쓰기만 다른 동일 상품/분류는 취합되고, 월간 매칭도 병합된다."""
    prev = PCParsedFile(
        products=[PCProduct("1리터 아메리카노", 4000, 10, 40000),
                  PCProduct("1리터아메리카노", 4000, 5, 20000)],
        categories=[PCCategory("음료 (ICE)", 15, 60000), PCCategory("음료(ICE)", 0, 0)],
    )
    curr = PCParsedFile(
        products=[PCProduct("1리터아메리카노", 4000, 20, 80000)],
        categories=[PCCategory("음료(ICE)", 20, 80000)],
    )
    res = analyze_pc(prev, curr, "5월", "6월")
    ame = [p for p in res.products if "아메리카노" in p.name]
    assert len(ame) == 1                      # 3개 표기가 1개로 병합
    assert ame[0].prev.sales == 60000         # 40000 + 20000
    assert ame[0].curr.sales == 80000
    assert ame[0].is_new is False             # 신규 오분류 아님
    assert ame[0].sales_growth_pct == round((80000 - 60000) / 60000 * 100, 2)
    # 분류도 병합
    ice = [c for c in res.categories if c.qty_curr == 20]
    assert len(ice) == 1

# 상품 테이블 2개(매출액 기준/판매개수 기준 = 동일 상품)+ 분류 테이블 1개 재현
_HTML = """<html><head><meta charset='utf-8'></head><body>
- 출력일 : 2026.07.02
<table>
<tr><td>순위</td><td>상품명</td><td>판매가격</td><td>판매개수</td><td>매출액</td><td>매출액 점유율</td></tr>
<tr><td>1</td><td>아메리카노</td><td>2000</td><td>100</td><td>200000</td><td>50%</td></tr>
<tr><td>2</td><td>라면</td><td>3000</td><td>50</td><td>150000</td><td>37%</td></tr>
</table>
<table>
<tr><td>순위</td><td>상품명</td><td>판매가격</td><td>판매개수</td><td>매출액</td><td>판매개수 점유율</td></tr>
<tr><td>1</td><td>아메리카노</td><td>2000</td><td>100</td><td>200000</td><td>66%</td></tr>
<tr><td>2</td><td>라면</td><td>3000</td><td>50</td><td>150000</td><td>33%</td></tr>
</table>
<table>
<tr><td>순위</td><td>상품 분류명</td><td>판매개수</td><td>매출액</td><td>매출액 점유율</td></tr>
<tr><td>1</td><td>음료</td><td>100</td><td>200000</td><td>57%</td></tr>
<tr><td>2</td><td>면</td><td>50</td><td>150000</td><td>42%</td></tr>
</table>
</body></html>"""


def test_pc_parser_no_double_count():
    """상품 테이블이 2개여도 중복 합산하지 않는다(첫 테이블만)."""
    pf = parse_pc_html(_HTML)
    assert pf.output_date == "2026.07.02"
    assert len(pf.products) == 2
    ame = next(p for p in pf.products if p.name == "아메리카노")
    assert ame.sales == 200000  # 400000(2배) 아님
    assert ame.qty == 100
    assert ame.unit_price == 2000
    total = sum(p.sales for p in pf.products)
    assert total == 350000
    # 분류
    assert len(pf.categories) == 2
    assert next(c for c in pf.categories if c.name == "음료").sales == 200000


def test_pc_analyzer_growth_and_rank():
    prev = parse_pc_html(_HTML)
    # 당월: 아메리카노 매출 2배, 라면 신규중단 테스트용으로 제거 + 신상품 추가
    curr_html = _HTML.replace(
        "<tr><td>2</td><td>라면</td><td>3000</td><td>50</td><td>150000</td><td>37%</td></tr>",
        "<tr><td>2</td><td>콜라</td><td>1500</td><td>200</td><td>300000</td><td>40%</td></tr>",
        1,  # 첫 상품테이블만 교체
    ).replace(
        "<tr><td>1</td><td>아메리카노</td><td>2000</td><td>100</td><td>200000</td><td>50%</td></tr>",
        "<tr><td>1</td><td>아메리카노</td><td>2000</td><td>200</td><td>400000</td><td>50%</td></tr>",
        1,
    )
    curr = parse_pc_html(curr_html)
    res = analyze_pc(prev, curr, "6월", "7월")

    by = {p.name: p for p in res.products}
    # 아메리카노: 매출 200000 -> 400000 = +100%
    assert by["아메리카노"].sales_growth_pct == 100.0
    # 콜라: 신규
    assert by["콜라"].is_new is True
    # 라면: 당월 없음 -> 중단
    assert by["라면"].is_discontinued is True
    # 순위: 당월 콜라(300000) > 아메리카노(400000)? 아메 400000 > 콜라 300000 → 아메 1위
    assert by["아메리카노"].rank_curr == 1
    assert res.dashboard.total_sales_curr == 700000
    assert res.meta.curr_label == "7월"
