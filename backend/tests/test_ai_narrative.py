"""AI 내러티브(규칙 기반) 테스트.

숫자 나열이 아니라 근거 있는 가설(계절·판매량/단가·매장 확산·분류 대비)을
담는지, 그리고 방향이 모순되지 않는지 검증한다.
"""

from __future__ import annotations

from datetime import date

from app.core.ai import _Ctx, _narrative_for, _season_tag, generate_ai_report
from app.core.analyzer import analyze
from app.core.parser import MenuRecord, ParsedFile


def _rec(store, cat, code, name, real, orders, amount=None, discount=0.0):
    amount = real if amount is None else amount
    return MenuRecord(
        store_code=store, store_name=store, category=cat,
        menu_code=code, menu_name=name,
        order_count=orders, order_amount=amount, discount_amount=discount,
        real_sales=real, gross_profit=real * 0.9,
    )


def _make(records, start, end):
    return ParsedFile(period_start=start, period_end=end, scope="테스트", records=records)


def test_season_tag():
    assert _season_tag("화채가꿀떡꿀떡") == "여름"
    assert _season_tag("주전자어묵탕") == "겨울"
    assert _season_tag("청도미나리전") == "봄"
    assert _season_tag("김치전") is None          # 계절성 없는 메뉴


def test_summer_menu_rising_in_june_gets_weather_hypothesis():
    """6월에 여름 메뉴가 올랐으면 '기온이 오르는' 계절 효과를 언급한다."""
    prev = _make([_rec("S1", "간단안주", "M1", "화채가꿀떡꿀떡", 800_000, 80)],
                 date(2026, 5, 1), date(2026, 5, 31))
    curr = _make([_rec("S1", "간단안주", "M1", "화채가꿀떡꿀떡", 1_150_000, 115)],
                 date(2026, 6, 1), date(2026, 6, 30))
    res = analyze(prev, curr)
    text = _narrative_for(res.menus[0], _Ctx(res))
    assert "6월" in text and "여름" in text
    assert "계절" in text


def test_winter_menu_falling_in_june_gets_weather_hypothesis():
    """6월에 겨울 메뉴가 하락하면 날씨 불일치 가설을 언급한다."""
    prev = _make([_rec("S1", "탕&식사", "M2", "주전자어묵탕", 1_000_000, 100)],
                 date(2026, 5, 1), date(2026, 5, 31))
    curr = _make([_rec("S1", "탕&식사", "M2", "주전자어묵탕", 700_000, 70)],
                 date(2026, 6, 1), date(2026, 6, 30))
    res = analyze(prev, curr)
    text = _narrative_for(res.menus[0], _Ctx(res))
    assert "겨울" in text and "6월" in text


def test_price_vs_volume_driver():
    """수량은 줄고 매출이 늘면 '건당 금액 상승'이 주도 요인으로 서술된다."""
    prev = _make([_rec("S1", "간단안주", "M3", "타코와사비", 1_000_000, 100)],
                 date(2026, 5, 1), date(2026, 5, 31))
    curr = _make([_rec("S1", "간단안주", "M3", "타코와사비", 1_200_000, 96)],
                 date(2026, 6, 1), date(2026, 6, 30))
    res = analyze(prev, curr)
    text = _narrative_for(res.menus[0], _Ctx(res))
    assert "건당 금액" in text


def test_store_clause_does_not_contradict_direction():
    """매장이 줄었는데 매출이 늘면 '감소 영향'이 아니라 매장당 개선으로 서술한다."""
    prev = _make(
        [_rec("S1", "튀김", "M4", "깡새우머리튀김", 300_000, 30),
         _rec("S2", "튀김", "M4", "깡새우머리튀김", 300_000, 30)],
        date(2026, 5, 1), date(2026, 5, 31),
    )
    curr = _make([_rec("S1", "튀김", "M4", "깡새우머리튀김", 800_000, 80)],
                 date(2026, 6, 1), date(2026, 6, 30))
    res = analyze(prev, curr)
    text = _narrative_for(res.menus[0], _Ctx(res))
    assert "줄어든 영향이 큽니다" not in text      # 모순 서술 금지
    assert "매장당 판매력이 개선" in text


def test_order_count_sign_not_duplicated():
    """'-3.4% 감소' 처럼 부호가 중복 표기되지 않는다."""
    prev = _make([_rec("S1", "간단안주", "M5", "타코와사비", 1_000_000, 100)],
                 date(2026, 5, 1), date(2026, 5, 31))
    curr = _make([_rec("S1", "간단안주", "M5", "타코와사비", 900_000, 90)],
                 date(2026, 6, 1), date(2026, 6, 30))
    res = analyze(prev, curr)
    text = _narrative_for(res.menus[0], _Ctx(res))
    assert "-" not in text.split("주문건수는")[1].split("%")[0]


def test_report_has_seasonal_recommendation():
    """계절 상승 메뉴가 있으면 추천에 시즌 대응 제안이 포함된다."""
    prev = _make([_rec("S1", "간단안주", "M1", "수박화채", 1_000_000, 100)],
                 date(2026, 5, 1), date(2026, 5, 31))
    curr = _make([_rec("S1", "간단안주", "M1", "수박화채", 1_500_000, 150)],
                 date(2026, 6, 1), date(2026, 6, 30))
    res = analyze(prev, curr)
    report = generate_ai_report(res)          # api_key 없음 → 규칙 기반
    assert report.provider == "rule-based"
    assert any("여름" in r for r in report.recommendations)
