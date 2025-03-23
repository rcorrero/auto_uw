"""
Data models for the Auto UW package.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, constr

class Claim(BaseModel):
    """Model for insurance claims."""
    date: str
    type: str
    amount: float

    @field_validator('date')
    def validate_date(cls, v):
        """Validate date format."""
        try:
            datetime.strptime(v, '%Y-%m-%d')
        except ValueError:
            raise ValueError('Date must be in YYYY-MM-DD format')
        return v

    @field_validator('type')
    def validate_type(cls, v):
        """Validate claim type."""
        valid_types = {'property', 'liability', 'workers_comp', 'auto'}
        if v not in valid_types:
            raise ValueError(f'Claim type must be one of {valid_types}')
        return v

    @field_validator('amount')
    def validate_amount(cls, v):
        """Validate claim amount."""
        if v <= 0:
            raise ValueError('Claim amount must be positive')
        return v

    def model_dump(self, *args, **kwargs):
        """Convert to dictionary for JSON serialization."""
        return {
            "date": self.date,
            "type": self.type,
            "amount": self.amount
        }

class PolicyRequest(BaseModel):
    """Model for insurance policy requests."""
    business_name: str
    business_type: str
    annual_revenue: float
    employee_count: int
    state: str
    city: str
    years_in_business: int
    business_description: str
    claims_history: List[Claim] = Field(default_factory=list)

    @field_validator('state')
    def validate_state(cls, v):
        """Validate state code."""
        valid_states = {
            'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
            'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
            'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
            'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
            'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY'
        }
        if v.upper() not in valid_states:
            raise ValueError(f'State must be a valid US state code')
        return v.upper()

    @field_validator('annual_revenue')
    def validate_revenue(cls, v):
        """Validate annual revenue."""
        if v <= 0:
            raise ValueError('Annual revenue must be positive')
        return v

    @field_validator('employee_count')
    def validate_employees(cls, v):
        """Validate employee count."""
        if v <= 0:
            raise ValueError('Employee count must be positive')
        return v

    @field_validator('business_description')
    def validate_description(cls, v):
        """Validate business description."""
        if not v.strip():
            raise ValueError('Business description cannot be empty')
        return v.strip()

    def model_dump(self, *args, **kwargs):
        """Convert to dictionary for JSON serialization."""
        return {
            "business_name": self.business_name,
            "business_type": self.business_type,
            "annual_revenue": self.annual_revenue,
            "employee_count": self.employee_count,
            "state": self.state,
            "city": self.city,
            "years_in_business": self.years_in_business,
            "business_description": self.business_description,
            "claims_history": [claim.model_dump() for claim in self.claims_history]
        }

class Document(BaseModel):
    """Model for storing documents in the document store."""
    doc_id: str
    title: str
    content: str
    doc_type: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator('doc_id')
    def validate_doc_id(cls, v):
        """Validate document ID."""
        if not v.strip():
            raise ValueError('Document ID cannot be empty')
        return v.strip()

    @field_validator('title')
    def validate_title(cls, v):
        """Validate document title."""
        if not v.strip():
            raise ValueError('Document title cannot be empty')
        return v.strip()

    @field_validator('content')
    def validate_content(cls, v):
        """Validate document content."""
        if not v.strip():
            raise ValueError('Document content cannot be empty')
        return v.strip()

    @field_validator('doc_type')
    def validate_doc_type(cls, v):
        """Validate document type."""
        valid_types = {'guideline', 'regulation', 'assessment', 'policy'}
        if v not in valid_types:
            raise ValueError(f'Document type must be one of {valid_types}')
        return v 