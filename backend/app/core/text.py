"""이름 정규화 + 수동 별칭 취합 유틸.

POS 데이터는 같은 상품/메뉴가 다르게 표기되는 경우가 많다:
  - 띄어쓰기: '1리터 아메리카노' vs '1리터아메리카노'
  - 구두점/대소문자: '아메리카노(ICE)' vs '아메리카노 ice'
  - 단어 자체가 다름(동의어): '아이스아메리카노' vs '차가운 아메리카노'  → 자동으론 위험

자동 규칙은 **공백·구두점·대소문자만** 제거(보수적: '핫도그','아이스크림' 오병합 없음).
그 이상(동의어/맥락)은 사용자가 등록하는 **별칭표(alias_map)** 로 취합한다.
"""

from __future__ import annotations

import re

# 공백 + 흔한 구두점 제거 (한글은 대소문자 없음, 영문만 lower 효과)
_STRIP = re.compile(r"[\s()\[\]{}<>·・|/\\,.!?~'\"`*#&_\-]+")


def normalize_name(name: str | None) -> str:
    """자동 정규화 키: 앞뒤공백 제거 + 소문자화 + 공백/구두점 제거."""
    if not name:
        return ""
    return _STRIP.sub("", name.strip().lower())


def canonical_key(name: str | None, alias_map: dict[str, str] | None = None) -> str:
    """취합 키. 별칭표에 등록된 이름은 대표명으로 치환 후 정규화."""
    if not name:
        return ""
    base = alias_map.get(name, name) if alias_map else name
    return normalize_name(base)


def display_name(name: str, alias_map: dict[str, str] | None = None) -> str:
    """표시명: 별칭표의 대표명이 있으면 그것, 없으면 원본."""
    if alias_map and name in alias_map:
        return alias_map[name]
    return name


def build_alias_map(groups: list[dict]) -> dict[str, str]:
    """별칭 그룹 목록 → {변형이름: 대표명} 매핑.

    groups: [{"canonical": "아이스 아메리카노", "members": ["아이스아메리카노","아메리카노(ice)", ...]}]
    대표명 자신도 매핑에 포함(자기 자신)한다.
    """
    out: dict[str, str] = {}
    for g in groups or []:
        canon = (g.get("canonical") or "").strip()
        if not canon:
            continue
        out[canon] = canon
        for m in g.get("members", []):
            m = (m or "").strip()
            if m:
                out[m] = canon
    return out
