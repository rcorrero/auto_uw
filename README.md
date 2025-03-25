# Auto UW - Automated Insurance Underwriting System

Auto UW is an intelligent insurance underwriting system that leverages Claude AI to automate the process of evaluating business insurance applications and generating detailed quotes. The system provides risk assessment, premium calculations, and professional PDF reports.

## Features

- **Intelligent Risk Assessment**: Uses Claude AI to evaluate business risk profiles based on:
  - Business type and size
  - Revenue and employee count
  - Location and years in business
  - Claims history
  - Business description and additional notes

- **Automated Premium Calculation**:
  - Base rates by business type
  - Risk-based adjustment factors
  - Claims history impact
  - Years in business consideration

- **Professional PDF Reports**:
  - Detailed quote information
  - Color-coded risk profiles
  - Risk factors and recommendations
  - Claims history tables
  - Business description and notes

- **REST API Interface**:
  - FastAPI-based endpoints
  - JSON request/response format
  - Input validation with Pydantic

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/auto_uw.git
cd auto_uw
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file with your Anthropic API key:
```bash
ANTHROPIC_API_KEY=your_api_key_here
CLAUDE_MODEL=claude-3-sonnet-20240229  # Optional, defaults to latest model
```

## Usage

### Command Line Interface

Generate a single quote:
```bash
python -m auto_uw quote \
    --business-name "Joe's Diner" \
    --business-type restaurant \
    --revenue 500000 \
    --employees 15 \
    --state CA \
    --city San Francisco \
    --years 5 \
    --description "Family-owned restaurant serving American cuisine" \
    --claims '[{"date": "2023-01-15", "type": "property", "amount": 5000}]' \
    --output quote.json
```

Process multiple quotes from a JSON file:
```bash
python -m auto_uw batch-quote \
    --input quotes.json \
    --output results.json
```

### API Usage

Start the API server:
```bash
uvicorn auto_uw.agent:app --reload
```

Send a quote request:
```bash
curl -X POST "http://localhost:8000/quote" \
     -H "Content-Type: application/json" \
     -d '{
         "business_name": "Joe's Diner",
         "business_type": "restaurant",
         "annual_revenue": 500000,
         "employee_count": 15,
         "state": "CA",
         "city": "San Francisco",
         "years_in_business": 5,
         "business_description": "Family-owned restaurant serving American cuisine",
         "claims_history": [
             {"date": "2023-01-15", "type": "property", "amount": 5000}
         ]
     }'
```

### API Documentation

#### Endpoints

##### POST /quote
Generate an insurance quote for a business.

**Request Body:**
```json
{
    "business_name": "string",
    "business_type": "string",
    "annual_revenue": "number",
    "employee_count": "integer",
    "state": "string",
    "city": "string",
    "years_in_business": "integer",
    "business_description": "string",
    "claims_history": [
        {
            "date": "string (YYYY-MM-DD)",
            "type": "string",
            "amount": "number"
        }
    ],
    "additional_notes": "string (optional)"
}
```

**Response:**
```json
{
    "quote_id": "string (UUID)",
    "business_name": "string",
    "premium_estimate": "number",
    "risk_profile": "string (low/medium/high)",
    "risk_factors": ["string"],
    "report_path": "string",
    "timestamp": "string (ISO 8601)"
}
```

**Status Codes:**
- 200: Success
- 400: Invalid request data
- 422: Validation error
- 500: Server error

### Example Outputs

#### Quote Response
```json
{
    "quote_id": "550e8400-e29b-41d4-a716-446655440000",
    "business_name": "Joe's Diner",
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
```

#### PDF Report Contents
The generated PDF report includes:
1. Title page with business name and quote ID
2. Quote details table with business information
3. Risk assessment section with color-coded profile
4. List of risk factors and recommendations
5. Claims history table (if applicable)
6. Business description and additional notes

## Project Structure

```
auto_uw/
├── __init__.py
├── agent.py          # Main underwriting agent implementation
├── cli.py           # Command-line interface
├── document_store.py # Document management system
├── models.py        # Data models and validation
└── report_generator.py # PDF report generation
```

## Dependencies

- anthropic>=0.18.1
- python-dotenv>=1.0.0
- pydantic>=2.6.1
- fastapi>=0.109.2
- uvicorn>=0.27.1
- pandas>=2.2.0
- reportlab>=4.1.0

## Development

### Setup Development Environment
1. Install development dependencies:
```bash
pip install -r requirements-dev.txt
```

2. Install pre-commit hooks:
```bash
pre-commit install
```

### Running Tests
```bash
# Run all tests
pytest

# Run tests with coverage report
pytest --cov=auto_uw

# Run specific test file
pytest tests/test_agent.py

# Run tests with verbose output
pytest -v
```

### Code Style
The project follows PEP 8 guidelines. Format code using:
```bash
# Format all Python files
black .

# Sort imports
isort .
```

### Adding New Features
1. Create a new branch for your feature
2. Add tests for new functionality
3. Update documentation
4. Submit a pull request

## Troubleshooting

### Common Issues

1. **API Key Not Found**
   - Ensure `.env` file exists in project root
   - Verify `ANTHROPIC_API_KEY` is set correctly
   - Check file permissions

2. **PDF Generation Fails**
   - Verify `reports` directory exists and is writable
   - Check for sufficient disk space
   - Ensure all required fonts are installed

3. **Validation Errors**
   - Review request format matches API documentation
   - Check data types (especially numbers vs strings)
   - Verify required fields are present

4. **Performance Issues**
   - Monitor API rate limits
   - Check network connectivity
   - Review large batch processing

## License

This project is licensed under the MIT License - see the LICENSE file for details. 