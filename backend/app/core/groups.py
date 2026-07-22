"""메뉴분류 → 상위 그룹(주류/음식/기타) 매핑.

메뉴개발팀 관점에서 주류(술)와 음식은 매출 동학이 달라 분리 분석한다.
  - 주류: 술(소주/맥주/막걸리 등)
  - 음식: 조리 메뉴
  - 기타: 음료(비주류)·이벤트·금액조정·직원호출 등 비핵심

새로운 분류가 등장하면 안전하게 '기타'로 폴백한다.
"""

from __future__ import annotations

GROUP_LIQUOR = "주류"
GROUP_FOOD = "음식"
GROUP_ETC = "기타"

# 대시보드/탭 표기 순서
GROUP_ORDER: list[str] = [GROUP_LIQUOR, GROUP_FOOD, GROUP_ETC]

# 분류명 → 그룹 (POS '메뉴별 매출 순위 집계' 기준)
CATEGORY_GROUP: dict[str, str] = {
    # 주류
    "주류": GROUP_LIQUOR,
    "막걸리메뉴": GROUP_LIQUOR,
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
