import io
import os
import calendar
from datetime import datetime
from django.conf import settings
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, HRFlowable
)

def get_decore_logo_path():
    path = os.path.join(settings.BASE_DIR, 'static', 'images', 'logo.png')
    if os.path.exists(path):
        return path
    return None

def generate_pdf_report(title, subtitle, summary_cards, table_headers, table_data, col_widths=None):
    buffer = io.BytesIO()
    
    # Page setup - A4 with 0.4 inch margins for crisp, clean layout
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=28,
        leftMargin=28,
        topMargin=28,
        bottomMargin=28
    )
    story = []
    styles = getSampleStyleSheet()
    
    # Typography Styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=16,
        leading=20,
        textColor=colors.HexColor('#1e3a8a'),
        fontName='Helvetica-Bold',
        spaceAfter=2
    )
    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#64748b'),
        fontName='Helvetica'
    )
    header_title_style = ParagraphStyle(
        'HeaderCompany',
        parent=styles['Heading2'],
        fontSize=13,
        leading=16,
        textColor=colors.HexColor('#0f172a'),
        fontName='Helvetica-Bold'
    )

    # 1. Header Table with Decore Logo
    logo_path = get_decore_logo_path()
    now_str = datetime.now().strftime("%d %b %Y, %I:%M %p")
    
    right_meta = Paragraph(
        f"<font size='8' color='#64748b'><b>Report Date:</b> {now_str}<br/><b>System Status:</b> Live Database</font>",
        ParagraphStyle('MetaRight', parent=styles['Normal'], alignment=2)
    )

    if logo_path:
        logo_img = Image(logo_path, width=1.4*inch, height=0.45*inch)
        header_table = Table(
            [[logo_img, Paragraph("<b>DECORE CONSTRUCTION</b><br/><font color='#64748b' size='8'>Web Management & Enterprise Ledger Suite</font>", header_title_style), right_meta]],
            colWidths=[1.5*inch, 3.8*inch, 2.2*inch]
        )
    else:
        header_table = Table(
            [[Paragraph("<b>DECORE CONSTRUCTION</b><br/><font color='#64748b' size='8'>Web Management & Enterprise Ledger Suite</font>", header_title_style), right_meta]],
            colWidths=[5.3*inch, 2.2*inch]
        )
        
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(header_table)
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#2563eb'), spaceAfter=10, spaceBefore=4))
    
    # 2. Document Title
    story.append(Paragraph(title, title_style))
    story.append(Paragraph(subtitle, subtitle_style))
    story.append(Spacer(1, 10))
    
    # 3. Summary Cards Bar (KPIs)
    if summary_cards:
        cards_row = []
        for label, val in summary_cards:
            p_text = f"<font size='7.5' color='#475569'><b>{label.upper()}</b></font><br/><font size='11' color='#1e3a8a'><b>{val}</b></font>"
            cards_row.append(Paragraph(p_text, styles['Normal']))
            
        num_cards = len(summary_cards)
        card_col_width = (7.5 * inch) / num_cards
        
        summary_table = Table([cards_row], colWidths=[card_col_width] * num_cards)
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8fafc')),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#cbd5e1')),
            ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
            ('TOPPADDING', (0,0), (-1,-1), 6),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
            ('LEFTPADDING', (0,0), (-1,-1), 6),
            ('RIGHTPADDING', (0,0), (-1,-1), 6),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 12))
        
    # 4. Table Headers and Rows
    formatted_table_data = []
    
    # Header row formatting
    header_row_p = [Paragraph(f"<b><font color='#ffffff' size='8.5'>{h}</font></b>", styles['Normal']) for h in table_headers]
    formatted_table_data.append(header_row_p)
    
    # Body rows formatting
    cell_style = ParagraphStyle('Cell', parent=styles['Normal'], fontSize=8, leading=10.5, textColor=colors.HexColor('#1e293b'))
    for row_data in table_data:
        p_row = [Paragraph(str(cell), cell_style) for cell in row_data]
        formatted_table_data.append(p_row)
        
    num_cols = len(table_headers)
    if not col_widths:
        w = (7.5 * inch) / num_cols
        col_widths = [w] * num_cols
    else:
        col_widths = [w * inch for w in col_widths]
        
    main_table = Table(formatted_table_data, colWidths=col_widths, repeatRows=1)
    
    t_style = [
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1e3a8a')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
    ]
    
    for i in range(1, len(formatted_table_data)):
        if i % 2 == 0:
            t_style.append(('BACKGROUND', (0, i), (-1, i), colors.HexColor('#f8fafc')))
            
    main_table.setStyle(TableStyle(t_style))
    story.append(main_table)
    
    # 5. Footer Signature
    story.append(Spacer(1, 14))
    footer_text = f"<font size='7' color='#94a3b8'>Decore Construction Management Platform &bull; System Generated Operational PDF Document &bull; Confidential</font>"
    story.append(Paragraph(footer_text, ParagraphStyle('Footer', parent=styles['Normal'], alignment=1)))

    doc.build(story)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf


def generate_monthly_attendance_pdf(year, month, worksite_id=None):
    from employees.models import Employee
    from attendance.models import Attendance
    from worksites.models import Worksite

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=18,
        leftMargin=18,
        topMargin=20,
        bottomMargin=20
    )
    story = []
    styles = getSampleStyleSheet()

    num_days = calendar.monthrange(year, month)[1]
    month_name = calendar.month_name[month]

    title_text = f"Monthly Attendance Roster — {month_name} {year}"
    site_name = "All Worksites"
    if worksite_id and str(worksite_id).isdigit():
        site = Worksite.objects.filter(pk=int(worksite_id)).first()
        if site:
            site_name = site.name

    # Header
    logo_path = get_decore_logo_path()
    header_title_style = ParagraphStyle(
        'HeaderCompany',
        parent=styles['Heading2'],
        fontSize=12,
        leading=14,
        textColor=colors.HexColor('#0f172a'),
        fontName='Helvetica-Bold'
    )
    right_meta = Paragraph(
        f"<font size='7.5' color='#64748b'><b>Worksite:</b> {site_name}<br/><b>Generated:</b> {datetime.now().strftime('%d %b %Y')}</font>",
        ParagraphStyle('MetaRight', parent=styles['Normal'], alignment=2)
    )

    if logo_path:
        logo_img = Image(logo_path, width=1.2*inch, height=0.4*inch)
        header_table = Table(
            [[logo_img, Paragraph(f"<b>DECORE CONSTRUCTION</b> — {title_text}", header_title_style), right_meta]],
            colWidths=[1.3*inch, 7.5*inch, 2.4*inch]
        )
    else:
        header_table = Table(
            [[Paragraph(f"<b>DECORE CONSTRUCTION</b> — {title_text}", header_title_style), right_meta]],
            colWidths=[8.8*inch, 2.4*inch]
        )

    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
    ]))
    story.append(header_table)
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#2563eb'), spaceAfter=8, spaceBefore=4))

    # Build Attendance Matrix
    employees = Employee.objects.select_related("worksite").order_by("first_name", "last_name")
    if worksite_id and str(worksite_id).isdigit():
        employees = employees.filter(worksite_id=int(worksite_id))

    headers = ["Worker Name", "Role"] + [str(d) for d in range(1, num_days + 1)] + ["P", "L", "A", "OT"]
    formatted_table_data = []

    # Table Header Row
    hdr_p = [Paragraph(f"<b><font color='#ffffff' size='7'>{h}</font></b>", styles['Normal']) for h in headers]
    formatted_table_data.append(hdr_p)

    cell_style = ParagraphStyle('Cell', parent=styles['Normal'], fontSize=6.5, leading=8, textColor=colors.HexColor('#0f172a'))
    center_cell = ParagraphStyle('CellC', parent=styles['Normal'], fontSize=6, leading=7.5, alignment=1)

    for emp in employees:
        att_map = {}
        records = Attendance.objects.filter(employee=emp, date__year=year, date__month=month)
        for r in records:
            att_map[r.date.day] = r.status

        row = [
            Paragraph(f"<b>{emp.full_name}</b>", cell_style),
            Paragraph(emp.get_role_display(), cell_style)
        ]

        p_cnt, l_cnt, a_cnt, ot_cnt = 0, 0, 0, 0
        for day in range(1, num_days + 1):
            st = att_map.get(day, "")
            if st in ["present", "Present"]:
                p_cnt += 1
                code = "<font color='#16a34a'><b>P</b></font>"
            elif st in ["late", "Late"]:
                l_cnt += 1
                code = "<font color='#d97706'><b>L</b></font>"
            elif st in ["absent", "Absent"]:
                a_cnt += 1
                code = "<font color='#dc2626'><b>A</b></font>"
            elif st in ["overtime", "Overtime"]:
                ot_cnt += 1
                code = "<font color='#2563eb'><b>OT</b></font>"
            else:
                code = "<font color='#94a3b8'>-</font>"
            row.append(Paragraph(code, center_cell))

        row.extend([
            Paragraph(f"<b>{p_cnt}</b>", center_cell),
            Paragraph(f"<b>{l_cnt}</b>", center_cell),
            Paragraph(f"<b>{a_cnt}</b>", center_cell),
            Paragraph(f"<b>{ot_cnt}</b>", center_cell),
        ])
        formatted_table_data.append(row)

    col_w = [1.3*inch, 0.9*inch] + [0.24*inch]*num_days + [0.3*inch, 0.3*inch, 0.3*inch, 0.35*inch]
    main_table = Table(formatted_table_data, colWidths=col_w, repeatRows=1)

    t_style = [
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1e3a8a')),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 2),
        ('RIGHTPADDING', (0,0), (-1,-1), 2),
        ('GRID', (0,0), (-1,-1), 0.4, colors.HexColor('#cbd5e1')),
    ]
    for i in range(1, len(formatted_table_data)):
        if i % 2 == 0:
            t_style.append(('BACKGROUND', (0, i), (-1, i), colors.HexColor('#f8fafc')))

    main_table.setStyle(TableStyle(t_style))
    story.append(main_table)

    story.append(Spacer(1, 10))
    footer_text = f"<font size='6.5' color='#94a3b8'>Decore Construction Platform &bull; P: Present &bull; L: Late (0.5 Day) &bull; A: Absent &bull; OT: Overtime (1.5 Day) &bull; Confidential Official Roster</font>"
    story.append(Paragraph(footer_text, ParagraphStyle('Footer', parent=styles['Normal'], alignment=1)))

    doc.build(story)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf
