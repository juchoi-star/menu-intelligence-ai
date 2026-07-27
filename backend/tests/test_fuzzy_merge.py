"""유사명 자동 취합(fuzzy) 테스트.

매장마다 같은 상품을 다르게 등록해 키가 갈라지는 문제를 자동으로 합친다.
합쳐야 할 것은 합치고, 서로 다른 상품(용량/제로 여부/합성어)은 절대 섞이지 않아야 한다.
"""

from __future__ import annotations

from app.core.text import build_alias_map, fuzzy_key


def _same(*names: str) -> bool:
    keys = {fuzzy_key(n) for n in names}
    return len(keys) == 1


def test_temperature_variants_merge():
    """온도 표기가 달라도 같은 상품으로 취합된다(사용자 요청 사례)."""
    assert _same(
        "아이스아메리카노",
        "아메리카노(ice)",
        "아메리카노 (ICE)",
        "차가운 아메리카노",
        "아메리카노아이스",
    )


def test_zero_variants_merge():
    """'콜라제로' 와 '제로콜라' 처럼 수식어 위치만 다른 것도 취합된다."""
    assert _same("콜라제로", "제로콜라", "콜라 제로", "제로 콜라")


def test_different_products_do_not_merge():
    """제로 여부·브랜드·용량이 다르면 절대 합쳐지지 않는다."""
    assert fuzzy_key("콜라") != fuzzy_key("콜라제로")          # 일반 vs 제로
    assert fuzzy_key("스프라이트") != fuzzy_key("스프라이트제로")
    assert fuzzy_key("콜라") != fuzzy_key("펩시콜라")           # 브랜드 구분
    assert fuzzy_key("생맥주300cc") != fuzzy_key("생맥주500cc")  # 용량 구분
    assert fuzzy_key("아메리카노") != fuzzy_key("아이스아메리카노")  # 온도 명시 여부


def test_compound_words_protected():
    """'아이스크림'·'핫도그' 처럼 수식어가 이름의 일부면 분해하지 않는다."""
    assert fuzzy_key("아이스크림") == "아이스크림"
    assert fuzzy_key("아이스티") == "아이스티"
    assert fuzzy_key("핫도그") == "핫도그"
    assert fuzzy_key("핫바") == "핫바"
    assert fuzzy_key("핫초코") == "핫초코"
    # 아이스크림이 들어간 파생 상품도 '크림'으로 잘리지 않는다
    assert "크림" in fuzzy_key("아이스크림와플")
    assert fuzzy_key("아이스크림와플") != fuzzy_key("와플")


def test_manual_alias_still_wins():
    """수동 별칭표가 자동 규칙보다 우선한다(자동으로 못 잡는 동의어 보정)."""
    amap = build_alias_map([{"canonical": "아메리카노", "members": ["american coffee"]}])
    assert fuzzy_key("american coffee", amap) == fuzzy_key("아메리카노", amap)


def test_whitespace_only_variants_merge():
    assert _same("생맥주 300cc", "생맥주300cc")
    assert _same("잔 슬러시 막걸리", "잔슬러시막걸리")
