import logging
from datetime import datetime
from typing import Dict, Any
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER

logger = logging.getLogger("OSINT_Tool")


def generate_pdf_report(results: Dict[str, Any], output_file: str):
    """
    Generate a professional PDF report with tiered results.
    
    Args:
        results: Results dictionary
        output_file: Output file path
    """
    logger.info(f"Generating PDF report: {output_file}")
    
    target = results.get('target', 'Unknown')
    target_type = results.get('target_type', 'Unknown')
    stats = results.get('statistics', {})
    
    # Create PDF
    doc = SimpleDocTemplate(output_file, pagesize=letter)
    story = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#667eea'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#667eea'),
        spaceAfter=12,
        spaceBefore=12
    )
    
    # Title Page
    story.append(Paragraph("OSINT Intelligence Report", title_style))
    story.append(Spacer(1, 0.2*inch))
    story.append(Paragraph(f"<b>Target:</b> {target}", styles['Normal']))
    story.append(Paragraph(f"<b>Type:</b> {target_type}", styles['Normal']))
    story.append(Paragraph(f"<b>Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
    story.append(Spacer(1, 0.5*inch))
    
    # Executive Summary
    story.append(Paragraph("Executive Summary", heading_style))
    summary_data = [
        ['Metric', 'Value'],
        ['Total Results', str(stats.get('total_unique', 0))],
        ['Confirmed Findings', str(stats.get('confirmed_count', 0))],
        ['Possible Findings', str(stats.get('possible_count', 0))],
        ['Average Quality Score', f"{stats.get('avg_quality_score', 0):.1f}/100"]
    ]
    
    summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(summary_table)
    story.append(Spacer(1, 0.3*inch))
    
    # Email Enumeration
    if 'emails' in results and results['emails']:
        emails_data = results['emails']
        confirmed = emails_data.get('confirmed_emails', [])
        possible = emails_data.get('possible_emails', [])
        
        story.append(Paragraph("Email Intelligence", heading_style))
        
        if confirmed:
            story.append(Paragraph("Confirmed Emails", styles['Heading3']))
            email_data = [['Email', 'Source', 'Conf']]
            for item in confirmed:
                email_data.append([
                    item.get('email', 'Unknown'),
                    item.get('source', 'Unknown'),
                    f"{int(item.get('confidence', 1.0)*100)}%"
                ])
            
            email_table = Table(email_data, colWidths=[3*inch, 2*inch, 1*inch])
            email_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#28a745')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(email_table)
            story.append(Spacer(1, 0.2*inch))
            
        if possible:
            story.append(Paragraph("Possible Emails (Top 20)", styles['Heading3']))
            email_data = [['Email', 'Source', 'Conf']]
            for item in possible[:20]:
                email_data.append([
                    item.get('email', 'Unknown'),
                    item.get('source', 'Pattern'),
                    f"{int(item.get('confidence', 0.5)*100)}%"
                ])
            
            email_table = Table(email_data, colWidths=[3*inch, 2*inch, 1*inch])
            email_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#ffc107')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(email_table)
            story.append(Spacer(1, 0.2*inch))
    
    # Social Media
    social_media = results.get('social_media', [])
    if social_media:
        story.append(Paragraph("Social Media Profiles", heading_style))
        
        social_data = [['Platform', 'URL', 'Source', 'Conf']]
        for profile in social_media[:20]:
            social_data.append([
                profile.get('platform', 'N/A'),
                Paragraph(profile.get('url', 'N/A'), styles['Normal']), # Wrap long URLs
                profile.get('source', 'Unknown'),
                f"{int(profile.get('confidence', 0.0)*100)}%"
            ])
        
        social_table = Table(social_data, colWidths=[1.5*inch, 2.5*inch, 1.5*inch, 0.8*inch])
        social_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP')
        ]))
        
        story.append(social_table)
    
    # Build PDF
    doc.build(story)
    
    logger.info(f"✓ PDF report saved to {output_file}")
