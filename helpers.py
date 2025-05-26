"""
Utility functions for the Google Maps Business Scraper.
"""

import re
import logging
import random
import time
from typing import Dict, List, Optional, Tuple, Union
from pathlib import Path
import json
import csv
from datetime import datetime

from ..models.business import Business, PhoneNumber, Location, SearchResult

# Configure logger
logger = logging.getLogger(__name__)

# Sri Lankan phone number patterns
SL_MOBILE_PATTERN = r'(?:\+94|0)7[0-2,4-8]\d{7}'
SL_LANDLINE_PATTERN = r'(?:\+94|0)(?:[1-9][0-9])\d{6}'
SL_GENERAL_PATTERN = r'(?:\+94|0)\d{9}'

def extract_phone_numbers(text: str) -> List[str]:
    """
    Extract Sri Lankan phone numbers from text.
    
    Args:
        text: Text containing potential phone numbers
        
    Returns:
        List of extracted phone numbers
    """
    # Combined pattern for both mobile and landline
    pattern = f"({SL_MOBILE_PATTERN}|{SL_LANDLINE_PATTERN}|{SL_GENERAL_PATTERN})"
    
    # Find all matches
    matches = re.findall(pattern, text)
    
    # Clean and normalize
    cleaned_numbers = []
    for match in matches:
        # Remove spaces, dashes, etc.
        number = ''.join(filter(lambda x: x.isdigit() or x == '+', match))
        
        # Convert local format to international if needed
        if number.startswith('0'):
            number = '+94' + number[1:]
        elif not number.startswith('+'):
            # Assume it's a local number without the leading 0
            number = '+94' + number
            
        cleaned_numbers.append(number)
    
    return cleaned_numbers

def validate_sri_lankan_phone(phone: str) -> Tuple[bool, Dict]:
    """
    Validate if a phone number is a valid Sri Lankan number.
    
    Args:
        phone: Phone number to validate
        
    Returns:
        Tuple of (is_valid, metadata)
    """
    # Normalize the number
    number = ''.join(filter(lambda x: x.isdigit() or x == '+', phone))
    
    # Convert to international format if needed
    if number.startswith('0'):
        number = '+94' + number[1:]
    elif not number.startswith('+'):
        number = '+94' + number
    
    # Check if it's a valid Sri Lankan number
    if not (number.startswith('+94') and len(number) == 12):
        return False, {"error": "Invalid length or country code"}
    
    # Extract the prefix (after +94)
    prefix = number[3:5]
    
    # Check if it's a mobile number
    mobile_prefixes = ['70', '71', '72', '74', '75', '76', '77', '78']
    is_mobile = prefix in mobile_prefixes
    
    # Check if it's a landline and identify region
    landline_regions = {
        '11': 'Colombo',
        '33': 'Gampaha',
        '34': 'Kalutara',
        '81': 'Kandy',
        '66': 'Matale',
        '52': 'Nuwara Eliya',
        '91': 'Galle',
        '41': 'Matara',
        '47': 'Hambantota',
        '21': 'Jaffna/Kilinochchi',
        '23': 'Mannar',
        '24': 'Vavuniya/Mullaitivu',
        '65': 'Batticaloa',
        '63': 'Ampara',
        '26': 'Trincomalee',
        '37': 'Kurunegala',
        '32': 'Puttalam',
        '25': 'Anuradhapura',
        '27': 'Polonnaruwa',
        '55': 'Badulla/Monaragala',
        '45': 'Ratnapura',
        '35': 'Kegalle'
    }
    
    region = landline_regions.get(prefix, None)
    
    return True, {
        "is_mobile": is_mobile,
        "region": region,
        "normalized": number,
        "local_format": '0' + number[3:]
    }

def random_delay(min_seconds: float = 1.0, max_seconds: float = 3.0) -> None:
    """
    Introduce a random delay to simulate human behavior.
    
    Args:
        min_seconds: Minimum delay in seconds
        max_seconds: Maximum delay in seconds
    """
    delay = random.uniform(min_seconds, max_seconds)
    logger.debug(f"Sleeping for {delay:.2f} seconds")
    time.sleep(delay)

def get_random_user_agent() -> str:
    """
    Get a random user agent string.
    
    Returns:
        Random user agent string
    """
    user_agents = [
        # Chrome on Windows
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        # Chrome on macOS
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        # Chrome on Linux
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        # Firefox on Windows
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0",
        # Firefox on macOS
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/115.0",
        # Safari on macOS
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Safari/605.1.15",
        # Edge on Windows
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
        # Mobile Chrome on Android
        "Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
        # Mobile Safari on iOS
        "Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/604.1"
    ]
    return random.choice(user_agents)

def save_results(results: SearchResult, output_format: str = 'csv', output_dir: str = './output') -> str:
    """
    Save search results to a file.
    
    Args:
        results: Search results to save
        output_format: Format to save as (csv, json, excel)
        output_dir: Directory to save to
        
    Returns:
        Path to the saved file
    """
    # Create output directory if it doesn't exist
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Generate filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    location_name = "unknown"
    if results.parameters.location and results.parameters.location.city:
        location_name = results.parameters.location.city
    elif results.parameters.query:
        location_name = results.parameters.query.replace(' ', '_')
    
    if output_format.lower() == 'json':
        filename = f"{location_name}_{timestamp}.json"
        file_path = output_path / filename
        
        # Convert to dictionary and save as JSON
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(results.to_dict(), f, ensure_ascii=False, indent=2)
            
    elif output_format.lower() == 'csv':
        filename = f"{location_name}_{timestamp}.csv"
        file_path = output_path / filename
        
        # Flatten the data structure for CSV
        rows = []
        for business in results.businesses:
            for phone in business.phone_numbers:
                row = {
                    'business_name': business.name,
                    'phone_number': phone.to_international_format(),
                    'phone_local': phone.to_local_format(),
                    'is_mobile': phone.is_mobile,
                    'phone_region': phone.region,
                    'category': business.category,
                    'rating': business.rating,
                    'reviews_count': business.reviews_count,
                    'website': business.website,
                }
                
                # Add location data if available
                if business.location:
                    row.update({
                        'latitude': business.location.latitude,
                        'longitude': business.location.longitude,
                        'address': business.location.address,
                        'city': business.location.city,
                        'district': business.location.district,
                    })
                
                rows.append(row)
        
        # Write to CSV
        if rows:
            with open(file_path, 'w', encoding='utf-8-sig', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)
        else:
            with open(file_path, 'w', encoding='utf-8-sig', newline='') as f:
                f.write("No results found")
    
    else:
        raise ValueError(f"Unsupported output format: {output_format}")
    
    logger.info(f"Results saved to {file_path}")
    return str(file_path)

def subdivide_area(center_lat: float, center_lng: float, radius_km: float, 
                  max_radius_km: float = 5.0) -> List[Tuple[float, float, float]]:
    """
    Subdivide a large area into smaller circles for more comprehensive coverage.
    
    Args:
        center_lat: Center latitude
        center_lng: Center longitude
        radius_km: Original radius in kilometers
        max_radius_km: Maximum radius for subdivisions
        
    Returns:
        List of (lat, lng, radius) tuples for each subdivision
    """
    if radius_km <= max_radius_km:
        return [(center_lat, center_lng, radius_km)]
    
    # Calculate how many subdivisions we need
    # Each subdivision will be max_radius_km in size
    # We'll create a grid of points to cover the original circle
    
    # Earth's radius in km
    earth_radius = 6371.0
    
    # Convert radius to degrees (approximate)
    radius_deg = radius_km / (earth_radius * math.pi / 180.0)
    max_radius_deg = max_radius_km / (earth_radius * math.pi / 180.0)
    
    # Calculate grid size
    grid_size = math.ceil(radius_deg / max_radius_deg) * 2
    
    # Generate grid points
    subdivisions = []
    for i in range(-grid_size//2, grid_size//2 + 1):
        for j in range(-grid_size//2, grid_size//2 + 1):
            # Calculate point coordinates
            lat = center_lat + i * max_radius_deg
            lng = center_lng + j * max_radius_deg
            
            # Check if point is within original circle
            distance = math.sqrt((lat - center_lat)**2 + (lng - center_lng)**2)
            if distance <= radius_deg:
                subdivisions.append((lat, lng, max_radius_km))
    
    return subdivisions

def is_within_sri_lanka(lat: float, lng: float) -> bool:
    """
    Check if coordinates are within Sri Lanka's boundaries.
    
    Args:
        lat: Latitude
        lng: Longitude
        
    Returns:
        True if within Sri Lanka, False otherwise
    """
    # Approximate bounding box for Sri Lanka
    bounds = {
        "north": 9.9,
        "south": 5.9,
        "east": 82.0,
        "west": 79.5
    }
    
    return (bounds["south"] <= lat <= bounds["north"] and 
            bounds["west"] <= lng <= bounds["east"])

def get_district_from_coordinates(lat: float, lng: float) -> Optional[str]:
    """
    Get the Sri Lankan district name from coordinates.
    
    This is a simplified implementation. In a production system,
    this would use GeoJSON data or a geocoding service.
    
    Args:
        lat: Latitude
        lng: Longitude
        
    Returns:
        District name or None if not found
    """
    # This is a simplified approximation
    # In a real implementation, this would use proper GeoJSON boundaries
    
    # Colombo district approximate bounds
    if 6.7 <= lat <= 7.0 and 79.8 <= lng <= 80.0:
        return "Colombo"
    
    # Kandy district approximate bounds
    if 7.1 <= lat <= 7.5 and 80.5 <= lng <= 80.8:
        return "Kandy"
    
    # Galle district approximate bounds
    if 5.9 <= lat <= 6.2 and 80.1 <= lng <= 80.3:
        return "Galle"
    
    # For a complete implementation, all 25 districts would be defined
    
    return None
