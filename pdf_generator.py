"""
pdf_generator.py  ·  كشف الحساب بالعربية (RTL)
الاتجاه: يمين → يسار
"""

import io
import os
from datetime import datetime

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (Image, PageBreak, Paragraph,
                                SimpleDocTemplate, Spacer, Table, TableStyle)

# ──────────────────────────────────────────────
#  تسجيل خط Amiri
# ──────────────────────────────────────────────
_BASE      = os.path.dirname(os.path.abspath(__file__))
_FONT_REG  = os.path.join(_BASE, "fonts", "Amiri-Regular.ttf")
_FONT_BOLD = os.path.join(_BASE, "fonts", "Amiri-Bold.ttf")

try:
    pdfmetrics.registerFont(TTFont("Amiri",      _FONT_REG))
    pdfmetrics.registerFont(TTFont("Amiri-Bold", _FONT_BOLD))
    FONT      = "Amiri"
    FONT_BOLD = "Amiri-Bold"
except Exception:
    FONT      = "Helvetica"
    FONT_BOLD = "Helvetica-Bold"

# ──────────────────────────────────────────────
#  معالجة النص العربي
# ──────────────────────────────────────────────
def _ar(text) -> str:
    """إعادة تشكيل النص العربي ليظهر صحيحاً في PDF."""
    if not text:
        return ""
    try:
        import arabic_reshaper
        from bidi.algorithm import get_display
        return get_display(arabic_reshaper.reshape(str(text)))
    except Exception:
        return str(text)


def _safe_str(val) -> str:
    try:
        if pd.isna(val):
            return ""
    except Exception:
        pass
    return str(val).strip()


def _safe_num(val) -> float:
    try:
        if pd.isna(val):
            return 0.0
        return float(val)
    except Exception:
        return 0.0


def _fmt(val) -> str:
    return f"{_safe_num(val):,.2f}"


# ──────────────────────────────────────────────
#  ألوان
# ──────────────────────────────────────────────
C_DARK  = colors.HexColor("#1a2332")
C_GOLD  = colors.HexColor("#d4af37")
C_LIGHT = colors.HexColor("#f8f9fa")
C_GRID  = colors.HexColor("#cccccc")


def _base_style():
    return [
        ("BACKGROUND",     (0, 0), (-1, 0),  C_DARK),
        ("TEXTCOLOR",      (0, 0), (-1, 0),  colors.white),
        ("FONTNAME",       (0, 0), (-1, 0),  FONT_BOLD),
        ("FONTSIZE",       (0, 0), (-1, 0),  9),
        ("ALIGN",          (0, 0), (-1, 0),  "CENTER"),
        ("FONTNAME",       (0, 1), (-1, -1), FONT),
        ("FONTSIZE",       (0, 1), (-1, -1), 8),
        ("ALIGN",          (0, 1), (-1, -1), "CENTER"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, C_LIGHT]),
        ("GRID",           (0, 0), (-1, -1), 0.5, C_GRID),
        ("VALIGN",         (0, 0), (-1, -1), "MIDDLE"),
    ]


def _with_total(cmds):
    return cmds + [
        ("BACKGROUND", (0, -1), (-1, -1), C_GOLD),
        ("TEXTCOLOR",  (0, -1), (-1, -1), colors.white),
        ("FONTNAME",   (0, -1), (-1, -1), FONT_BOLD),
        ("LINEABOVE",  (0, -1), (-1, -1), 2, C_DARK),
    ]


# ──────────────────────────────────────────────
#  الدالة الرئيسية
# ──────────────────────────────────────────────
def generate_account_statement_pdf(
    customer_name,
    company_name,
    ref_number,
    statement_df,
    aging_data=None,
    checks_data=None,
):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=15*mm, leftMargin=15*mm,
        topMargin=15*mm, bottomMargin=15*mm,
    )

    title_s = ParagraphStyle("T", fontName=FONT_BOLD, fontSize=18,
                              textColor=C_DARK, alignment=TA_CENTER, spaceAfter=6)
    sub_s   = ParagraphStyle("S", fontName=FONT, fontSize=10,
                              textColor=colors.HexColor("#444"),
                              alignment=TA_RIGHT, spaceAfter=3)
    sec_s   = ParagraphStyle("H", fontName=FONT_BOLD, fontSize=13,
                              textColor=C_DARK, alignment=TA_RIGHT,
                              spaceAfter=6, spaceBefore=10)
    foot_s  = ParagraphStyle("F", fontName=FONT, fontSize=8,
                              textColor=colors.gray, alignment=TA_CENTER)

    el = []

    # ── ترويسة الشركة (شعار + اسم) ──
    LOGO_PATH = os.path.join(_BASE, "LOGO.jpeg")
    company_name_ar = "شركة بهاء الدين البستنجي وشركاه"

    logo_cell = ""
    if os.path.exists(LOGO_PATH):
        try:
            logo_cell = Image(LOGO_PATH, width=35*mm, height=20*mm, kind='proportional')
        except Exception:
            logo_cell = ""

    name_style = ParagraphStyle("CompName", fontName=FONT_BOLD, fontSize=16,
                                textColor=C_DARK, alignment=TA_RIGHT)
    sub2_s = ParagraphStyle("CompSub", fontName=FONT, fontSize=9,
                            textColor=colors.HexColor("#666"), alignment=TA_RIGHT)

    header_tbl = Table(
        [[logo_cell, Paragraph(_ar(company_name_ar), name_style)]],
        colWidths=[40*mm, A4[0] - 70*mm],
    )
    header_tbl.setStyle(TableStyle([
        ("VALIGN",  (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN",   (0, 0), (0, 0),   "LEFT"),
        ("ALIGN",   (1, 0), (1, 0),   "RIGHT"),
        ("LINEBELOW", (0, 0), (-1, 0), 1.5, C_DARK),
    ]))
    el.append(header_tbl)
    el.append(Spacer(1, 8))

    # ── بيانات الكشف ──
    el.append(Paragraph(_ar("كشف الحساب"), title_s))
    el.append(Paragraph(_ar(f"العميل : {_safe_str(customer_name)}"), sub_s))
    el.append(Paragraph(_ar(f"الشركة : {_safe_str(company_name)}"), sub_s))
    el.append(Paragraph(
        _ar(f"المرجع : {_safe_str(ref_number)}  |  تاريخ الإصدار : {datetime.now().strftime('%Y-%m-%d %H:%M')}"),
        sub_s))
    el.append(Spacer(1, 10))

    # ══════════════════════════════════════════
    #  ١. حركات الحساب
    #
    #  الترتيب البصري (يمين → يسار):
    #  [تاريخ الحركة] [الشركة] [تفاصيل الحركة] [دائن] [مدين] [رصيد]
    #
    #  في ReportLab (يسار → يمين) نرتّب الأعمدة معكوسة:
    #  col0=رصيد  col1=مدين  col2=دائن  col3=تفاصيل  col4=شركة  col5=تاريخ
    # ══════════════════════════════════════════
    if statement_df is not None and not statement_df.empty:
        el.append(Paragraph(_ar("١. حركات الحساب"), sec_s))

        # رأس الجدول — الترتيب الفعلي في الـ PDF (يسار←يمين)
        header_row = [
            _ar("رصيد"),           # col0 — أقصى اليسار
            _ar("مدين"),           # col1
            _ar("دائن"),           # col2
            _ar("تفاصيل الحركة"), # col3
            _ar("DocNum"),        # col4 — رقم الحركة
            _ar("الشركة"),         # col5
            _ar("تاريخ الحركة"),  # col6 — أقصى اليمين
        ]
        col_widths = [26*mm, 24*mm, 24*mm, 50*mm, 26*mm, 30*mm, 28*mm]

        rows = [header_row]
        total_d = total_c = 0.0

        for _, row in statement_df.iterrows():
            # ── قراءة القيم بأسمائها الحقيقية من CSV ──
            date_raw = row.get("PostingDate", "")
            try:
                date = date_raw.strftime("%Y-%m-%d") if hasattr(date_raw, "strftime") else _safe_str(date_raw)
            except Exception:
                date = _safe_str(date_raw)
            comp = _safe_str(row.get("Company", ""))
            det  = _safe_str(row.get("Details", ""))[:45]
            import re
            docnum_match = re.search(r'-?\s*(\d{6,})', str(row.get("Details", "")))
            docnum = docnum_match.group(1) if docnum_match else ""
            d    = _safe_num(row.get("DebitAmount",    0))
            c    = _safe_num(row.get("CreditAmount",   0))
            b    = _safe_num(row.get("RunningBalance", 0))
            total_d += d
            total_c += c

            # ── بناء الصف بنفس ترتيب الأعمدة ──
            # _ar() فقط على النصوص العربية، الأرقام تبقى كما هي
            rows.append([
                f"{b:,.2f}",   # col0 رصيد
                f"{d:,.2f}",   # col1 مدين
                f"{c:,.2f}",   # col2 دائن
                _ar(det),      # col3 تفاصيل
                _ar(docnum),   # col4 DocNum
                _ar(comp),     # col5 شركة
                _ar(date),     # col6 تاريخ
            ])

        # صف الإجمالي
        rows.append([
            f"{total_d - total_c:,.2f}",
            f"{total_d:,.2f}",
            f"{total_c:,.2f}",
            _ar(f"{len(statement_df)} سجل"),
            "",
            "",
            _ar("الإجمالي"),
        ])

        tbl = Table(rows, colWidths=col_widths, repeatRows=1)
        tbl.setStyle(TableStyle(_with_total(_base_style())))
        el.append(tbl)
        el.append(Spacer(1, 10))

    # ══════════════════════════════════════════
    #  ٢. أعمار الذمم
    #  الأعمدة: الرصيد الحالي + فترات الأعمار فقط
    #  الترتيب البصري (يمين←يسار):
    #  [اكثر من 90] [76-90] [61-75] [46-60] [31-45] [16-30] [0-15] [الرصيد الحالي]
    # ══════════════════════════════════════════
    if aging_data is not None and not aging_data.empty:
        el.append(PageBreak())
        el.append(Paragraph(_ar("٢. تقرير أعمار الذمم"), sec_s))

        PERIOD_COLS = [
            "0-15 يوم", "16-30 يوم", "31-45 يوم",
            "46-60 يوم", "61-75 يوم", "76-90 يوم", "اكثر من 90 يوم",
        ]
        CURRENT_COL = "الرصيد الحالي"

        avail = [c for c in PERIOD_COLS if c in aging_data.columns]
        has_current = CURRENT_COL in aging_data.columns

        # الترتيب المنطقي: فترات أولاً ثم الرصيد الحالي
        logical_cols = avail + ([CURRENT_COL] if has_current else [])
        if not logical_cols:
            logical_cols = [c for c in aging_data.columns
                            if pd.api.types.is_numeric_dtype(aging_data[c])][:6]

        # عكس الترتيب للعرض RTL في PDF
        display_cols = list(reversed(logical_cols))
        PAGE_W = A4[0] - 30*mm
        cw_ag  = PAGE_W / len(display_cols)

        hdr_ag = [_ar(c) for c in display_cols]
        ag_rows = [hdr_ag]
        for _, row in aging_data.iterrows():
            ag_rows.append([_fmt(row.get(c, 0)) for c in display_cols])

        atbl = Table(ag_rows, colWidths=[cw_ag]*len(display_cols), repeatRows=1)
        atbl.setStyle(TableStyle(_base_style()))
        el.append(atbl)
        el.append(Spacer(1, 10))

    # ══════════════════════════════════════════
    #  ٣. الشيكات المعلقة
    #  الأعمدة (يمين←يسار):
    #  [تاريخ الاستحقاق] [قيمة الشيك] [رقم الشيك]
    # ══════════════════════════════════════════
    if checks_data is not None and not checks_data.empty:
        el.append(PageBreak())
        el.append(Paragraph(_ar("٣. الشيكات المعلقة"), sec_s))

        # الترتيب البصري RTL: تاريخ (يمين) | قيمة | رقم (يسار)
        # في ReportLab: col0=رقم الشيك  col1=قيمة الشيك  col2=تاريخ الاستحقاق
        header_ch = [
            _ar("رقم الشيك"),
            _ar("قيمة الشيك"),
            _ar("تاريخ الاستحقاق"),
        ]
        cw_ch = [90*mm, 50*mm, 50*mm]

        ch_rows = [header_ch]
        for _, row in checks_data.iterrows():
            chk_no  = _safe_str(row.get("رقم الشيك",      ""))
            chk_val = _fmt(row.get("قيمة الشيك",          0))
            due     = _safe_str(row.get("تاريخ الاستحقاق", ""))

            ch_rows.append([
                _ar(chk_no),  # col0
                chk_val,      # col1
                _ar(due),     # col2
            ])

        ctbl = Table(ch_rows, colWidths=cw_ch, repeatRows=1)
        ctbl.setStyle(TableStyle(_base_style()))
        el.append(ctbl)

    # ── تذييل ──
    el.append(Spacer(1, 15))
    el.append(Paragraph(
        _ar(f"تم الإنشاء بواسطة SAP Analytics  |  {datetime.now().strftime('%Y-%m-%d %H:%M')}"),
        foot_s))

    doc.build(el)
    buffer.seek(0)
    return buffer
