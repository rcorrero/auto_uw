"""
Tests for the UnderwritingAgent class.
"""

import os
import json
import pytest
from unittest.mock import Mock, patch
from datetime import datetime
from auto_uw.agent import UnderwritingAgent
from auto_uw.models import PolicyRequest, Claim

@pytest.fixture
def mock_anthropic():
    """Mock Anthropic client."""
    with patch('auto_uw.agent.Anthropic') as mock:
        yield mock

@pytest.fixture
def agent(mock_anthropic):
    """Create an UnderwritingAgent instance with mocked dependencies."""
    with patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'test_key'}):
        agent = UnderwritingAgent()
        agent.client = Mock()
        return agent

@pytest.fixture
def sample_request():
    """Create a sample policy request."""
    return PolicyRequest(
        business_name="Test Restaurant",
        business_type="restaurant",
        annual_revenue=500000,
        employee_count=15,
        state="CA",
        city="San Francisco",
        years_in_business=5,
        business_description="Family-owned restaurant",
        claims_history=[
            Claim(
                date="2023-01-15",
                type="property",
                amount=5000
            )
        ]
    )

@pytest.fixture
def sample_risk_evaluation():
    """Create a sample risk evaluation response."""
    return {
        "risk_profile": "medium",
        "risk_factors": [
            "Recent property claim",
            "High-traffic location",
            "Limited years in business"
        ],
        "risk_score": 65
    }

@pytest.fixture
def sample_decision():
    """Create a sample underwriting decision response."""
    return {
        "decision": "approved",
        "premium_estimate": 7500.00,
        "conditions": [
            "Install security cameras",
            "Regular safety inspections"
        ],
        "explanation": "Business shows moderate risk but meets underwriting criteria"
    }

def test_agent_initialization(agent):
    """Test agent initialization."""
    assert agent.api_key == 'test_key'
    assert agent.model == 'claude-3-sonnet-20240229'
    assert agent.client is not None

def test_evaluate_risk(agent, sample_request, sample_risk_evaluation):
    """Test risk evaluation."""
    # Mock Claude's response
    mock_response = Mock()
    mock_response.content = [Mock(text=json.dumps(sample_risk_evaluation))]
    agent.client.messages.create.return_value = mock_response
    
    # Test risk evaluation
    result = agent.evaluate_risk(sample_request)
    
    # Verify results
    assert result == sample_risk_evaluation
    assert result['risk_profile'] in ['low', 'medium', 'high']
    assert isinstance(result['risk_factors'], list)
    assert isinstance(result['risk_score'], int)
    
    # Verify API call
    agent.client.messages.create.assert_called_once()
    call_args = agent.client.messages.create.call_args[1]
    assert call_args['model'] == agent.model
    assert call_args['max_tokens'] == 1000
    assert call_args['temperature'] == 0.7

def test_make_decision(agent, sample_request, sample_risk_evaluation, sample_decision):
    """Test underwriting decision making."""
    # Mock Claude's responses
    mock_risk_response = Mock()
    mock_risk_response.content = [Mock(text=json.dumps(sample_risk_evaluation))]
    mock_decision_response = Mock()
    mock_decision_response.content = [Mock(text=json.dumps(sample_decision))]
    
    agent.client.messages.create.side_effect = [
        mock_risk_response,
        mock_decision_response
    ]
    
    # Test decision making
    result = agent.make_decision(sample_request)
    
    # Verify results
    assert result == sample_decision
    assert result['decision'] in ['approved', 'declined', 'review']
    assert isinstance(result['premium_estimate'], float)
    assert isinstance(result['conditions'], list)
    assert isinstance(result['explanation'], str)
    
    # Verify API calls
    assert agent.client.messages.create.call_count == 2

def test_process_policy_request(agent, sample_request, sample_risk_evaluation, sample_decision):
    """Test complete policy request processing."""
    # Mock Claude's responses
    mock_risk_response = Mock()
    mock_risk_response.content = [Mock(text=json.dumps(sample_risk_evaluation))]
    mock_decision_response = Mock()
    mock_decision_response.content = [Mock(text=json.dumps(sample_decision))]
    
    agent.client.messages.create.side_effect = [
        mock_risk_response,
        mock_decision_response
    ]
    
    # Test request processing
    result = agent.process_policy_request(sample_request)
    
    # Verify results
    assert 'quote_id' in result
    assert result['business_name'] == sample_request.business_name
    assert isinstance(result['premium_estimate'], float)
    assert result['risk_profile'] == sample_risk_evaluation['risk_profile']
    assert isinstance(result['risk_factors'], list)
    assert 'report_path' in result
    assert result['report_path'].endswith('.pdf')
    assert isinstance(result['timestamp'], str)
    
    # Verify report file was created
    assert os.path.exists(result['report_path'])

def test_calculate_base_rate(agent, sample_request):
    """Test base rate calculation."""
    # Test different business types
    test_cases = [
        ("restaurant", 0.015),
        ("retail", 0.012),
        ("professional_services", 0.008),
        ("manufacturing", 0.020),
        ("construction", 0.025),
        ("unknown_type", 0.015)  # Default rate
    ]
    
    for business_type, expected_rate in test_cases:
        request = PolicyRequest(**{**sample_request.model_dump(), "business_type": business_type})
        base_rate = agent._calculate_base_rate(request)
        assert base_rate == expected_rate * (request.annual_revenue / 1000)

def test_calculate_adjustment_factor(agent, sample_request, sample_risk_evaluation):
    """Test adjustment factor calculation."""
    # Test different risk profiles
    test_cases = [
        ("low", 0.8),
        ("medium", 1.0),
        ("high", 1.5)
    ]
    
    for risk_profile, expected_factor in test_cases:
        analysis = {**sample_risk_evaluation, "risk_profile": risk_profile}
        factor = agent._calculate_adjustment_factor(sample_request, analysis)
        assert factor >= expected_factor  # Factor can be higher due to additional adjustments

def test_generate_report(agent, sample_request, sample_risk_evaluation):
    """Test PDF report generation."""
    # Test report generation
    report_path = agent._generate_report(sample_request, sample_risk_evaluation, 7500.00)
    
    # Verify report file
    assert os.path.exists(report_path)
    assert report_path.endswith('.pdf')
    
    # Clean up
    os.remove(report_path)
    assert not os.path.exists(report_path)

def test_error_handling(agent, sample_request):
    """Test error handling in various scenarios."""
    # Test invalid API key
    with pytest.raises(ValueError, match="ANTHROPIC_API_KEY not found"):
        UnderwritingAgent()
    
    # Test invalid JSON response
    mock_response = Mock()
    mock_response.content = [Mock(text="Invalid JSON")]
    agent.client.messages.create.return_value = mock_response
    
    with pytest.raises(ValueError, match="Failed to parse Claude's response"):
        agent.evaluate_risk(sample_request)
    
    # Test file system errors
    with patch('os.makedirs', side_effect=OSError("Permission denied")):
        with pytest.raises(OSError):
            agent._generate_report(sample_request, sample_risk_evaluation, 7500.00) 