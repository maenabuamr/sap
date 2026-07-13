from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_RIGHT, TA_CENTER, TA_LEFT
import io
from datetime import datetime
import pandas as pd


def _safe_str(val):
    """Convert to safe string for PDF"""
    if pd.isna(val):
        return ""
    return str(val).strip()


def _safe_num(val, default=0.0):
    """Convert to safe number"""
    try:
        if pd.isna(val):
            return default
        return float(val)
    except:
        return default


def _format_date(date_val):
    """Convert Excel serial date to readable format"""
    try:
        if pd.isna(date_val):
            return ""
        n = float(date_val)
        if 30000 < n < 60000:
            dt = pd.Timestamp('1899-12-30') + pd.Timedelta(days=n)
            return dt.strftime('%Y-%m-%d')
    except:
        pass
    return _safe_str(date_val)


def generate_account_statement_pdf(customer_name, company_name, ref_number, statement_df, aging_data=None, checks_data=None):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=15*mm, leftMargin=15*mm, topMargin=15*mm, bottomMargin=15*mm)
    elements = []
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('Title', parent=styles['Title'], fontSize=16, textColor=colors.HexColor('#1a2332'), alignment=TA_CENTER, spaceAfter=8)
    sub_style = ParagraphStyle('Sub', parent=styles['Normal'], fontSize=10, textColor=colors.HexColor('#444'), alignment=TA_CENTER, spaceAfter=3)
    section_style = ParagraphStyle('Section', parent=styles['Heading2'], fontSize=13, textColor=colors.HexColor('#1a2332'), alignment=TA_LEFT, spaceAfter=8, spaceBefore=10, fontName='Helvetica-Bold')

    # ====== HEADER ======
    elements.append(Paragraph("ACCOUNT STATEMENT", title_style))
    elements.append(Paragraph(f"<b>Customer:</b> {_safe_str(customer_name)}", sub_style))
    elements.append(Paragraph(f"<b>Company:</b> {_safe_str(company_name)}", sub_style))
    elements.append(Paragraph(f"<b>Reference:</b> {_safe_str(ref_number)}  |  <b>Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}", sub_style))
    elements.append(Spacer(1, 10))

    # ====== 1. STATEMENT TABLE ======
    if statement_df is not None and not statement_df.empty:
        elements.append(Paragraph("1. Account Transactions", section_style))
        col_headers = ["Balance", "Credit", "Debit", "Posting Date", "Reference", "Description"]
        data_rows = [col_headers]
        for _, row in statement_df.iterrows():
            data_rows.append([
                f"{_safe_num(row.get('RunningBalance', 0)):,.2f}",
                f"{_safe_num(row.get('CreditAmount', 0)):,.2f}",
                f"{_safe_num(row.get('DebitAmount', 0)):,.2f}",
                _format_date(row.get('PostingDate', '')),
                _safe_str(row.get('ReferenceNumber', '')),
                _safe_str(row.get('Description', ''))[:50]
            ])
        if 'DebitAmount' in statement_df.columns:
            td = statement_df['DebitAmount'].sum()
            tc = statement_df['CreditAmount'].sum()
            data_rows.append([f"{_safe_num(td-tc):,.2f}", f"{_safe_num(tc):,.2f}", f"{_safe_num(td):,.2f}", "TOTAL", f"{len(statement_df)} rows", ""])

        tbl = Table(data_rows, colWidths=[25*mm, 22*mm, 22*mm, 25*mm, 22*mm, 64*mm], repeatRows=1)
        tbl.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a2332')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ALIGN', (0, 1), (4, -1), 'CENTER'),
            ('ALIGN', (5, 1), (5, -1), 'LEFT'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#f8f9fa')]),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#d4af37')),
            ('TEXTCOLOR', (0, -1), (-1, -1), colors.white),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('LINEABOVE', (0, -1), (-1, -1), 2, colors.HexColor('#1a2332')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(tbl)
        elements.append(Spacer(1, 10))

    # ====== 2. AGING REPORT ======
    if aging_data is not None and not aging_data.empty:
        elements.append(PageBreak())
        elements.append(Paragraph("2. Aging Report", section_style))

        # Auto-detect columns
        possible_date_cols = [c for c in aging_data.columns if any(k in c.lower() for k in ['current', '0', 'days_0'])]
        possible_aging_cols = {
            '1-30': [c for c in aging_data.columns if '1_30' in c or '1-30' in c or 'days1' in c.lower()],
            '31-60': [c for c in aging_data.columns if '31_60' in c or '31-60' in c],
            '61-90': [c for c in aging_data.columns if '61_90' in c or '61-90' in c],
            '91-120': [c for c in aging_data.columns if '91_120' in c or '91-120' in c],
            '120+': [c for c in aging_data.columns if '120' in c and '91' not in c],
            'Current': [c for c in aging_data.columns if 'current' in c.lower() or c.lower() in ['0', 'not_due']],
            'Total': [c for c in aging_data.columns if 'total' in c.lower() or 'sum' in c.lower() or 'رصيد' in c],
        }

        # Show ALL columns from aging data, dynamic
        display_cols = list(aging_data.columns)[:8]  # Max 8 columns
        data_rows = [display_cols]
        for _, row in aging_data.iterrows():
            data_rows.append([_safe_str(row.get(c, ''))[:30] for c in display_cols])

        # Calculate equal width
        avail_width = 180
        col_w = avail_width / len(display_cols)
        atbl = Table(data_rows, colWidths=[col_w*mm]*len(display_cols), repeatRows=1)
        atbl.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2d3e55')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(atbl)

    # ====== 3. CHECKS ======
    if checks_data is not None and not checks_data.empty:
        elements.append(PageBreak())
        elements.append(Paragraph("3. Pending Checks", section_style))

        display_cols = list(checks_data.columns)[:6]  # Max 6 columns
        data_rows = [display_cols]
        for _, row in checks_data.iterrows():
            data_rows.append([_safe_str(row.get(c, ''))[:30] for c in display_cols])

        avail_width = 180
        col_w = avail_width / len(display_cols)
        ctbl = Table(data_rows, colWidths=[col_w*mm]*len(display_cols), repeatRows=1)
        ctbl.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2d3e55')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(ctbl)

    elements.append(Spacer(1, 15))
    elements.append(Paragraph(f"Generated by SAP Analytics | {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles['Italic']))
    doc.build(elements)
    buffer.seek(0)
    return buffer
