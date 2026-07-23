"""수동 별칭표 스키마."""

from __future__ import annotations

from pydantic import BaseModel, Field


class AliasGroup(BaseModel):
    canonical: str                              # 대표 메뉴명
    members: list[str] = Field(default_factory=list)  # 같은 메뉴로 볼 변형 이름들


class AliasSetBody(BaseModel):
    groups: list[AliasGroup] = Field(default_factory=list)
