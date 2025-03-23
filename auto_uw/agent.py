"""
Automated underwriting agent using Claude for risk assessment and premium calculation.
"""

import os
import json
import uuid
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import pandas as pd
from dotenv import load_dotenv
from anthropic import Anthropic
from pydantic import BaseModel, Field
from fastapi import FastAPI, HTTPException
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from .report_generator import QuoteReportGenerator
from .models import PolicyRequest, Claim

# Load environment variables
load_dotenv()

# Get API key and model from environment
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-3-sonnet-20240229")  # Default to latest model if not specified

if not ANTHROPIC_API_KEY:
    raise ValueError("ANTHROPIC_API_KEY environment variable is required")

class PolicyRequest(BaseModel):
    """Structure for incoming policy quote requests"""
    business_name: str
    business_type: str
    annual_revenue: float
    employee_count: int
    state: str
    city: str
    years_in_business: int
    business_description: str
    claims_history: List[Dict[str, Any]]
    additional_notes: Optional[str] = None

class UnderwritingAgent:
    """Agent for processing insurance quotes."""
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize the agent with configuration."""
        self.config = config or {}
        self.api_key = os.getenv('ANTHROPIC_API_KEY')
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment variables")
        
        self.model = os.getenv('CLAUDE_MODEL', CLAUDE_MODEL)
        self.client = Anthropic(api_key=self.api_key)
    
    def _parse_claude_response(self, response: Any) -> Dict[str, Any]:
        """Parse Claude's response into a dictionary."""
        try:
            # Extract the text content from the response
            text = response.content[0].text
            
            # Try to find JSON content between triple backticks if present
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].strip()
            
            # Parse the JSON
            return json.loads(text)
        except (json.JSONDecodeError, IndexError, AttributeError) as e:
            print(f"Error parsing Claude response: {e}")
            print(f"Raw response: {response}")
            raise ValueError("Failed to parse Claude's response")
    
    def evaluate_risk(self, request: Union[PolicyRequest, Dict[str, Any]]) -> Dict[str, Any]:
        """Evaluate the risk profile of a policy request."""
        # Convert dict to PolicyRequest if needed
        if isinstance(request, dict):
            request = PolicyRequest(**request)
        
        # Create a prompt for risk evaluation
        prompt = f"""
        Evaluate the risk profile for this business:
        
        Business: {request.business_name}
        Type: {request.business_type}
        Revenue: ${request.annual_revenue:,.2f}
        Employees: {request.employee_count}
        Location: {request.city}, {request.state}
        Years in Business: {request.years_in_business}
        Description: {request.business_description}
        
        Claims History:
        {json.dumps(request.claims_history, indent=2)}
        
        Please provide a JSON response with:
        1. risk_profile (low/medium/high)
        2. risk_factors (list of specific factors)
        3. risk_score (0-100)
        
        Format your response as valid JSON.
        """
        
        # Get Claude's analysis
        response = self.client.messages.create(
            model=self.model,
            max_tokens=1000,
            temperature=0.7,
            system="You are an expert insurance underwriter. Evaluate the business risk profile. Always respond with valid JSON.",
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )
        
        return self._parse_claude_response(response)
    
    def make_decision(self, request: PolicyRequest) -> Dict[str, Any]:
        """Make an underwriting decision for a policy request."""
        try:
            # Get risk evaluation
            risk_evaluation = self.evaluate_risk(request)
            
            # Calculate premium
            premium = self._calculate_premium(request)
            
            # Generate quote ID
            quote_id = f"QUOTE_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Generate report
            report_path = self._generate_report(request, risk_evaluation, {
                'quote_id': quote_id,
                'risk_profile': risk_evaluation['risk_profile'],
                'risk_factors': risk_evaluation['risk_factors'],
                'risk_score': risk_evaluation['risk_score'],
                'premium_estimate': premium,
                'conditions': self._determine_conditions(request, risk_evaluation),
                'explanation': self._generate_explanation(request, risk_evaluation, premium)
            })
            
            return {
                'business_name': request.business_name,
                'quote_id': quote_id,
                'risk_profile': risk_evaluation['risk_profile'],
                'risk_factors': risk_evaluation['risk_factors'],
                'risk_score': risk_evaluation['risk_score'],
                'premium_estimate': premium,
                'conditions': self._determine_conditions(request, risk_evaluation),
                'explanation': self._generate_explanation(request, risk_evaluation, premium),
                'report_path': report_path
            }
            
        except Exception as e:
            raise Exception(f"Failed to make decision: {str(e)}")
    
    def process_policy_request(self, request: PolicyRequest) -> Dict:
        """Process a policy request and generate a quote."""
        # Generate a unique quote ID
        quote_id = str(uuid.uuid4())
        
        # Create the prompt for Claude
        prompt = self._create_analysis_prompt(request)
        
        # Get Claude's analysis
        response = self.client.messages.create(
            model=self.model,
            max_tokens=1000,
            temperature=0.7,
            system="You are an expert insurance underwriter. Analyze the business details and provide a risk assessment and premium estimate. Always respond with valid JSON.",
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )
        
        # Parse Claude's response
        analysis = self._parse_claude_response(response)
        
        # Calculate premium
        base_rate = self._calculate_base_rate(request.business_type)
        adjustment_factor = self._calculate_adjustment_factor(request, analysis)
        premium = base_rate * adjustment_factor
        
        # Generate report
        report_path = self._generate_report(request, analysis, premium)
        
        # Prepare response
        return {
            "quote_id": quote_id,
            "business_name": request.business_name,
            "premium_estimate": premium,
            "risk_profile": analysis.get("risk_profile", "unknown"),
            "risk_factors": analysis.get("risk_factors", []),
            "report_path": report_path,
            "timestamp": datetime.now().isoformat()
        }
    
    def _create_analysis_prompt(self, request: PolicyRequest) -> str:
        """Create the prompt for Claude's analysis."""
        return f"""
        Please analyze this business for insurance underwriting:
        
        Business: {request.business_name}
        Type: {request.business_type}
        Revenue: ${request.annual_revenue:,.2f}
        Employees: {request.employee_count}
        Location: {request.city}, {request.state}
        Years in Business: {request.years_in_business}
        Description: {request.business_description}
        
        Claims History:
        {json.dumps(request.claims_history, indent=2)}
        
        Additional Notes: {request.additional_notes}
        
        Please provide a JSON response with:
        1. risk_profile (low/medium/high)
        2. risk_factors (list of specific factors)
        3. recommendations (list of risk mitigation steps)
        
        Format your response as valid JSON.
        """
    
    def _calculate_base_rate(self, business_type: str) -> float:
        """Calculate the base rate for a business type."""
        base_rates = {
            'restaurant': 5000,
            'retail': 4000,
            'manufacturing': 8000,
            'construction': 10000,
            'professional_services': 3000
        }
        return base_rates.get(business_type.lower(), 5000)

    def _calculate_revenue_factor(self, annual_revenue: float) -> float:
        """Calculate the revenue adjustment factor."""
        if annual_revenue < 500000:
            return 0.8
        elif annual_revenue < 1000000:
            return 1.0
        elif annual_revenue < 2000000:
            return 1.2
        else:
            return 1.5

    def _calculate_employee_factor(self, employee_count: int) -> float:
        """Calculate the employee count adjustment factor."""
        if employee_count < 10:
            return 0.8
        elif employee_count < 25:
            return 1.0
        elif employee_count < 50:
            return 1.2
        else:
            return 1.5

    def _calculate_claims_factor(self, claims_history: List[Dict[str, Any]]) -> float:
        """Calculate the claims history adjustment factor."""
        if not claims_history:
            return 0.9
        
        total_claims = len(claims_history)
        total_amount = sum(claim.get('amount', 0) for claim in claims_history)
        
        if total_claims == 1 and total_amount < 5000:
            return 1.1
        elif total_claims == 1:
            return 1.2
        elif total_claims == 2:
            return 1.3
        else:
            return 1.5

    def _calculate_years_factor(self, years_in_business: int) -> float:
        """Calculate the years in business adjustment factor."""
        if years_in_business < 2:
            return 1.2
        elif years_in_business < 5:
            return 1.1
        elif years_in_business < 10:
            return 1.0
        else:
            return 0.9

    def _calculate_premium(self, request: PolicyRequest) -> float:
        """Calculate the final premium estimate."""
        base_rate = self._calculate_base_rate(request.business_type)
        revenue_factor = self._calculate_revenue_factor(request.annual_revenue)
        employee_factor = self._calculate_employee_factor(request.employee_count)
        claims_factor = self._calculate_claims_factor(request.claims_history)
        years_factor = self._calculate_years_factor(request.years_in_business)
        
        return base_rate * revenue_factor * employee_factor * claims_factor * years_factor
    
    def _calculate_adjustment_factor(self, request: PolicyRequest, analysis: Dict) -> float:
        """Calculate the adjustment factor based on risk profile and other factors."""
        # Base adjustment factors
        risk_factors = {
            "low": 0.8,
            "medium": 1.0,
            "high": 1.5
        }
        
        # Start with risk profile adjustment
        factor = risk_factors.get(analysis.get("risk_profile", "medium"), 1.0)
        
        # Adjust for claims history
        if request.claims_history:
            factor *= 1.2
        
        # Adjust for years in business
        if request.years_in_business < 3:
            factor *= 1.1
        
        return factor
    
    def _generate_report(self, request: PolicyRequest, analysis: Dict, premium: float) -> str:
        """Generate a detailed PDF report."""
        # Create reports directory if it doesn't exist
        os.makedirs("reports", exist_ok=True)
        
        # Generate report filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = f"reports/quote_{timestamp}.pdf"
        
        # Create the PDF document
        doc = SimpleDocTemplate(
            report_path,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        # Get styles
        styles = getSampleStyleSheet()
        title_style = styles['Heading1']
        heading_style = styles['Heading2']
        normal_style = styles['Normal']
        
        # Create custom styles
        risk_style = ParagraphStyle(
            'RiskStyle',
            parent=normal_style,
            textColor=colors.red if analysis.get('risk_profile') == 'high' else
                     colors.orange if analysis.get('risk_profile') == 'medium' else
                     colors.green
        )
        
        # Build the document
        story = []
        
        # Title
        story.append(Paragraph(f"Insurance Quote Report for {request.business_name}", title_style))
        story.append(Spacer(1, 12))
        
        # Quote Details
        story.append(Paragraph("Quote Details", heading_style))
        story.append(Spacer(1, 6))
        
        quote_data = [
            ["Business Name:", request.business_name],
            ["Business Type:", request.business_type],
            ["Annual Revenue:", f"${request.annual_revenue:,.2f}"],
            ["Employee Count:", str(request.employee_count)],
            ["Location:", f"{request.city}, {request.state}"],
            ["Years in Business:", str(request.years_in_business)],
            ["Premium Estimate:", f"${premium:,.2f}"],
            ["Risk Profile:", analysis.get('risk_profile', 'unknown')],
            ["Generated On:", datetime.now().strftime("%Y-%m-%d %H:%M:%S")]
        ]
        
        quote_table = Table(quote_data, colWidths=[2*inch, 4*inch])
        quote_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ]))
        story.append(quote_table)
        story.append(Spacer(1, 12))
        
        # Premium Calculation Breakdown
        story.append(Paragraph("Premium Calculation Breakdown", heading_style))
        story.append(Spacer(1, 6))
        
        # Calculate factors
        base_rate = self._calculate_base_rate(request.business_type)
        revenue_factor = self._calculate_revenue_factor(request.annual_revenue)
        employee_factor = self._calculate_employee_factor(request.employee_count)
        claims_factor = self._calculate_claims_factor(request.claims_history)
        years_factor = self._calculate_years_factor(request.years_in_business)
        
        # Create calculation table
        calc_data = [
            ["Factor", "Value", "Explanation"],
            ["Base Rate", f"${base_rate:,.2f}", f"Standard rate for {request.business_type.title()} businesses"],
            ["Revenue Factor", f"{revenue_factor:.2f}x", f"Based on annual revenue of ${request.annual_revenue:,.2f}"],
            ["Employee Factor", f"{employee_factor:.2f}x", f"Based on {request.employee_count} employees"],
            ["Claims Factor", f"{claims_factor:.2f}x", f"Based on {len(request.claims_history)} claims"],
            ["Years Factor", f"{years_factor:.2f}x", f"Based on {request.years_in_business} years in business"],
            ["Final Premium", f"${premium:,.2f}", f"${base_rate:,.2f} × {revenue_factor:.2f} × {employee_factor:.2f} × {claims_factor:.2f} × {years_factor:.2f}"]
        ]
        
        calc_table = Table(calc_data, colWidths=[2*inch, 1.5*inch, 2.5*inch])
        calc_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ]))
        story.append(calc_table)
        story.append(Spacer(1, 12))
        
        # Risk Assessment
        story.append(Paragraph("Risk Assessment", heading_style))
        story.append(Spacer(1, 6))
        
        risk_profile = analysis.get('risk_profile', 'unknown').upper()
        story.append(Paragraph(f"Risk Profile: {risk_profile}", risk_style))
        story.append(Spacer(1, 6))
        
        # Risk Score
        if 'risk_score' in analysis:
            story.append(Paragraph(f"Risk Score: {analysis['risk_score']:.2f}", normal_style))
            story.append(Spacer(1, 6))
        
        # Risk Factors
        story.append(Paragraph("Risk Factors:", heading_style))
        story.append(Spacer(1, 6))
        
        for factor in analysis.get('risk_factors', []):
            story.append(Paragraph(f"• {factor}", normal_style))
        story.append(Spacer(1, 12))
        
        # Business Description
        story.append(Paragraph("Business Description", heading_style))
        story.append(Spacer(1, 6))
        story.append(Paragraph(request.business_description, normal_style))
        story.append(Spacer(1, 12))
        
        # Claims History
        if request.claims_history:
            story.append(Paragraph("Claims History", heading_style))
            story.append(Spacer(1, 6))
            
            claims_data = [["Date", "Type", "Amount"]]
            for claim in request.claims_history:
                claims_data.append([
                    claim.get('date', 'N/A'),
                    claim.get('type', 'N/A'),
                    f"${claim.get('amount', 0):,.2f}"
                ])
            
            claims_table = Table(claims_data, colWidths=[2*inch, 2*inch, 2*inch])
            claims_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ]))
            story.append(claims_table)
            story.append(Spacer(1, 12))
        
        # Required Conditions
        conditions = self._determine_conditions(request, analysis)
        if conditions:
            story.append(Paragraph("Required Conditions", heading_style))
            story.append(Spacer(1, 6))
            
            for condition in conditions:
                story.append(Paragraph(f"• {condition}", normal_style))
            story.append(Spacer(1, 12))
        
        # Additional Notes
        if request.additional_notes:
            story.append(Paragraph("Additional Notes", heading_style))
            story.append(Spacer(1, 6))
            story.append(Paragraph(request.additional_notes, normal_style))
        
        # Build the PDF
        doc.build(story)
        
        return report_path

    def _determine_conditions(self, request: PolicyRequest, risk_evaluation: Dict[str, Any]) -> List[str]:
        """Determine special conditions based on risk evaluation."""
        conditions = []
        
        # High risk conditions
        if risk_evaluation['risk_profile'].lower() == 'high':
            conditions.extend([
                "Monthly safety inspections required",
                "Employee training program implementation",
                "Security system installation",
                "Regular risk assessment reviews"
            ])
        
        # Business type specific conditions
        if request.business_type.lower() == 'restaurant':
            conditions.extend([
                "Food safety certification required",
                "Regular kitchen equipment maintenance",
                "Employee hygiene training"
            ])
        elif request.business_type.lower() == 'manufacturing':
            conditions.extend([
                "Equipment safety inspections",
                "Worker safety training",
                "Emergency response plan"
            ])
        
        # Claims history conditions
        if request.claims_history:
            conditions.extend([
                "Claims review every 6 months",
                "Risk mitigation plan required"
            ])
        
        return conditions

    def _generate_explanation(self, request: PolicyRequest, risk_evaluation: Dict[str, Any], premium: float) -> str:
        """Generate a detailed explanation of the premium calculation."""
        base_rate = self._calculate_base_rate(request.business_type)
        revenue_factor = self._calculate_revenue_factor(request.annual_revenue)
        employee_factor = self._calculate_employee_factor(request.employee_count)
        claims_factor = self._calculate_claims_factor(request.claims_history)
        years_factor = self._calculate_years_factor(request.years_in_business)
        
        explanation = [
            f"Premium calculation for {request.business_name}:",
            f"1. Base Rate: ${base_rate:,.2f} (based on {request.business_type.title()} business type)",
            f"2. Revenue Adjustment: {revenue_factor:.2f}x (based on annual revenue of ${request.annual_revenue:,.2f})",
            f"3. Employee Count Adjustment: {employee_factor:.2f}x (based on {request.employee_count} employees)",
            f"4. Claims History Adjustment: {claims_factor:.2f}x (based on {len(request.claims_history)} claims)",
            f"5. Years in Business Adjustment: {years_factor:.2f}x (based on {request.years_in_business} years)",
            f"\nFinal Calculation: ${base_rate:,.2f} × {revenue_factor:.2f} × {employee_factor:.2f} × {claims_factor:.2f} × {years_factor:.2f} = ${premium:,.2f}",
            f"\nRisk Profile: {risk_evaluation['risk_profile'].title()}",
            f"Risk Score: {risk_evaluation['risk_score']:.2f}",
            "\nKey Risk Factors:",
            *[f"- {factor}" for factor in risk_evaluation['risk_factors']]
        ]
        
        return "\n".join(explanation)

# Create FastAPI app
app = FastAPI(title="Auto UW API")

# Initialize agent
agent = UnderwritingAgent()

@app.post("/quote")
async def get_quote(request: PolicyRequest):
    """Get an insurance quote for a business"""
    return agent.process_policy_request(request)