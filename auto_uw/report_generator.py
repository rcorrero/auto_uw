"""
Module for generating PDF reports of insurance quotes.
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER

class QuoteReportGenerator:
    """Generates PDF reports for insurance quotes."""
    
    def __init__(self, quotes_dir: str = "quotes"):
        """Initialize the report generator."""
        self.quotes_dir = Path(quotes_dir)
        self.quotes_dir.mkdir(parents=True, exist_ok=True)
        self.styles = getSampleStyleSheet()
        
        # Create custom styles
        self.styles.add(ParagraphStyle(
            name='QuoteTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER
        ))
        
        self.styles.add(ParagraphStyle(
            name='QuoteSubtitle',
            parent=self.styles['Heading2'],
            fontSize=16,
            spaceAfter=20
        ))
        
        self.styles.add(ParagraphStyle(
            name='QuoteBody',
            parent=self.styles['Normal'],
            fontSize=12,
            spaceAfter=12
        ))
    
    def _create_header(self, quote_id: str, business_name: str) -> list:
        """Create the header section of the report."""
        elements = []
        
        # Title
        elements.append(Paragraph("Insurance Quote Report", self.styles['QuoteTitle']))
        
        # Quote ID and Business Name
        header_data = [
            ["Quote ID:", quote_id],
            ["Business Name:", business_name],
            ["Generated At:", datetime.now().strftime("%Y-%m-%d %H:%M:%S")]
        ]
        
        header_table = Table(header_data, colWidths=[2*inch, 4*inch])
        header_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ]))
        
        elements.append(header_table)
        elements.append(Spacer(1, 20))
        
        return elements
    
    def _create_business_info(self, request: Dict[str, Any]) -> list:
        """Create the business information section."""
        elements = []
        elements.append(Paragraph("Business Information", self.styles['QuoteSubtitle']))
        
        # Business details
        business_data = [
            ["Business Type:", request['business_type']],
            ["Annual Revenue:", f"${request['annual_revenue']:,.2f}"],
            ["Employee Count:", str(request['employee_count'])],
            ["Location:", f"{request['city']}, {request['state']}"],
            ["Years in Business:", str(request['years_in_business'])]
        ]
        
        business_table = Table(business_data, colWidths=[2*inch, 4*inch])
        business_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ]))
        
        elements.append(business_table)
        elements.append(Spacer(1, 20))
        
        # Business Description
        elements.append(Paragraph("Business Description:", self.styles['QuoteBody']))
        elements.append(Paragraph(request['business_description'], self.styles['QuoteBody']))
        elements.append(Spacer(1, 20))
        
        # Claims History
        elements.append(Paragraph("Claims History:", self.styles['QuoteBody']))
        if request['claims_history']:
            claims_data = [["Date", "Type", "Amount"]]
            for claim in request['claims_history']:
                claims_data.append([
                    claim['date'],
                    claim['type'],
                    f"${claim['amount']:,.2f}"
                ])
            
            claims_table = Table(claims_data, colWidths=[2*inch, 2*inch, 2*inch])
            claims_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 12),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ]))
            elements.append(claims_table)
        else:
            elements.append(Paragraph("No previous claims", self.styles['QuoteBody']))
        
        elements.append(Spacer(1, 20))
        return elements
    
    def _create_risk_assessment(self, response: Dict[str, Any]) -> list:
        """Create the risk assessment section."""
        elements = []
        elements.append(Paragraph("Risk Assessment", self.styles['QuoteSubtitle']))
        
        # Risk Profile
        risk_data = [
            ["Risk Profile:", response['risk_profile'].upper()],
            ["Base Rate:", f"${response['base_rate']:,.2f}"],
            ["Adjustment Factor:", f"{response['adjustment_factor']:.2f}x"],
            ["Final Premium:", f"${response['premium_estimate']:,.2f}"]
        ]
        
        risk_table = Table(risk_data, colWidths=[2*inch, 4*inch])
        risk_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ]))
        
        elements.append(risk_table)
        elements.append(Spacer(1, 20))
        
        # Special Considerations
        elements.append(Paragraph("Special Considerations:", self.styles['QuoteBody']))
        if response['special_considerations']:
            for consideration in response['special_considerations']:
                elements.append(Paragraph(f"• {consideration}", self.styles['QuoteBody']))
        else:
            elements.append(Paragraph("No special considerations identified", self.styles['QuoteBody']))
        
        elements.append(Spacer(1, 20))
        
        # Recommended Coverage
        elements.append(Paragraph("Recommended Coverage:", self.styles['QuoteBody']))
        if response['recommended_coverage']:
            for coverage in response['recommended_coverage']:
                elements.append(Paragraph(f"• {coverage}", self.styles['QuoteBody']))
        else:
            elements.append(Paragraph("Standard coverage recommended", self.styles['QuoteBody']))
        
        elements.append(Spacer(1, 20))
        return elements
    
    def _create_model_analysis(self, model_response: str) -> list:
        """Create the model analysis section."""
        elements = []
        elements.append(Paragraph("Model Analysis", self.styles['QuoteSubtitle']))
        elements.append(Paragraph(model_response, self.styles['QuoteBody']))
        elements.append(Spacer(1, 20))
        return elements
    
    def generate_report(self, 
                       quote_id: str,
                       request: Dict[str, Any],
                       response: Dict[str, Any],
                       model_response: str) -> str:
        """Generate a PDF report for a quote."""
        # Create the PDF document
        filename = self.quotes_dir / f"quote_{quote_id}.pdf"
        doc = SimpleDocTemplate(
            str(filename),
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        # Build the report content
        elements = []
        
        # Add each section
        elements.extend(self._create_header(quote_id, request['business_name']))
        elements.extend(self._create_business_info(request))
        elements.extend(self._create_risk_assessment(response))
        elements.extend(self._create_model_analysis(model_response))
        
        # Build the PDF
        doc.build(elements)
        
        return str(filename) 