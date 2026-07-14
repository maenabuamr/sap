import io
import os
import pandas as pd
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle)

# ──────────────────────────────────────────────
#  تسجيل الخطوط
# ──────────────────────────────────────────────
_BASE      = os.path.dirname(os.path.abspath(__file__))
_FONT_REG  = os.path.join(_BASE, "fonts", "Amiri-Regular.ttf")
_FONT_BOLD = os.path.join(_BASE, "fonts", "Amiri-Bold.ttf")

try:
    pdfmetrics.registerFont(TTFont("Amiri",       _FONT_REG))
    pdfmetrics.registerFont(TTFont("Amiri-Bold", _FONT_BOLD))
    FONT       = "Amiri"
    FONT_BOLD = "Amiri-Bold"
except Exception:
    FONT       = "Helvetica"
    FONT_BOLD = "Helvetica-Bold"

# ──────────────────────────────────────────────
#  دوال المساعدة
# ──────────────────────────────────────────────
def _ar(text) -> str:
    if not text: return ""
    try:
        import arabic_reshaper
        from bidi.algorithm import get_display
        return get_display(arabic_reshaper.reshape(str(text)))
    except Exception: return str(text)

def _safe_str(val) -> str:
    return str(val).strip() if not pd.isna(val) else ""

def _safe_num(val) -> float:
    try: return float(val) if not pd.isna(val) else 0.0
    except: return 0.0

def _fmt(val) -> str: return f"{_safe_num(val):,.2f}"

# ──────────────────────────────────────────────
#  التنسيقات
# ──────────────────────────────────────────────
C_DARK  = colors.HexColor("#1a2332")
C_GOLD  = colors.HexColor("#d4af37")
C_LIGHT = colors.HexColor("#f8f9fa")
C_GRID  = colors.HexColor("#cccccc")

def _base_style():
    return [
        ("BACKGROUND", (0, 0), (-1, 0), C_DARK),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), FONT_BOLD),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("FONTNAME", (0, 1), (-1, -1), FONT),
        ("FONTSIZE", (0, 1), (-1, -1), 8),
        ("ALIGN", (0, 1), (-1, -1), "CENTER"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, C_LIGHT]),
        ("GRID", (0, 0), (-1, -1), 0.5, C_GRID),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]

def _with_total(cmds):
    return cmds + [
        ("BACKGROUND", (0, -1), (-1, -1), C_GOLD),
        ("TEXTCOLOR", (0, -1), (-1, -1), colors.white),
        ("FONTNAME", (0, -1), (-1, -1), FONT_BOLD),
        ("LINEABOVE", (0, -1), (-1, -1), 2, C_DARK),
    ]

# ──────────────────────────────────────────────
#  الدالة الرئيسية
# ──────────────────────────────────────────────
def generate_account_statement_pdf(customer_name, company_name, ref_number, statement_df, aging_data=None, checks_data=None):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=15*mm, leftMargin=15*mm, topMargin=15*mm, bottomMargin=15*mm)
    
    # التنسيقات
    title_s = ParagraphStyle("T", fontName=FONT_BOLD, fontSize=18, textColor=C_DARK, alignment=TA_CENTER, spaceAfter=6)
    sub_s   = ParagraphStyle("S", fontName=FONT, fontSize=10, textColor=colors.HexColor("#444"), alignment=TA_RIGHT, spaceAfter=3)
    sec_s   = ParagraphStyle("H", fontName=FONT_BOLD, fontSize=13, textColor=C_DARK, alignment=TA_RIGHT, spaceAfter=6, spaceBefore=10)
    foot_s  = ParagraphStyle("F", fontName=FONT, fontSize=8, textColor=colors.gray, alignment=TA_CENTER)
    
    # تنسيقات الترويسة الجديدة
    name_style = ParagraphStyle("CompName", fontName=FONT_BOLD, fontSize=16, textColor=C_DARK, alignment=TA_RIGHT)

    el = []
    
    # ── الترويسة ──
    LOGO_PATH = os.path.join(_BASE, "LOGO.jpeg")
    logo_cell = ""
    if os.path.exists(LOGO_PATH):
        try: logo_cell = Image(LOGO_PATH, width=35*mm, height=20*mm, kind='proportional')
        except: logo_cell = ""
    
    header_tbl = Table([[logo_cell, Paragraph(_ar("شركة بهاء الدين البستنجي وشركاه"), name_style)]], colWidths=[40*mm, A4[0] - 70*mm])
    header_tbl.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("ALIGN", (0, 0), (0, 0), "LEFT"), ("ALIGN", (1, 0), (1, 0), "RIGHT"), ("LINEBELOW", (0, 0), (-1, 0), 1.5, C_DARK)]))
    el.append(header_tbl)
    el.append(Spacer(1, 15))

    # ── البيانات الأساسية ──
    el.append(Paragraph(_ar("كشف الحساب"), title_s))
    el.append(Paragraph(_ar(f"العميل : {_safe_str(customer_name)}"), sub_s))
    el.append(Paragraph(_ar(f"الشركة : {_safe_str(company_name)}"), sub_s))
    el.append(Paragraph(_ar(f"المرجع : {_safe_str(ref_number)} | تاريخ الإصدار : {datetime.now().strftime('%Y-%m-%d')}"), sub_s))
    el.append(Spacer(1, 10))

    # ── ١. حركات الحساب ──
    if statement_df is not None and not statement_df.empty:
        el.append(Paragraph(_ar("١. حركات الحساب"), sec_s))
        header_row = [_ar("تاريخ"), _ar("الشركة"), _ar("رقم الحركة"), _ar("تفاصيل الحركة"), _ar("دائن"), _ar("مدين"), _ar("رصيد")]
        col_widths = [20*mm, 25*mm, 25*mm, 45*mm, 25*mm, 25*mm, 25*mm]
        rows = [header_row]
        total_d = total_c = 0.0
        for _, row in statement_df.iterrows():
            d = _safe_num(row.get("DebitAmount", 0))
            c = _safe_num(row.get("CreditAmount", 0))
            b = _safe_num(row.get("RunningBalance", 0))
            total_d += d; total_c += c
            clean_date = pd.to_datetime(row.get("PostingDate")).strftime('%Y-%m-%d') if not pd.isna(row.get("PostingDate")) else ""
            rows.append([_ar(clean_date), _ar(_safe_str(row.get("Company", ""))), _ar(_safe_str(row.get("DocNum", ""))), _ar(_safe_str(row.get("Details", ""))), _fmt(c), _fmt(d), _fmt(b)])
        rows.append([ "", "", "", _ar("الإجمالي"), _fmt(total_c), _fmt(total_d), _fmt(total_d - total_c)])
        tbl = Table(rows, colWidths=col_widths, repeatRows=1)
        tbl.setStyle(TableStyle(_with_total(_base_style())))
        el.append(tbl)
        el.append(Spacer(1, 15))

    # ── ٢. أعمار الذمم ──
    if aging_data is not None and not aging_data.empty:
        el.append(Paragraph(_ar("٢. تقرير أعمار الذمم"), sec_s))
        PERIOD_COLS = ["0-15 يوم", "16-30 يوم", "31-45 يوم", "46-60 يوم", "61-75 يوم", "76-90 يوم", "اكثر من 90 يوم"]
        display_cols = ["الرصيد الحالي"] + [c for c in PERIOD_COLS if c in aging_data.columns]
        hdr_ag = [_ar(c) for c in display_cols]
        ag_rows = [hdr_ag]
        for _, row in aging_data.iterrows():
            ag_rows.append([_fmt(row.get(c, 0)) for c in display_cols])
        atbl = Table(ag_rows, repeatRows=1)
        atbl.setStyle(TableStyle(_base_style()))
        el.append(atbl)
        el.append(Spacer(1, 15))

    # ── ٣. الشيكات المعلقة ──
    if checks_data is not None and not checks_data.empty:
        el.append(Paragraph(_ar("٣. الشيكات المعلقة"), sec_s))
        header_ch = [_ar("تاريخ الاستحقاق"), _ar("قيمة الشيك"), _ar("رقم الشيك")]
        ch_rows = [header_ch]
        for _, row in checks_data.iterrows():
            ch_rows.append([_ar(_safe_str(row.get("تاريخ الاستحقاق", ""))), _fmt(row.get("قيمة الشيك", 0)), _ar(_safe_str(row.get("رقم الشيك", "")))])
        ctbl = Table(ch_rows, colWidths=[50*mm, 50*mm, 90*mm], repeatRows=1)
        ctbl.setStyle(TableStyle(_base_style()))
        el.append(ctbl)

    # ── تذييل ──
    el.append(Spacer(1, 20))
    el.append(Paragraph(_ar(f"تم الإنشاء بواسطة SAP Analytics | {datetime.now().strftime('%Y-%m-%d %H:%M')}"), foot_s))
    
    doc.build(el)
    buffer.seek(0)
    return buffer