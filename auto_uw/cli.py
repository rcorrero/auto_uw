"""
Command-line interface for the Auto UW package.
"""

import json
import os
from typing import Dict, Any
from pathlib import Path
import click
from dotenv import load_dotenv
from .agent import UnderwritingAgent
from .models import PolicyRequest, Claim

# Load environment variables
load_dotenv()

def validate_api_key() -> None:
    """Validate that the Anthropic API key is set."""
    if not os.getenv('ANTHROPIC_API_KEY'):
        raise click.ClickException(
            "ANTHROPIC_API_KEY environment variable not set. "
            "Please set it before running the command."
        )

def load_json_file(file_path: str) -> Dict[str, Any]:
    """Load and validate a JSON file."""
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        return data
    except json.JSONDecodeError as e:
        raise click.ClickException(f"Invalid JSON file: {e}")
    except FileNotFoundError:
        raise click.ClickException(f"File not found: {file_path}")

def save_json_file(data: Dict[str, Any], file_path: str) -> None:
    """Save data to a JSON file."""
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        raise click.ClickException(f"Failed to save output file: {e}")

@click.group()
def cli():
    """Auto UW - Automated Insurance Underwriting System."""
    pass

@cli.command()
@click.option('--business-name', required=True, help='Name of the business')
@click.option('--business-type', required=True, help='Type of business (e.g., restaurant, retail)')
@click.option('--annual-revenue', required=True, type=float, help='Annual revenue in USD')
@click.option('--employee-count', required=True, type=int, help='Number of employees')
@click.option('--state', required=True, help='State where the business operates')
@click.option('--city', required=True, help='City where the business operates')
@click.option('--years-in-business', required=True, type=int, help='Years in business')
@click.option('--business-description', required=True, help='Detailed description of business operations')
@click.option('--claims', help='JSON file containing claims history')
@click.option('--output', '-o', help='Output file path for the quote')
def quote(business_name: str, business_type: str, annual_revenue: float,
          employee_count: int, state: str, city: str, years_in_business: int,
          business_description: str, claims: str, output: str) -> None:
    """Generate an insurance quote for a business."""
    try:
        # Validate API key
        validate_api_key()
        
        # Load claims history if provided
        claims_history = []
        if claims:
            claims_data = load_json_file(claims)
            if not isinstance(claims_data, list):
                raise click.ClickException("Claims file must contain a list of claims")
            claims_history = [Claim(**claim) for claim in claims_data]
        
        # Create policy request
        request = PolicyRequest(
            business_name=business_name,
            business_type=business_type,
            annual_revenue=annual_revenue,
            employee_count=employee_count,
            state=state,
            city=city,
            years_in_business=years_in_business,
            business_description=business_description,
            claims_history=claims_history
        )
        
        # Initialize agent and process request
        agent = UnderwritingAgent()
        result = agent.process_request(request)
        
        # Save or display result
        if output:
            save_json_file(result, output)
            click.echo(f"Quote saved to {output}")
        else:
            click.echo(json.dumps(result, indent=2))
            
    except Exception as e:
        raise click.ClickException(str(e))

@cli.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.option('--output-dir', '-o', help='Output directory for quotes')
def batch_quote(input_file: str, output_dir: str) -> None:
    """Process multiple policy requests from a JSON file."""
    try:
        # Validate API key
        validate_api_key()
        
        # Load input file
        data = load_json_file(input_file)
        if not isinstance(data, list):
            raise click.ClickException("Input file must contain a list of policy requests")
        
        # Create output directory if specified
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        
        # Initialize agent
        agent = UnderwritingAgent()
        
        # Process each request
        for i, request_data in enumerate(data, 1):
            try:
                # Create policy request
                request = PolicyRequest(**request_data)
                
                # Process request
                result = agent.process_request(request)
                
                # Save result
                if output_dir:
                    output_file = os.path.join(
                        output_dir,
                        f"quote_{request.business_name.lower().replace(' ', '_')}_{i}.json"
                    )
                    save_json_file(result, output_file)
                    click.echo(f"Quote {i} saved to {output_file}")
                else:
                    click.echo(f"\nQuote {i} for {request.business_name}:")
                    click.echo(json.dumps(result, indent=2))
                    
            except Exception as e:
                click.echo(f"Error processing request {i}: {str(e)}", err=True)
                continue
                
    except Exception as e:
        raise click.ClickException(str(e))

@cli.command()
@click.argument('business_type')
def guidelines(business_type: str) -> None:
    """Display underwriting guidelines for a specific business type."""
    try:
        # Initialize agent
        agent = UnderwritingAgent()
        
        # Get guidelines
        guidelines = agent.get_business_type_guidelines(business_type)
        
        # Display guidelines
        if guidelines:
            click.echo(f"\nUnderwriting Guidelines for {business_type.title()} Businesses:")
            click.echo("=" * 50)
            for guideline in guidelines:
                click.echo(f"\n{guideline.title}")
                click.echo("-" * 30)
                click.echo(guideline.content)
                if guideline.metadata:
                    click.echo("\nMetadata:")
                    for key, value in guideline.metadata.items():
                        click.echo(f"  {key}: {value}")
        else:
            click.echo(f"No guidelines found for {business_type}")
            
    except Exception as e:
        raise click.ClickException(str(e))

if __name__ == '__main__':
    cli() 