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
    footer_text = f"<font size='7' color='#94a3b8'>Decore Builders Construction Platform &bull; System Generated Operational PDF Document &bull; Confidential</font>"
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
    employees = Employee.objects.select_related("worksite").order_by("name")
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
            Paragraph(f"<b>{emp.name}</b>", cell_style),
            Paragraph(emp.role, cell_style)
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
    footer_text = f"<font size='6.5' color='#94a3b8'>Decore Builders Platform &bull; P: Present &bull; L: Late (0.5 Day) &bull; A: Absent &bull; OT: Overtime (Daily wage + Extra hours * hourly rate) &bull; Confidential Official Roster</font>"
    story.append(Paragraph(footer_text, ParagraphStyle('Footer', parent=styles['Normal'], alignment=1)))

    doc.build(story)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf


def generate_salary_receipt_pdf(data):
    """Generate a branded PDF Salary Receipt Voucher for an employee payment."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    story = []
    styles = getSampleStyleSheet()

    # Colors
    primary_color = colors.HexColor('#1e3a8a')
    success_color = colors.HexColor('#16a34a')
    muted_color = colors.HexColor('#64748b')

    # Typography
    header_title_style = ParagraphStyle(
        'HeaderTitle',
        parent=styles['Heading1'],
        fontSize=15,
        leading=18,
        textColor=primary_color,
        fontName='Helvetica-Bold'
    )
    sub_head_style = ParagraphStyle(
        'SubHead',
        parent=styles['Normal'],
        fontSize=9,
        leading=12,
        textColor=muted_color
    )

    logo_path = get_decore_logo_path()
    voucher_no = f"VCHR-{datetime.now().strftime('%Y%m%d')}-{data.get('employee_id', '00')}"
    today_str = datetime.now().strftime("%d %b %Y, %I:%M %p")

    right_meta = Paragraph(
        f"<font size='8' color='#64748b'><b>Voucher No:</b> {voucher_no}<br/><b>Issue Date:</b> {today_str}<br/><b>Status:</b> PAID &amp; VERIFIED</font>",
        ParagraphStyle('MetaRight', parent=styles['Normal'], alignment=2)
    )

    if logo_path:
        logo_img = Image(logo_path, width=1.5*inch, height=0.5*inch)
        header_table = Table(
            [[logo_img, Paragraph("<b>DECORE CONSTRUCTION MANAGEMENT</b><br/><font color='#64748b' size='8.5'>Official Weekly Salary Disbursement Voucher</font>", header_title_style), right_meta]],
            colWidths=[1.6*inch, 3.7*inch, 2.2*inch]
        )
    else:
        header_table = Table(
            [[Paragraph("<b>DECORE CONSTRUCTION MANAGEMENT</b><br/><font color='#64748b' size='8.5'>Official Weekly Salary Disbursement Voucher</font>", header_title_style), right_meta]],
            colWidths=[5.3*inch, 2.2*inch]
        )

    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(header_table)
    story.append(HRFlowable(width="100%", thickness=2, color=primary_color, spaceAfter=14, spaceBefore=4))

    # Employee Details Card Box
    emp_details_text = f"""
    <b>EMPLOYEE INFORMATION &amp; PAY PERIOD</b><br/>
    <b>Worker Name:</b> {data.get('employee_name', 'Employee')}<br/>
    <b>Role / Occupation:</b> {data.get('employee_role', 'Worker')}<br/>
    <b>Phone Number:</b> {data.get('phone', 'N/A')}<br/>
    <b>Assigned Worksite:</b> {data.get('worksite_name', 'General Worksites')}<br/>
    <b>Pay Period (Saturday):</b> {data.get('period_str', 'Weekly Payroll')}
    """
    
    pay_details_text = f"""
    <b>PAYMENT DISBURSEMENT METHOD</b><br/>
    <b>Payment Method:</b> {data.get('payment_method', 'Bank Transfer')}<br/>
    <b>Reference / Transaction ID:</b> {data.get('reference_number', 'N/A')}<br/>
    <b>Disbursement Status:</b> <font color='#16a34a'><b>COMPLETED</b></font><br/>
    <b>Payment Date:</b> {data.get('paid_date', today_str)}
    """

    info_table = Table(
        [[
            Paragraph(emp_details_text, ParagraphStyle('InfoL', parent=styles['Normal'], fontSize=8.5, leading=12.5)),
            Paragraph(pay_details_text, ParagraphStyle('InfoR', parent=styles['Normal'], fontSize=8.5, leading=12.5))
        ]],
        colWidths=[3.75*inch, 3.75*inch]
    )
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8fafc')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#cbd5e1')),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 14))

    # Financial Breakdown Table
    table_headers = ["Earnings &amp; Deductions Item", "Calculation Unit", "Rate (Rs.)", "Subtotal (Rs.)"]
    hdr_p = [Paragraph(f"<b><font color='#ffffff' size='8.5'>{h}</font></b>", styles['Normal']) for h in table_headers]

    cell_s = ParagraphStyle('Cell', parent=styles['Normal'], fontSize=8.5, leading=11)
    cell_r = ParagraphStyle('CellR', parent=styles['Normal'], fontSize=8.5, leading=11, alignment=2)

    pres_days = data.get('present_days', 0)
    d_wage = data.get('daily_wage', 0)
    gross_wage = pres_days * d_wage
    bonus = data.get('bonus', 0)
    deductions = data.get('deductions', 0)
    net_sal = data.get('net_salary', gross_wage + bonus - deductions)
    paid_amt = data.get('paid_amount', net_sal)

    table_rows = [
        hdr_p,
        [
            Paragraph("Basic Days Worked Wage", cell_s),
            Paragraph(f"{pres_days} Days", cell_s),
            Paragraph(f"Rs. {d_wage:,.2f}", cell_r),
            Paragraph(f"Rs. {gross_wage:,.2f}", cell_r)
        ],
        [
            Paragraph("Weekly Overtime / Performance Bonus", cell_s),
            Paragraph("Additional", cell_s),
            Paragraph("—", cell_r),
            Paragraph(f"+Rs. {bonus:,.2f}", cell_r)
        ],
        [
            Paragraph("Salary Advances / Deductions", cell_s),
            Paragraph("Deductions", cell_s),
            Paragraph("—", cell_r),
            Paragraph(f"-Rs. {deductions:,.2f}", cell_r)
        ]
    ]

    breakdown_table = Table(table_rows, colWidths=[3.2*inch, 1.4*inch, 1.4*inch, 1.5*inch])
    breakdown_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), primary_color),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
    ]))
    story.append(breakdown_table)
    story.append(Spacer(1, 10))

    # Net Amount Paid Banner Box
    net_box_p = Paragraph(
        f"<b>TOTAL SALARY DISBURSED TO WORKER:</b> &nbsp;&nbsp;<font size='14' color='#16a34a'><b>Rs. {paid_amt:,.2f}</b></font>",
        ParagraphStyle('NetBox', parent=styles['Normal'], alignment=2)
    )
    net_table = Table([[net_box_p]], colWidths=[7.5*inch])
    net_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f0fdf4')),
        ('BOX', (0,0), (-1,-1), 1.5, colors.HexColor('#16a34a')),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
        ('RIGHTPADDING', (0,0), (-1,-1), 10),
    ]))
    story.append(net_table)
    story.append(Spacer(1, 25))

    # Signature Seal & Manager Sign Row
    sign_left = Paragraph("<b>EMPLOYEE ACKNOWLEDGEMENT</b><br/><br/><br/>_______________________<br/><font color='#64748b' size='7.5'>Worker Signature / Thumb Impression</font>", styles['Normal'])
    sign_right = Paragraph("<b>AUTHORIZED ISSUER</b><br/><br/><br/>_______________________<br/><font color='#64748b' size='7.5'>Decore Builders Manager / Stamp</font>", ParagraphStyle('RSign', parent=styles['Normal'], alignment=2))

    sign_table = Table([[sign_left, sign_right]], colWidths=[3.75*inch, 3.75*inch])
    sign_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'BOTTOM'),
    ]))
    story.append(sign_table)

    story.append(Spacer(1, 20))
    footer_text = f"<font size='7' color='#94a3b8'>Decore Builders Platform &bull; Computer Generated Salary Voucher &bull; Official Record</font>"
    story.append(Paragraph(footer_text, ParagraphStyle('Footer', parent=styles['Normal'], alignment=1)))

    doc.build(story)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf


def generate_subcontract_receipt_pdf(data):
    """
    Generate a clean, high-precision PDF payment receipt for Subcontractors.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=28, leftMargin=28, topMargin=28, bottomMargin=28
    )
    story = []
    styles = getSampleStyleSheet()

    primary_color = colors.HexColor('#1e3a8a')
    card_bg = colors.HexColor('#f8fafc')

    # Brand Header
    logo_path = get_decore_logo_path()
    if logo_path:
        logo_img = Image(logo_path, width=0.45*inch, height=0.45*inch)
        brand_p = Paragraph("<font size='16' color='#1e3a8a'><b>DECORE CONSTRUCTION</b></font><br/><font size='8' color='#64748b'>Subcontractor Payment Voucher</font>", styles['Normal'])
        header_tbl = Table([[logo_img, brand_p]], colWidths=[0.6*inch, 6.9*inch])
        header_tbl.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'MIDDLE')]))
        story.append(header_tbl)
    else:
        story.append(Paragraph("<font size='16' color='#1e3a8a'><b>DECORE CONSTRUCTION</b></font>", styles['Normal']))
    
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=1.5, color=primary_color, spaceAfter=15))

    # Meta Info Card
    meta_html = f"""
    <b>SUBCONTRACTOR:</b> {data.get('contractor_name')}<br/>
    <b>TRADE &amp; SCOPE:</b> {data.get('trade_display')} &bull; {data.get('title')}<br/>
    <b>WORKSITE:</b> {data.get('worksite_name')}<br/>
    <b>CONTACT PHONE:</b> {data.get('phone') or 'N/A'}
    """
    date_html = f"""
    <b>PAYMENT DATE:</b> {data.get('payment_date')}<br/>
    <b>PAYMENT METHOD:</b> {data.get('payment_method')}<br/>
    <b>REFERENCE / UTR:</b> {data.get('reference_number') or 'N/A'}<br/>
    <b>VOUCHER STATUS:</b> <font color='#16a34a'><b>DISBURSED</b></font>
    """
    p_meta = Paragraph(meta_html, ParagraphStyle('MetaL', parent=styles['Normal'], leading=14, fontSize=8.5))
    p_date = Paragraph(date_html, ParagraphStyle('MetaR', parent=styles['Normal'], leading=14, fontSize=8.5, alignment=2))
    
    meta_table = Table([[p_meta, p_date]], colWidths=[4.2*inch, 3.3*inch])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), card_bg),
        ('PADDING', (0,0), (-1,-1), 8),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
        ('VALIGN', (0,0), (-1,-1), 'TOP')
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 15))

    # Payment Breakdown Table
    cell_h = ParagraphStyle('TH', parent=styles['Normal'], fontName='Helvetica-Bold', textColor=colors.white, fontSize=9)
    cell_l = ParagraphStyle('TL', parent=styles['Normal'], fontSize=8.5)
    cell_r = ParagraphStyle('TR', parent=styles['Normal'], fontSize=8.5, alignment=2)

    rows = [
        [Paragraph("DESCRIPTION", cell_h), Paragraph("VALUATION", ParagraphStyle('THr', parent=cell_h, alignment=2))],
        [Paragraph("Agreed Contract Amount", cell_l), Paragraph(f"Rs. {data.get('contract_amount', 0):,.2f}", cell_r)],
        [Paragraph("Total Cumulative Paid (Including this Payment)", cell_l), Paragraph(f"Rs. {data.get('paid_amount', 0):,.2f}", cell_r)],
        [Paragraph("Remaining Contract Balance Outstanding", cell_l), Paragraph(f"Rs. {data.get('balance_amount', 0):,.2f}", cell_r)],
    ]
    tbl = Table(rows, colWidths=[5.2*inch, 2.3*inch])
    tbl.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), primary_color),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(tbl)
    story.append(Spacer(1, 15))

    # Payment Amount Banner
    disbursed = data.get('disbursed_amount', 0)
    net_p = Paragraph(f"<b>AMOUNT DISBURSED IN THIS PAYMENT:</b> &nbsp;&nbsp;<font size='14' color='#16a34a'><b>Rs. {disbursed:,.2f}</b></font>", ParagraphStyle('Net', parent=styles['Normal'], alignment=2))
    net_tbl = Table([[net_p]], colWidths=[7.5*inch])
    net_tbl.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f0fdf4')),
        ('BOX', (0,0), (-1,-1), 1.5, colors.HexColor('#16a34a')),
        ('PADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(net_tbl)
    story.append(Spacer(1, 25))

    # Signature Block
    sign_l = Paragraph("<b>SUBCONTRACTOR ACKNOWLEDGEMENT</b><br/><br/><br/>_______________________<br/><font color='#64748b' size='7.5'>Subcontractor Signature</font>", styles['Normal'])
    sign_r = Paragraph("<b>AUTHORIZED ISSUER</b><br/><br/><br/>_______________________<br/><font color='#64748b' size='7.5'>Decore Builders Site Manager / Engineer</font>", ParagraphStyle('R', parent=styles['Normal'], alignment=2))
    sign_tbl = Table([[sign_l, sign_r]], colWidths=[3.75*inch, 3.75*inch])
    sign_tbl.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'BOTTOM')]))
    story.append(sign_tbl)

    story.append(Spacer(1, 20))
    footer = "<font size='7' color='#94a3b8'>Decore Builders Platform &bull; Official Subcontractor Payment Receipt</font>"
    story.append(Paragraph(footer, ParagraphStyle('F', parent=styles['Normal'], alignment=1)))

    doc.build(story)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf
