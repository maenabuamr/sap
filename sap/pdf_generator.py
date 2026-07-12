from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.enums import TA_RIGHT, TA_CENTER, TA_LEFT
import io
from datetime import datetime


def generate_account_statement_pdf(customer_name, company_name, ref_number, statement_df, aging_data=None, checks_data=None):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=15*mm, leftMargin=15*mm, topMargin=15*mm, bottomMargin=15*mm)
    elements = []
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('Title', parent=styles['Title'], fontSize=16, textColor=colors.HexColor('#1a2332'), alignment=TA_CENTER, spaceAfter=10)
    sub_style = ParagraphStyle('Sub', parent=styles['Normal'], fontSize=10, textColor=colors.HexColor('#444'), alignment=TA_CENTER, spaceAfter=4)
    section_style = ParagraphStyle('Section', parent=styles['Heading2'], fontSize=13, textColor=colors.HexColor('#1a2332'), alignment=TA_LEFT, spaceAfter=8, spaceBefore=10)

    # ====== HEADER ======
    elements.append(Paragraph("ACCOUNT STATEMENT", title_style))
    elements.append(Paragraph(f"<b>Customer:</b> {customer_name}", sub_style))
    elements.append(Paragraph(f"<b>Company:</b> {company_name}", sub_style))
    elements.append(Paragraph(f"<b>Reference:</b> {ref_number}  |  <b>Date:</b> {datetime.now().strftime('%Y-%m-%d')}", sub_style))
    elements.append(Spacer(1, 10))

    # ====== STATEMENT TABLE ======
    if not statement_df.empty:
        elements.append(Paragraph("1. Account Transactions", section_style))
        col_headers = ["Balance", "Credit", "Debit", "Posting Date", "Reference", "Description"]
        data_rows = [col_headers]
        for _, row in statement_df.iterrows():
            data_rows.append([
                f"{row.get('RunningBalance', 0):,.2f}",
                f"{row.get('CreditAmount', 0):,.2f}",
                f"{row.get('DebitAmount', 0):,.2f}",
                str(row.get('PostingDate', '')),
                str(row.get('ReferenceNumber', '')),
                str(row.get('Description', ''))[:50]
            ])
        if 'DebitAmount' in statement_df.columns:
            td = statement_df['DebitAmount'].sum()
            tc = statement_df['CreditAmount'].sum()
            data_rows.append([f"{td-tc:,.2f}", f"{tc:,.2f}", f"{td:,.2f}", "TOTAL", "", ""])

        tbl = Table(data_rows, colWidths=[25*mm, 22*mm, 22*mm, 25*mm, 22*mm, 64*mm], repeatRows=1)
        tbl.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a2332')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ALIGN', (0, 1), (-1, 1), 'CENTER'),
            ('ALIGN', (0, 2), (4, -2), 'CENTER'),
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

    # ====== AGING REPORT ======
    if aging_data is not None and not aging_data.empty:
        elements.append(Paragraph("2. Aging Report", section_style))
        aging_rows = [["Current", "1-30 Days", "31-60 Days", "61-90 Days", "91-120 Days", "120+ Days", "Total"]]
        for _, row in aging_data.iterrows():
            aging_rows.append([
                f"{row.get('Current', 0):,.2f}",
                f"{row.get('Days_1_30', 0):,.2f}",
                f"{row.get('Days_31_60', 0):,.2f}",
                f"{row.get('Days_61_90', 0):,.2f}",
                f"{row.get('Days_91_120', 0):,.2f}",
                f"{row.get('Days_120_Plus', 0):,.2f}",
                f"{row.get('Total', 0):,.2f}"
            ])
        atbl = Table(aging_rows, colWidths=[27*mm]*7, repeatRows=1)
        atbl.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2d3e55')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
        ]))
        elements.append(atbl)

    # ====== CHECKS ======
    if checks_data is not None and not checks_data.empty:
        elements.append(Paragraph("3. Pending Checks", section_style))
        check_rows = [["Check #", "Amount", "Due Date", "Status"]]
        for _, row in checks_data.iterrows():
            check_rows.append([
                str(row.get('CheckNumber', '')),
                f"{row.get('Amount', 0):,.2f}",
                str(row.get('DueDate', '')),
                str(row.get('Status', ''))
            ])
        ctbl = Table(check_rows, colWidths=[40*mm, 40*mm, 50*mm, 50*mm], repeatRows=1)
        ctbl.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2d3e55')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
        ]))
        elements.append(ctbl)

    elements.append(Spacer(1, 20))
    elements.append(Paragraph(f"Generated by SAP Analytics | {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles['Italic']))
    doc.build(elements)
    buffer.seek(0)
    return buffer
