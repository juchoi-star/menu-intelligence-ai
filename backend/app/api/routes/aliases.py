"""수동 별칭표 조회/저장 라우트 (브랜드별 공유).

유사/동의어 메뉴를 하나로 취합하기 위한 사용자 정의 규칙.
분석(compare) 시 해당 브랜드의 별칭표가 자동 적용된다.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.repository import VALID_BRANDS, get_alias_groups, save_alias_groups
from app.models.alias_schemas import AliasGroup, AliasSetBody

router = APIRouter(prefix="/aliases", tags=["aliases"])


def _check_brand(brand: str) -> None:
    if brand not in VALID_BRANDS:
        raise HTTPException(404, f"알 수 없는 브랜드: {brand} (허용: {', '.join(VALID_BRANDS)})")


@router.get("/{brand}", response_model=AliasSetBody)
def get_aliases(brand: str, db: Session = Depends(get_db)) -> AliasSetBody:
    _check_brand(brand)
    return AliasSetBody(groups=[AliasGroup(**g) for g in get_alias_groups(db, brand)])


@router.put("/{brand}", response_model=AliasSetBody)
def put_aliases(brand: str, body: AliasSetBody, db: Session = Depends(get_db)) -> AliasSetBody:
    _check_brand(brand)
    # 대표명이 비어있는 그룹은 제외하고 저장
    groups = [
        {"canonical": g.canonical.strip(), "members": [m.strip() for m in g.members if m.strip()]}
        for g in body.groups
        if g.canonical.strip()
    ]
    save_alias_groups(db, brand, groups)
    return AliasSetBody(groups=[AliasGroup(**g) for g in groups])
