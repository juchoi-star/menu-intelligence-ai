"""이름 정규화 + 별칭표 취합 테스트.

핵심: 별칭표에 등록한 표기와 데이터의 표기가 공백/구두점/대소문자만
다를 때도 같은 대표명으로 취합되어야 한다(정규화 매칭).
"""

from __future__ import annotations

from app.core.text import build_alias_map, canonical_key, display_name, normalize_name


def test_normalize_strips_space_punct_case():
    assert normalize_name("아메리카노 (ICE)") == normalize_name("아메리카노(ice)")
    assert normalize_name("1리터 아메리카노") == normalize_name("1리터아메리카노")


def test_alias_matches_whitespace_variant():
    """'아메리카노(ICE)'로 등록해도 '아메리카노 (ICE)'(공백차)까지 취합된다."""
    amap = build_alias_map(
        [{"canonical": "아이스 아메리카노", "members": ["아메리카노(ICE)", "차가운 아메리카노"]}]
    )
    # 등록 표기와 공백만 다른 실제 데이터 표기
    assert display_name("아메리카노 (ICE)", amap) == "아이스 아메리카노"
    # 취합 키가 동일 → 한 메뉴로 합쳐진다
    assert canonical_key("아메리카노 (ICE)", amap) == canonical_key("아이스 아메리카노", amap)
    assert canonical_key("차가운  아메리카노", amap) == canonical_key("아이스 아메리카노", amap)


def test_alias_none_returns_normalized_self():
    assert canonical_key("김치전", None) == normalize_name("김치전")
    assert display_name("김치전", None) == "김치전"
