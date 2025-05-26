"""
Test script for validating the Google Maps Business Scraper.
"""

import os
import sys
import logging
import json
import csv
from pathlib import Path
import time
import random

# Add the parent directory to the path so we can import the package
sys.path.append(str(Path(__file__).resolve().parent.parent))

from src.main import GoogleMapsScraper
from src.models.business import SearchParameters, Location

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def validate_phone_numbers(results_file):
    """
    Validate phone numbers in the results file.
    
    Args:
        results_file: Path to the results file
        
    Returns:
        Tuple of (total_phones, valid_phones, validation_rate)
    """
    logger.info(f"Validating phone numbers in {results_file}")
    
    # Check file extension
    if results_file.endswith('.csv'):
        # Read CSV file
        with open(results_file, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        # Extract phone numbers
        phone_numbers = []
        for row in rows:
            if 'phone_number' in row and row['phone_number']:
                phone_numbers.append(row['phone_number'])
    
    elif results_file.endswith('.json'):
        # Read JSON file
        with open(results_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Extract phone numbers
        phone_numbers = []
        for business in data.get('businesses', []):
            for phone in business.get('phone_numbers', []):
                if isinstance(phone, dict) and 'number' in phone:
                    phone_numbers.append(phone['number'])
                elif isinstance(phone, str):
                    phone_numbers.append(phone)
    
    else:
        logger.error(f"Unsupported file format: {results_file}")
        return 0, 0, 0.0
    
    # Validate phone numbers
    valid_count = 0
    for phone in phone_numbers:
        # Check if it's a valid Sri Lankan number
        if (phone.startswith('+94') and len(phone) == 12) or (phone.startswith('0') and len(phone) == 10):
            # Check if it has a valid prefix
            if phone.startswith('+94'):
                prefix = phone[3:5]
            else:  # starts with 0
                prefix = phone[1:3]
            
            # Valid mobile prefixes
            mobile_prefixes = ['70', '71', '72', '74', '75', '76', '77', '78']
            
            # Valid landline prefixes (simplified)
            landline_prefixes = [
                '11', '33', '34', '81', '66', '52', '91', '41', '47',
                '21', '23', '24', '65', '63', '26', '37', '32', '25',
                '27', '55', '45', '35'
            ]
            
            if prefix in mobile_prefixes or prefix in landline_prefixes:
                valid_count += 1
    
    # Calculate validation rate
    total = len(phone_numbers)
    validation_rate = valid_count / total if total > 0 else 0.0
    
    logger.info(f"Total phone numbers: {total}")
    logger.info(f"Valid phone numbers: {valid_count}")
    logger.info(f"Validation rate: {validation_rate:.2%}")
    
    return total, valid_count, validation_rate

def test_major_cities():
    """Test scraping for major cities in Sri Lanka."""
    logger.info("Testing major cities in Sri Lanka")
    
    # Initialize scraper
    scraper = GoogleMapsScraper()
    
    # Major cities to test
    cities = [
        "Colombo",
        "Kandy",
        "Galle",
        "Jaffna",
        "Batticaloa"
    ]
    
    # Business types to search for
    business_types = [
        "restaurant",
        "hotel",
        "bank",
        "hospital",
        "pharmacy"
    ]
    
    results = []
    
    # Test each city with a random business type
    for city in cities:
        business_type = random.choice(business_types)
        query = f"{business_type} in {city}"
        
        logger.info(f"Testing: {query}")
        
        try:
            # Perform search with limited results for testing
            search_results = scraper.search(
                query=query,
                location=city,
                radius_km=2.0,
                max_results=10
            )
            
            # Save results
            output_path = scraper.save_results(
                search_results,
                output_format="csv"
            )
            
            # Validate phone numbers
            total, valid, rate = validate_phone_numbers(output_path)
            
            results.append({
                "city": city,
                "query": query,
                "total_results": len(search_results.businesses),
                "total_phones": total,
                "valid_phones": valid,
                "validation_rate": rate
            })
            
            logger.info(f"Found {len(search_results.businesses)} businesses in {city}")
            
        except Exception as e:
            logger.error(f"Error testing {city}: {e}")
            results.append({
                "city": city,
                "query": query,
                "error": str(e)
            })
        
        # Add delay between tests
        time.sleep(random.uniform(5.0, 10.0))
    
    # Calculate overall statistics
    total_businesses = sum(r.get("total_results", 0) for r in results if "total_results" in r)
    total_phones = sum(r.get("total_phones", 0) for r in results if "total_phones" in r)
    valid_phones = sum(r.get("valid_phones", 0) for r in results if "valid_phones" in r)
    overall_rate = valid_phones / total_phones if total_phones > 0 else 0.0
    
    logger.info("=== Overall Results ===")
    logger.info(f"Total cities tested: {len(cities)}")
    logger.info(f"Total businesses found: {total_businesses}")
    logger.info(f"Total phone numbers: {total_phones}")
    logger.info(f"Valid phone numbers: {valid_phones}")
    logger.info(f"Overall validation rate: {overall_rate:.2%}")
    
    # Save overall results
    output_dir = Path(scraper.config['output']['output_dir'])
    output_dir.mkdir(parents=True, exist_ok=True)
    
    results_file = output_dir / "validation_results.json"
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump({
            "cities_tested": len(cities),
            "total_businesses": total_businesses,
            "total_phones": total_phones,
            "valid_phones": valid_phones,
            "overall_validation_rate": overall_rate,
            "detailed_results": results
        }, f, indent=2)
    
    logger.info(f"Validation results saved to {results_file}")
    
    return results_file

def test_radius_parameters():
    """Test scraping with various radius parameters."""
    logger.info("Testing various radius parameters")
    
    # Initialize scraper
    scraper = GoogleMapsScraper()
    
    # Test location (Colombo)
    location = "Colombo"
    
    # Radius values to test (in km)
    radius_values = [1.0, 3.0, 5.0, 10.0]
    
    # Business type to search for
    business_type = "restaurant"
    
    results = []
    
    # Test each radius
    for radius in radius_values:
        query = f"{business_type} in {location}"
        
        logger.info(f"Testing radius {radius}km for {query}")
        
        try:
            # Perform search with limited results for testing
            search_results = scraper.search(
                query=query,
                location=location,
                radius_km=radius,
                max_results=20
            )
            
            # Save results
            output_path = scraper.save_results(
                search_results,
                output_format="csv"
            )
            
            # Validate phone numbers
            total, valid, rate = validate_phone_numbers(output_path)
            
            results.append({
                "radius_km": radius,
                "query": query,
                "total_results": len(search_results.businesses),
                "total_phones": total,
                "valid_phones": valid,
                "validation_rate": rate
            })
            
            logger.info(f"Found {len(search_results.businesses)} businesses with radius {radius}km")
            
        except Exception as e:
            logger.error(f"Error testing radius {radius}km: {e}")
            results.append({
                "radius_km": radius,
                "query": query,
                "error": str(e)
            })
        
        # Add delay between tests
        time.sleep(random.uniform(5.0, 10.0))
    
    # Save results
    output_dir = Path(scraper.config['output']['output_dir'])
    output_dir.mkdir(parents=True, exist_ok=True)
    
    results_file = output_dir / "radius_test_results.json"
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump({
            "location": location,
            "business_type": business_type,
            "radius_values_tested": radius_values,
            "detailed_results": results
        }, f, indent=2)
    
    logger.info(f"Radius test results saved to {results_file}")
    
    return results_file

def main():
    """Run validation tests."""
    logger.info("Starting validation tests")
    
    # Test major cities
    city_results_file = test_major_cities()
    
    # Test radius parameters
    radius_results_file = test_radius_parameters()
    
    logger.info("Validation tests completed")
    logger.info(f"City test results: {city_results_file}")
    logger.info(f"Radius test results: {radius_results_file}")

if __name__ == "__main__":
    main()
