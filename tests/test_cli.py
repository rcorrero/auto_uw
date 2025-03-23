"""Tests for the CLI interface."""

import os
import json
import pytest
from unittest.mock import patch, Mock
from click.testing import CliRunner
from auto_uw.cli import cli
from auto_uw.models import PolicyRequest, Claim

@pytest.fixture
def runner():
    """Create a CLI runner."""
    return CliRunner()

@pytest.fixture
def sample_request_data():
    """Create sample request data."""
    return {
        "business_name": "Test Restaurant",
        "business_type": "restaurant",
        "annual_revenue": 500000,
        "employee_count": 15,
        "state": "CA",
        "city": "San Francisco",
        "years_in_business": 5,
        "business_description": "Family-owned restaurant",
        "claims_history": [
            {
                "date": "2023-01-15",
                "type": "property",
                "amount": 5000
            }
        ]
    }

@pytest.fixture
def sample_quote_response():
    """Create a sample quote response."""
    return {
        "quote_id": "550e8400-e29b-41d4-a716-446655440000",
        "business_name": "Test Restaurant",
        "premium_estimate": 7500.00,
        "risk_profile": "medium",
        "risk_factors": [
            "Recent property claim",
            "High-traffic location",
            "Limited years in business"
        ],
        "report_path": "reports/quote_20240322_225604.pdf",
        "timestamp": "2024-03-22T22:56:04.123456"
    }

def test_quote_command(runner, sample_request_data, sample_quote_response):
    """Test the quote command."""
    with patch('auto_uw.cli.UnderwritingAgent') as mock_agent:
        # Configure mock
        mock_instance = Mock()
        mock_instance.process_policy_request.return_value = sample_quote_response
        mock_agent.return_value = mock_instance
        
        # Run command
        result = runner.invoke(cli, [
            'quote',
            '--business-name', sample_request_data['business_name'],
            '--business-type', sample_request_data['business_type'],
            '--revenue', str(sample_request_data['annual_revenue']),
            '--employees', str(sample_request_data['employee_count']),
            '--state', sample_request_data['state'],
            '--city', sample_request_data['city'],
            '--years', str(sample_request_data['years_in_business']),
            '--description', sample_request_data['business_description'],
            '--claims', json.dumps(sample_request_data['claims_history']),
            '--output', 'quote.json'
        ])
        
        # Verify command execution
        assert result.exit_code == 0
        assert "Quote generated successfully" in result.output
        
        # Verify output file
        assert os.path.exists('quote.json')
        with open('quote.json', 'r') as f:
            output_data = json.load(f)
            assert output_data == sample_quote_response
        
        # Clean up
        os.remove('quote.json')
        assert not os.path.exists('quote.json')

def test_batch_quote_command(runner, sample_request_data, sample_quote_response):
    """Test the batch-quote command."""
    # Create input file
    input_data = [sample_request_data]
    with open('quotes.json', 'w') as f:
        json.dump(input_data, f)
    
    with patch('auto_uw.cli.UnderwritingAgent') as mock_agent:
        # Configure mock
        mock_instance = Mock()
        mock_instance.process_policy_request.return_value = sample_quote_response
        mock_agent.return_value = mock_instance
        
        # Run command
        result = runner.invoke(cli, [
            'batch-quote',
            '--input', 'quotes.json',
            '--output', 'results.json'
        ])
        
        # Verify command execution
        assert result.exit_code == 0
        assert "Batch processing completed" in result.output
        
        # Verify output file
        assert os.path.exists('results.json')
        with open('results.json', 'r') as f:
            output_data = json.load(f)
            assert len(output_data) == 1
            assert output_data[0] == sample_quote_response
        
        # Clean up
        os.remove('quotes.json')
        os.remove('results.json')
        assert not os.path.exists('quotes.json')
        assert not os.path.exists('results.json')

def test_missing_required_fields(runner):
    """Test handling of missing required fields."""
    # Run command with missing fields
    result = runner.invoke(cli, [
        'quote',
        '--business-name', 'Test Restaurant',
        '--output', 'quote.json'
    ])
    
    # Verify error handling
    assert result.exit_code != 0
    assert "Missing required fields" in result.output

def test_invalid_json(runner):
    """Test handling of invalid JSON input."""
    # Run command with invalid JSON
    result = runner.invoke(cli, [
        'quote',
        '--business-name', 'Test Restaurant',
        '--business-type', 'restaurant',
        '--revenue', '500000',
        '--employees', '15',
        '--state', 'CA',
        '--city', 'San Francisco',
        '--years', '5',
        '--description', 'Test description',
        '--claims', 'invalid json',
        '--output', 'quote.json'
    ])
    
    # Verify error handling
    assert result.exit_code != 0
    assert "Invalid JSON format" in result.output

def test_file_permission_errors(runner, sample_request_data):
    """Test handling of file permission errors."""
    with patch('auto_uw.cli.UnderwritingAgent') as mock_agent:
        # Configure mock
        mock_instance = Mock()
        mock_instance.process_policy_request.return_value = {
            "quote_id": "test-id",
            "report_path": "reports/test.pdf"
        }
        mock_agent.return_value = mock_instance
        
        # Mock file operations to raise permission errors
        with patch('builtins.open', side_effect=PermissionError):
            result = runner.invoke(cli, [
                'quote',
                '--business-name', sample_request_data['business_name'],
                '--business-type', sample_request_data['business_type'],
                '--revenue', str(sample_request_data['annual_revenue']),
                '--employees', str(sample_request_data['employee_count']),
                '--state', sample_request_data['state'],
                '--city', sample_request_data['city'],
                '--years', str(sample_request_data['years_in_business']),
                '--description', sample_request_data['business_description'],
                '--claims', json.dumps(sample_request_data['claims_history']),
                '--output', 'quote.json'
            ])
            
            # Verify error handling
            assert result.exit_code != 0
            assert "Permission denied" in result.output

def test_api_key_validation(runner):
    """Test API key validation."""
    # Remove API key from environment
    with patch.dict(os.environ, {}, clear=True):
        result = runner.invoke(cli, ['quote', '--help'])
        
        # Verify error handling
        assert result.exit_code != 0
        assert "ANTHROPIC_API_KEY not found" in result.output 