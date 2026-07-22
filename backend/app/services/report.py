"""AI 보고서 PDF 생성.

reportlab 내장 CJK CID 폰트(HYSMyeongJo-Medium)를 사용해
별도 폰트 파일 없이 한글을 렌더링한다.

목차:
  1. 매출 요약  2. 메뉴 성장  3. 메뉴 감소  4. 순위 변화
  5. 가맹점 분석  6. AI 분석  7. 추천 액션
"""

from __future__ import annotations

import io

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.models.schemas import AnalysisResult, MenuInsightItem

_FONT = "HYSMyeongJo-Medium"
_registered = False


def _ensure_font() -> None:
    global _registered
    if not _registered:
        pdfmetrics.registerFont(UnicodeCIDFont(_FONT))
        _registered = True


def _styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle("t", parent=base["Title"], fontName=_FONT, fontSize=20, leading=26),
        "h2": ParagraphStyle("h2", parent=base["Heading2"], fontName=_FONT, fontSize=13, leading=18,
                              textColor=colors.HexColor("#1e293b"), spaceBefore=14, spaceAfter=6),
        "body": ParagraphStyle("b", parent=base["BodyText"], fontName=_FONT, fontSize=10, leading=15),
        "small": ParagraphStyle("s", parent=base["BodyText"], fontName=_FONT, fontSize=8.5,
                                 leading=12, textColor=colors.HexColor("#475569")),
    }


def _won(v: float) -> str:
    return f"{v:,.0f}원"


def _insight_table(items: list[MenuInsightItem], value_header: str, st: dict) -> Table:
    header = ["메뉴", "분류", value_header, "전월→당월 실매출"]
    rows = [header]
    for it in items[:10]:
        rows.append([
            Paragraph(it.menu_name, st["small"]),
            Paragraph(it.category, st["small"]),
            Paragraph(it.detail or str(it.value), st["small"]),
            Paragraph(f"{_won(it.prev_real_sales)} → {_won(it.curr_real_sales)}", st["small"]),
        ])
    if len(rows) == 1:
        rows.append([Paragraph("해당 없음", st["small"]), "", "", ""])
    tbl = Table(rows, colWidths=[45 * mm, 22 * mm, 45 * mm, 55 * mm])
    tbl.setStyle(
        TableStyle([
            ("FONTNAME", (0, 0), (-1, -1), _FONT),
            ("FONTSIZE", (0, 0), (-1, -1), 8.5),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f1f5f9")]),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ])
    )
    return tbl


def build_pdf_report(result: AnalysisResult) -> bytes:
    """분석 결과를 PDF 바이트로 렌더링."""
    _ensure_font()
    st = _styles()
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=18 * mm, rightMargin=18 * mm, topMargin=18 * mm, bottomMargin=16 * mm,
        title=f"Menu Intelligence Report {result.meta.curr_label}",
    )
    d = result.dashboard
    ins = result.insights
    story: list = []

    # 표지 / 타이틀
    story.append(Paragraph("Menu Intelligence AI 분석 보고서", st["title"]))
    story.append(Paragraph(
        f"{result.meta.prev_label} → {result.meta.curr_label} · {result.meta.scope or ''} · "
        f"가맹점 {result.meta.store_count}개",
        st["small"],
    ))
    story.append(Spacer(1, 8 * mm))

    # 1. 매출 요약
    story.append(Paragraph("1. 매출 요약", st["h2"]))
    summary_rows = [
        ["지표", "당월", "전월", "증감"],
        ["실매출", _won(d.total_sales_curr), _won(d.total_sales_prev), f"{d.sales_delta_pct}%"],
        ["주문건수", f"{d.order_count_curr:,.0f}", f"{d.order_count_prev:,.0f}", f"{d.order_delta_pct}%"],
        ["이익률", f"{d.profit_rate_curr}%", f"{d.profit_rate_prev}%", "-"],
        ["할인율", f"{d.discount_rate_curr}%", f"{d.discount_rate_prev}%", "-"],
        ["판매 메뉴수", f"{d.menu_count_curr}", f"{d.menu_count_prev}", "-"],
    ]
    summary_tbl = Table(summary_rows, colWidths=[40 * mm, 42 * mm, 42 * mm, 30 * mm])
    summary_tbl.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), _FONT),
        ("FONTSIZE", (0, 0), (-1, -1), 9.5),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")),
        ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(summary_tbl)
    story.append(Spacer(1, 3 * mm))
    story.append(Paragraph(result.ai.summary, st["body"]))

    # 2. 메뉴 성장
    story.append(Paragraph("2. 메뉴 성장 (상승 TOP10)", st["h2"]))
    story.append(_insight_table(ins.rising_top10, "성장률", st))

    # 3. 메뉴 감소
    story.append(Paragraph("3. 메뉴 감소 (하락 TOP10)", st["h2"]))
    story.append(_insight_table(ins.falling_top10, "감소율", st))

    # 4. 순위 변화
    story.append(Paragraph("4. 순위 변화", st["h2"]))
    story.append(Paragraph("▲ 순위 상승", st["body"]))
    story.append(_insight_table(ins.rank_up, "순위변화", st))
    story.append(Spacer(1, 2 * mm))
    story.append(Paragraph("▼ 순위 하락", st["body"]))
    story.append(_insight_table(ins.rank_down, "순위변화", st))

    # 5. 가맹점 분석
    story.append(Paragraph("5. 가맹점 분석 (당월 실매출 상위)", st["h2"]))
    store_rows = [["가맹점", "실매출", "증감률", "이익률", "메뉴수"]]
    for s in result.stores[:20]:
        store_rows.append([
            Paragraph(s.store_name, st["small"]),
            _won(s.real_sales_curr),
            f"{s.sales_delta_pct}%",
            f"{s.profit_rate_curr}%",
            f"{s.menu_count_curr}",
        ])
    store_tbl = Table(store_rows, colWidths=[60 * mm, 42 * mm, 24 * mm, 22 * mm, 20 * mm])
    store_tbl.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), _FONT),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f1f5f9")]),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")),
        ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(store_tbl)

    # 6. AI 분석
    story.append(Paragraph("6. AI 분석", st["h2"]))
    by_code = {m.menu_code: m for m in result.menus}
    for code, text in list(result.ai.menu_narratives.items())[:12]:
        name = by_code[code].menu_name if code in by_code else code
        story.append(Paragraph(f"• <b>{name}</b> — {text}", st["body"]))
        story.append(Spacer(1, 1.5 * mm))

    # 7. 추천 액션
    story.append(Paragraph("7. 추천 액션", st["h2"]))
    for i, rec in enumerate(result.ai.recommendations, 1):
        story.append(Paragraph(f"{i}. {rec}", st["body"]))
        story.append(Spacer(1, 1.5 * mm))

    doc.build(story)
    return buf.getvalue()
