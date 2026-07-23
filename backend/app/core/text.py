"""이름 정규화 유틸.

POS 데이터는 같은 상품/메뉴가 띄어쓰기 차이로 다르게 표기되는 경우가 많다
(예: '1리터 아메리카노' vs '1리터아메리카노', '짜계치' 코드 중복).
취합/월간 매칭 시 공백을 제거한 정규화 키로 동일 상품을 합친다.

공백만 제거(보수적) — '&','/' 같은 구두점 차이는 서로 다른 상품일 수 있어 건드리지 않는다.
"""

from __future__ import annotations

import re

_WS = re.compile(r"\s+")


def normalize_name(name: str | None) -> str:
    """매칭 키용 정규화: 앞뒤 공백 제거 + 내부 모든 공백류 제거."""
    if not name:
        return ""
    return _WS.sub("", name.strip())
