"""그룹(주류/음식/기타) 분리 분석 테스트."""

from __future__ import annotations

from app.core.analyzer import analyze
from app.core.groups import GROUP_ETC, GROUP_FOOD, GROUP_LIQUOR, group_for
from app.core.parser import MenuRecord, ParsedFile


def test_group_mapping():
    assert group_for("주류") == GROUP_LIQUOR
    assert group_for("막걸리메뉴") == GROUP_LIQUOR
    assert group_for("전") == GROUP_FOOD
    assert group_for("탕&식사") == GROUP_FOOD
    assert group_for("음료") == GROUP_ETC
    assert group_for("직원호출") == GROUP_ETC
    # 미등록 분류는 안전하게 기타로 폴백
    assert group_for("신규분류XYZ") == GROUP_ETC
    assert group_for(None) == GROUP_ETC


def _rec(store, cat, code, name, real, orders=1, amount=None):
    amount = real if amount is None else amount
    return MenuRecord(
        store_code=store, store_name=store, category=cat,
        menu_code=code, menu_name=name,
        order_count=orders, order_amount=amount, real_sales=real,
        gross_profit=real * 0.9,
    )


def _make(records):
    return ParsedFile(period_start=None, period_end=None, scope="테스트", records=records)


def test_rank_is_within_group():
    """주류와 음식은 각각 그룹 내에서 순위가 매겨진다."""
    prev = _make([
        _rec("S1", "주류", "L1", "소주", 100),
        _rec("S1", "전", "F1", "김치전", 100),
    ])
    curr = _make([
        _rec("S1", "주류", "L1", "소주", 500),        # 주류 그룹 1위
        _rec("S1", "주류", "L2", "맥주", 200),        # 주류 그룹 2위
        _rec("S1", "전", "F1", "김치전", 300),        # 음식 그룹 1위
        _rec("S1", "전", "F2", "해물파전", 150),      # 음식 그룹 2위
    ])
    res = analyze(prev, curr)
    by_code = {m.menu_code: m for m in res.menus}
    # 그룹별로 1위가 각각 존재해야 한다
    assert by_code["L1"].rank_curr == 1 and by_code["L1"].group == GROUP_LIQUOR
    assert by_code["F1"].rank_curr == 1 and by_code["F1"].group == GROUP_FOOD
    assert by_code["L2"].rank_curr == 2
    assert by_code["F2"].rank_curr == 2


def test_group_contribution_is_within_group():
    """기여도는 그룹 내 실매출 대비로 계산된다."""
    curr = _make([
        _rec("S1", "주류", "L1", "소주", 800),   # 주류 총 1000 → 80%
        _rec("S1", "주류", "L2", "맥주", 200),
        _rec("S1", "전", "F1", "김치전", 100),   # 음식 총 100 → 100%
    ])
    prev = _make([_rec("S1", "주류", "L1", "소주", 800)])
    res = analyze(prev, curr)
    by_code = {m.menu_code: m for m in res.menus}
    assert by_code["L1"].contribution_pct == 80.0        # 그룹 내
    assert by_code["F1"].contribution_pct == 100.0       # 그룹 내
    # 전체 대비 기여도는 별도 필드
    assert round(by_code["F1"].contribution_overall_pct, 1) == round(100 / 1100 * 100, 1)


def test_group_summaries_present():
    curr = _make([
        _rec("S1", "주류", "L1", "소주", 500),
        _rec("S1", "전", "F1", "김치전", 300),
        _rec("S1", "음료", "E1", "콜라", 50),
    ])
    prev = _make([_rec("S1", "주류", "L1", "소주", 400)])
    res = analyze(prev, curr)
    groups = {g.group: g for g in res.groups}
    assert set(groups) == {GROUP_LIQUOR, GROUP_FOOD, GROUP_ETC}
    # 대시보드 그룹 슬라이스도 동일
    assert {g.group for g in res.dashboard.sales_by_group} == {GROUP_LIQUOR, GROUP_FOOD, GROUP_ETC}
    # 가맹점 그룹별 매출 분해
    assert res.stores[0].group_sales_curr[GROUP_LIQUOR] == 500
