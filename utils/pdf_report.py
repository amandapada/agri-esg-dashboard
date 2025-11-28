from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
import plotly.io as pio
from io import BytesIO
from datetime import datetime

def generate_pdf_report(farm_data, farmer_name, year, insights_list, gauge_fig, pie_fig, donut_fig, bar_fig, line_fig=None):
    """
    Generate a comprehensive PDF report with all charts and metrics.
    Returns BytesIO object ready for download.
    """
    
    # Create PDF buffer
    pdf_buffer = BytesIO()
    
    # Create PDF document
    doc = SimpleDocTemplate(
        pdf_buffer,
        pagesize=A4,
        rightMargin=0.5*inch,
        leftMargin=0.5*inch,
        topMargin=0.75*inch,
        bottomMargin=0.75*inch
    )
    
    # Container for PDF elements
    elements = []
    
    # Define styles
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=28,
        textColor=colors.HexColor('#2d5016'),
        spaceAfter=12,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#5d4037'),
        spaceAfter=12,
        spaceBefore=12,
        fontName='Helvetica-Bold',
        borderPadding=10
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=11,
        alignment=TA_JUSTIFY,
        spaceAfter=12,
        textColor=colors.HexColor('#5d4037')
    )
    
    # === HEADER ===
    elements.append(Paragraph(f"🌾 Farm Sustainability Report", title_style))
    elements.append(Spacer(1, 0.2*inch))
    
    # Use .get() to avoid crashing if optional data is missing
    farm_name_val = farm_data.get('farm_name', 'Unknown Farm')
    
    elements.append(Paragraph(f"<b>Farm Name:</b> {farm_name_val}", normal_style))
    # Changed label to "Report For" since we are passing the Farm Name/Greeting here
    elements.append(Paragraph(f"<b>Report For:</b> {farmer_name}", normal_style))
    elements.append(Paragraph(f"<b>Year:</b> {year}", normal_style))
    elements.append(Paragraph(f"<b>Generated:</b> {datetime.now().strftime('%d %B %Y')}", normal_style))
    elements.append(Spacer(1, 0.3*inch))
    
    # === OVERALL SCORE SECTION ===
    elements.append(Paragraph("Your Farm's ESG Score", heading_style))
    
    esg_score = farm_data.get('esg_score', 0)
    
    # Updated text to plain English logic
    if esg_score >= 70:
        message = "Healthy Profile! You're leading the way."
        color = "#2d5016"
    elif esg_score >= 50:
        message = "On Track! A few improvements will help."
        color = "#f9a825"
    else:
        message = "Needs Work. Let's improve your practices."
        color = "#c62828"
    
    elements.append(Paragraph(f"<b>Overall Score: {esg_score:.0f}/100</b>", 
                             ParagraphStyle('ScoreStyle', parent=normal_style, fontSize=14, 
                                          textColor=colors.HexColor(color))))
    elements.append(Paragraph(message, normal_style))
    elements.append(Spacer(1, 0.2*inch))
    
    # Add gauge chart image
    try:
        gauge_img_buffer = BytesIO()
        gauge_fig.write_image(gauge_img_buffer, format='png', width=400, height=300)
        gauge_img_buffer.seek(0)
        gauge_img = Image(gauge_img_buffer, width=3*inch, height=2.25*inch)
        elements.append(gauge_img)
    except:
        elements.append(Paragraph("(Gauge chart unavailable)", normal_style))
    
    elements.append(Spacer(1, 0.3*inch))
    
    # === ESG COMPONENTS ===
    elements.append(Paragraph("Score Breakdown", heading_style))
    
    e_score = farm_data.get('e_score', 0)
    s_score = farm_data.get('s_score', 0)
    g_score = farm_data.get('g_score', 0)
    
    # Plain English assessments
    def get_assessment(score):
        if score >= 70: return 'Healthy'
        if score >= 50: return 'On Track'
        return 'Needs Work'

    score_data = [
        ['Component', 'Score', 'Status'],
        ['Environment (50%)', f"{e_score:.0f}/100", get_assessment(e_score)],
        ['Social (30%)', f"{s_score:.0f}/100", get_assessment(s_score)],
        ['Governance (20%)', f"{g_score:.0f}/100", get_assessment(g_score)],
    ]
    
    score_table = Table(score_data, colWidths=[2.5*inch, 1.5*inch, 1.5*inch])
    score_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4a7c29')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 11),
    ]))
    elements.append(score_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Add pie chart
    try:
        pie_img_buffer = BytesIO()
        pie_fig.write_image(pie_img_buffer, format='png', width=500, height=400)
        pie_img_buffer.seek(0)
        pie_img = Image(pie_img_buffer, width=3.5*inch, height=2.8*inch)
        elements.append(pie_img)
    except:
        elements.append(Paragraph("(Pie chart unavailable)", normal_style))
    
    elements.append(PageBreak())
    
    # === KEY METRICS ===
    elements.append(Paragraph("Quick Stats", heading_style))
    
    # Safe extraction of optional metrics
    area = farm_data.get('total_farm_area_ha', 0)
    emissions = farm_data.get('emissions_per_ha', 0)
    nitrogen = farm_data.get('n_per_ha', 0)
    
    # Calculate SFI average safely
    sfi_score = 0
    sfi_count = 0
    if 'sfi_soil_compliance_rate' in farm_data: 
        sfi_score += farm_data['sfi_soil_compliance_rate']
        sfi_count += 1
    if 'sfi_nutrient_compliance_rate' in farm_data: 
        sfi_score += farm_data['sfi_nutrient_compliance_rate']
        sfi_count += 1
    if 'sfi_hedgerow_compliance_rate' in farm_data: 
        sfi_score += farm_data['sfi_hedgerow_compliance_rate']
        sfi_count += 1
        
    sfi_final = (sfi_score / max(sfi_count, 1)) * 100 if sfi_count > 0 else 0

    # New Logic: Healthy / Low / Needs work / On track
    metrics_data = [
        ['Metric', 'Value', 'Status'],
        ['Total Farm Area', f"{area:.1f} ha", '✓ On Track'],
        
        # Emissions (Lower is better)
        ['Emissions', f"{emissions:.0f} kg/ha", 'Low' if emissions < 30 else 'Okay' if emissions < 50 else 'High'],
        
        # Nitrogen (Lower is better)
        ['Nitrogen Use', f"{nitrogen:.0f} kg/ha", 'Low' if nitrogen < 50 else 'Okay' if nitrogen < 100 else 'High'],
        
        # Compliance
        ['Compliance', f"{sfi_final:.0f}%", 'Healthy' if sfi_final > 80 else 'On Track'],
    ]
    
    metrics_table = Table(metrics_data, colWidths=[2.5*inch, 1.5*inch, 1.5*inch])
    metrics_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4a7c29')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
    ]))
    elements.append(metrics_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Add donut chart
    try:
        donut_img_buffer = BytesIO()
        donut_fig.write_image(donut_img_buffer, format='png', width=500, height=400)
        donut_img_buffer.seek(0)
        donut_img = Image(donut_img_buffer, width=3.5*inch, height=2.8*inch)
        elements.append(donut_img)
    except:
        pass
    
    elements.append(PageBreak())
    
    # === RECOMMENDATIONS ===
    elements.append(Paragraph("What You Can Do This Season", heading_style))
    
    # Filter out the "Hello X" greeting from the insights list so it doesn't look weird in a list
    clean_insights = [i for i in insights_list if not i.lower().startswith(('hello', 'hi ', 'dear'))]
    
    if not clean_insights:
        clean_insights = insights_list # Fallback if filtering removes everything

    for i, insight in enumerate(clean_insights, 1):
        elements.append(Paragraph(f"<b>{i}.</b> {insight}", normal_style))
    
    elements.append(Spacer(1, 0.3*inch))
    
    # === COMPARISON ===
    elements.append(Paragraph("Your Farm vs. Others", heading_style))
    
    try:
        bar_img_buffer = BytesIO()
        bar_fig.write_image(bar_img_buffer, format='png', width=600, height=400)
        bar_img_buffer.seek(0)
        bar_img = Image(bar_img_buffer, width=5*inch, height=3.33*inch)
        elements.append(bar_img)
    except:
        elements.append(Paragraph("(Comparison chart unavailable)", normal_style))
    
    # Add multi-year progress if available
    if line_fig:
        elements.append(PageBreak())
        elements.append(Paragraph("Your Progress Over Time", heading_style))
        try:
            line_img_buffer = BytesIO()
            line_fig.write_image(line_img_buffer, format='png', width=600, height=400)
            line_img_buffer.seek(0)
            line_img = Image(line_img_buffer, width=5*inch, height=3.33*inch)
            elements.append(line_img)
        except:
            pass
    
    elements.append(Spacer(1, 0.5*inch))
    elements.append(Paragraph(
        "<i>This report was generated by the AgriESG Dashboard.</i>",
        ParagraphStyle('Footer', parent=normal_style, fontSize=9, textColor=colors.grey)
    ))
    
    # Build PDF
    doc.build(elements)
    pdf_buffer.seek(0)
    
    return pdf_buffer