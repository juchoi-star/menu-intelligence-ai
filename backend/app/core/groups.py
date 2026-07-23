"""메뉴분류 → 상위 그룹(주류/막걸리/음식/기타) 매핑.

메뉴개발팀 관점에서 주류·막걸리·음식은 매출 동학이 달라 분리 분석한다.
술(참이슬 등)이 음식 순위에 섞이지 않도록 그룹별로 순위를 매긴다.
  - 주류: 소주/맥주/양주 등
  - 막걸리: 막걸리 메뉴
  - 음식: 조리 메뉴
  - 기타: 음료(비주류)·이벤트·금액조정·직원호출 등 비핵심

새로운 분류가 등장하면 안전하게 '기타'로 폴백한다.
"""

from __future__ import annotations

GROUP_LIQUOR = "주류"
GROUP_MAKGEOLLI = "막걸리"
GROUP_FOOD = "음식"
GROUP_ETC = "기타"

# 대시보드/탭 표기 순서
GROUP_ORDER: list[str] = [GROUP_LIQUOR, GROUP_MAKGEOLLI, GROUP_FOOD, GROUP_ETC]

# 분류명 → 그룹 (POS '메뉴별 매출 순위 집계' 기준)
CATEGORY_GROUP: dict[str, str] = {
    # 주류
    "주류": GROUP_LIQUOR,
    # 막걸리
    "막걸리메뉴": GROUP_MAKGEOLLI,
    # 음식
    "전": GROUP_FOOD,
    "탕&식사": GROUP_FOOD,
    "간단안주": GROUP_FOOD,
    "세트": GROUP_FOOD,
    "튀김": GROUP_FOOD,
    # 기타
    "음료": GROUP_ETC,
    "이벤트": GROUP_ETC,
    "기타": GROUP_ETC,
    "직원호출": GROUP_ETC,
    "미분류": GROUP_ETC,
}


def group_for(category: str | None) -> str:
    """분류명을 상위 그룹으로 변환. 미등록 분류는 '기타'로 폴백."""
    if not category:
        return GROUP_ETC
    return CATEGORY_GROUP.get(category.strip(), GROUP_ETC)
