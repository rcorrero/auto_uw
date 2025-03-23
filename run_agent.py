"""
Script to run the underwriting agent.
"""

import os
from dotenv import load_dotenv
from auto_uw.agent import UnderwritingAgent, PolicyRequest

def main():
    # Load environment variables
    load_dotenv()
    
    # Get API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not found in environment variables")
    
    # Initialize the agent
    agent = UnderwritingAgent()
    
    # Example policy request
    example_request = PolicyRequest(
        business_name="Joe's Diner",
        business_type="restaurant",
        annual_revenue=750000.0,
        employee_count=25,
        state="CA",
        city="San Francisco",
        years_in_business=5,
        business_description="""
        Family-owned restaurant serving American cuisine. Located in a historic building.
        Features a full-service kitchen, dining area, and bar. Open for lunch and dinner.
        Has a liquor license and serves wine and beer.
        """,
        claims_history=[
            {"date": "2023-01-15", "type": "slip_and_fall", "amount": 5000.0},
            {"date": "2022-06-20", "type": "property_damage", "amount": 2500.0}
        ],
        additional_notes="Recently renovated kitchen with new fire suppression system."
    )
    
    # Process the request
    try:
        quote_response = agent.process_policy_request(example_request)
        print("\nQuote Response:")
        print("-" * 50)
        print(f"Business: {quote_response['business_name']}")
        print(f"Quote ID: {quote_response['quote_id']}")
        print(f"\nPremium Estimate: ${quote_response['premium_estimate']:,.2f}")
        print(f"Risk Profile: {quote_response['risk_profile']}")
        print("\nRisk Factors:")
        for factor in quote_response['risk_factors']:
            print(f"- {factor}")
        print(f"\nDetailed Report: {quote_response['report_path']}")
    except Exception as e:
        print(f"Error processing request: {e}")

if __name__ == "__main__":
    main() 