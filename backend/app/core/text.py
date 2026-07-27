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
import unicodedata

# 공백 + 흔한 구두점 제거 (한글은 대소문자 없음, 영문만 lower 효과)
# `\s` 는 유니코드 공백(NBSP·전각공백 등)까지 잡지만, 폭이 없어 눈에 보이지 않는
# 제어문자(U+200B~200D 폭없는공백/결합자, U+FEFF BOM, U+00AD soft hyphen)는
# `\s` 에 해당하지 않아 따로 제거해야 한다. 엑셀·웹 복붙으로 자주 섞여 들어오며,
# 눈에 안 보이는 탓에 같은 이름인데 취합이 안 되는 원인이 된다.
_STRIP = re.compile(
    r"[\s​‌‍⁠﻿­()\[\]{}<>·・|/\\,.!?~'\"`*#&_\-]+"
)

# 유니코드 정규화: 전각 영문/숫자(Ａ→A, １→1)와 조합형 한글(ㄱ+ㅏ)을 표준형으로 통일.
_NFKC = "NFKC"


def normalize_name(name: str | None) -> str:
    """자동 정규화 키: 유니코드 정규화 + 소문자화 + 공백/구두점/비가시문자 제거."""
    if not name:
        return ""
    text = unicodedata.normalize(_NFKC, str(name))
    return _STRIP.sub("", text.strip().lower())


# ---------------------------------------------------------------------------
# 유사명 자동 취합(fuzzy)
#
# 매장마다 같은 상품을 다르게 등록해 키가 갈라지는 문제('아이스아메리카노',
# '아메리카노(ice)', '차가운 아메리카노')를 자동으로 하나로 모은다.
# 방식: 온도·제로 같은 **수식어를 표준 마커로 분리**하고 남은 어간(stem)으로 비교.
#   아이스아메리카노 → 아메리카노 + [ICE]
#   아메리카노(ice)  → 아메리카노 + [ICE]
#   차가운 아메리카노 → 아메리카노 + [ICE]
# 마커는 키에 남기므로 '콜라'와 '콜라제로'는 섞이지 않고,
# '콜라제로'와 '제로콜라'는 같은 키(콜라+[ZERO])가 되어 합쳐진다.
# 용량·수량(300cc, 500, 2p)은 서로 다른 상품이라 절대 제거하지 않는다.
# ---------------------------------------------------------------------------

# 마커별 표기 변형(긴 것부터 매칭해야 '아이스드'가 '아이스'로 잘리지 않는다)
_MODIFIERS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("ICE", ("아이스드", "아이스", "차가운", "iced", "ice", "cold")),
    ("HOT", ("따뜻한", "뜨거운", "핫", "hot", "warm")),
    ("ZERO", ("무설탕", "제로", "zero")),
)

# 수식어가 상품명의 일부인 합성어 — 이런 이름에선 해당 마커를 추출하지 않는다
# (예: '아이스크림'에서 '아이스'를 떼면 '크림'이 되어 엉뚱하게 합쳐진다).
_COMPOUNDS: tuple[str, ...] = (
    "아이스크림", "아이스티", "아이스박스", "아이스팩", "아이스홍시", "아이스와인",
    "핫도그", "핫바", "핫초코", "핫케이크", "핫윙", "핫팩", "핫소스",
)

# 이름 장식용 수식어(상품 구분과 무관) — 제거해 표기차를 흡수한다.
_DECOR: tuple[str, ...] = (
    "신메뉴", "신상품", "신규", "추천", "인기", "베스트", "시즌", "한정", "특가",
    "best", "new",
)

# 어간이 이보다 짧아지면 마커 추출을 취소한다(과도한 병합 방지).
_MIN_STEM = 2


def _extract_modifiers(norm: str) -> tuple[str, tuple[str, ...]]:
    """정규화된 이름에서 수식어 마커를 떼어내고 (어간, 마커들) 반환."""
    stem = norm
    for decor in _DECOR:
        stem = stem.replace(decor, "")
    markers: set[str] = set()
    changed = True
    while changed:                     # '아이스아메리카노ice' 처럼 중복 표기도 정리
        changed = False
        for marker, variants in _MODIFIERS:
            if any(c in stem for c in _COMPOUNDS):
                continue               # 합성어(아이스크림 등)는 건드리지 않는다
            for v in variants:
                if stem.startswith(v):
                    rest = stem[len(v):]
                elif stem.endswith(v):
                    rest = stem[: -len(v)]
                else:
                    continue
                if len(rest) < _MIN_STEM:
                    continue           # 어간이 너무 짧아지면 추출 취소(핫바→바 방지)
                stem, changed = rest, True
                markers.add(marker)
                break
            if changed:
                break
    return stem, tuple(sorted(markers))


def fuzzy_key(name: str | None, alias_map: dict[str, str] | None = None) -> str:
    """유사명 취합 키. 수동 별칭표를 먼저 적용한 뒤 수식어를 표준화한다.

    100% 정확한 분류는 불가능하므로(매장 자유 입력), 안전한 규칙만 적용하고
    남은 예외는 별칭표로 보정한다.
    """
    if not name:
        return ""
    base = _alias_canonical(name, alias_map) or name
    norm = normalize_name(base)
    if not norm:
        return ""
    stem, markers = _extract_modifiers(norm)
    if not stem:                       # 전부 수식어였다면 원본 유지
        return norm
    return stem + ("|" + "+".join(markers) if markers else "")


def _alias_canonical(name: str, alias_map: dict[str, str] | None) -> str | None:
    """별칭표에서 대표명을 찾는다.

    1) 원본 완전일치 우선(가장 정확)
    2) 정규화(공백·구두점·대소문자 제거) 일치 — build_alias_map 이 정규화 키도
       함께 넣어두므로 O(1) 조회로 '아메리카노(ICE)' vs '아메리카노 (ICE)' 같은
       표기차를 흡수한다.
    """
    if not alias_map:
        return None
    return alias_map.get(name) or alias_map.get(normalize_name(name))


def canonical_key(name: str | None, alias_map: dict[str, str] | None = None) -> str:
    """취합 키. 별칭표에 등록된 이름은 대표명으로 치환 후 정규화."""
    if not name:
        return ""
    base = _alias_canonical(name, alias_map) or name
    return normalize_name(base)


def display_name(name: str, alias_map: dict[str, str] | None = None) -> str:
    """표시명: 별칭표의 대표명이 있으면 그것, 없으면 원본."""
    return _alias_canonical(name, alias_map) or name


def build_alias_map(groups: list[dict]) -> dict[str, str]:
    """별칭 그룹 목록 → {변형이름: 대표명} 매핑.

    groups: [{"canonical": "아이스 아메리카노", "members": ["아이스아메리카노","아메리카노(ice)", ...]}]
    대표명 자신도 매핑에 포함(자기 자신)한다.
    표기차(공백/구두점/대소문자)를 흡수하기 위해 **정규화 키도 함께** 등록한다.
    """
    out: dict[str, str] = {}
    for g in groups or []:
        canon = (g.get("canonical") or "").strip()
        if not canon:
            continue
        for variant in [canon, *g.get("members", [])]:
            variant = (variant or "").strip()
            if not variant:
                continue
            out[variant] = canon                    # 원본 표기 그대로
            out.setdefault(normalize_name(variant), canon)  # 정규화 표기(공백/구두점 무시)
    return out
