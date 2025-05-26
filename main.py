"""
Main module for the Google Maps Business Scraper.
"""

import argparse
import logging
import sys
import os
from pathlib import Path
from typing import Dict, List, Optional, Union
import json

from .models.business import Business, PhoneNumber, Location, SearchParameters, SearchResult
from .browser.playwright_scraper import PlaywrightScraper
from .utils.helpers import save_results, subdivide_area, is_within_sri_lanka
from .config.settings import get_config, load_user_config

# Configure logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class GoogleMapsScraper:
    """
    Main class for the Google Maps Business Scraper.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the scraper.
        
        Args:
            config_path: Path to configuration file
        """
        # Load configuration
        if config_path:
            load_user_config(config_path)
        self.config = get_config()
        
        # Set up logging
        self._setup_logging()
        
        logger.info("Google Maps Business Scraper initialized")
    
    def _setup_logging(self):
        """Set up logging based on configuration."""
        log_level = getattr(logging, self.config['logging']['level'])
        log_dir = self.config['logging']['log_dir']
        
        # Create log directory if it doesn't exist
        if self.config['logging']['log_to_file']:
            os.makedirs(log_dir, exist_ok=True)
            
            # Add file handler
            log_file = os.path.join(log_dir, 'scraper.log')
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(log_level)
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            ))
            
            # Add handler to root logger
            logging.getLogger().addHandler(file_handler)
        
        # Set level for root logger
        logging.getLogger().setLevel(log_level)
    
    def search(self, query: str, location: Optional[Union[str, Dict]] = None, 
              radius_km: float = None, max_results: int = None) -> SearchResult:
        """
        Search for businesses on Google Maps.
        
        Args:
            query: Search query
            location: Location to search in (name, coordinates, or Location object)
            radius_km: Search radius in kilometers
            max_results: Maximum number of results to return
            
        Returns:
            Search results
        """
        # Use default radius if not specified
        if radius_km is None:
            radius_km = self.config['location']['default_radius']
        
        # Use default max results if not specified
        if max_results is None:
            max_results = self.config['extraction']['max_results_per_query']
        
        # Process location
        location_obj = self._process_location(location)
        
        # Create search parameters
        params = SearchParameters(
            query=query,
            location=location_obj,
            radius_km=radius_km,
            max_results=max_results
        )
        
        # Check if we need to subdivide the area
        if radius_km > self.config['location']['subdivision_threshold']:
            logger.info(f"Radius {radius_km}km exceeds threshold, subdividing area")
            return self._search_subdivided_area(params)
        
        # Perform search
        logger.info(f"Searching for '{query}' in {location_obj.city if location_obj else 'specified location'} "
                   f"with radius {radius_km}km")
        
        # Use Playwright scraper
        with PlaywrightScraper(
            headless=self.config['browser']['headless'],
            stealth_mode=self.config['browser']['stealth_mode']
        ) as scraper:
            result = scraper.search_businesses(params)
        
        return result
    
    def _process_location(self, location) -> Optional[Location]:
        """
        Process location input into a Location object.
        
        Args:
            location: Location input (string, dict, or Location object)
            
        Returns:
            Location object or None
        """
        if location is None:
            return None
        
        if isinstance(location, Location):
            return location
        
        if isinstance(location, dict):
            # Extract coordinates from dictionary
            lat = location.get('lat') or location.get('latitude')
            lng = location.get('lng') or location.get('longitude')
            
            if lat is not None and lng is not None:
                return Location(
                    latitude=float(lat),
                    longitude=float(lng),
                    city=location.get('city'),
                    district=location.get('district')
                )
        
        if isinstance(location, str):
            # Check if it's a major city in Sri Lanka
            for city in self.config['location']['major_cities']:
                if city['name'].lower() == location.lower():
                    return Location(
                        latitude=city['lat'],
                        longitude=city['lng'],
                        city=city['name']
                    )
            
            # Check if it's a district in Sri Lanka
            for district in self.config['location']['districts']:
                if district.lower() == location.lower():
                    # Use approximate district center (this would be more precise in production)
                    # For now, just use a placeholder
                    return Location(
                        latitude=7.5,  # Placeholder
                        longitude=80.7,  # Placeholder
                        district=district
                    )
            
            # Assume it's a search query for a location
            # In a production system, this would use geocoding
            logger.warning(f"Location '{location}' not recognized as a known city or district. "
                          "Using as search query.")
            return None
        
        logger.warning(f"Unrecognized location format: {location}")
        return None
    
    def _search_subdivided_area(self, params: SearchParameters) -> SearchResult:
        """
        Search a large area by subdividing it into smaller areas.
        
        Args:
            params: Search parameters
            
        Returns:
            Combined search results
        """
        # Create a result object to hold all findings
        combined_result = SearchResult(parameters=params)
        
        # Get center coordinates
        if params.location:
            center_lat = params.location.latitude
            center_lng = params.location.longitude
        else:
            # Default to center of Sri Lanka if no location specified
            center_lat = 7.5
            center_lng = 80.7
        
        # Subdivide the area
        subdivisions = subdivide_area(
            center_lat, center_lng, params.radius_km,
            max_radius_km=self.config['location']['subdivision_threshold']
        )
        
        logger.info(f"Subdivided area into {len(subdivisions)} smaller areas")
        
        # Search each subdivision
        for i, (lat, lng, radius) in enumerate(subdivisions):
            logger.info(f"Searching subdivision {i+1}/{len(subdivisions)}")
            
            # Create location object for this subdivision
            sub_location = Location(
                latitude=lat,
                longitude=lng,
                city=params.location.city if params.location else None,
                district=params.location.district if params.location else None
            )
            
            # Create search parameters for this subdivision
            sub_params = SearchParameters(
                query=params.query,
                location=sub_location,
                radius_km=radius,
                max_results=params.max_results
            )
            
            # Perform search for this subdivision
            with PlaywrightScraper(
                headless=self.config['browser']['headless'],
                stealth_mode=self.config['browser']['stealth_mode']
            ) as scraper:
                sub_result = scraper.search_businesses(sub_params)
            
            # Add businesses to combined result
            for business in sub_result.businesses:
                # Check for duplicates before adding
                if not any(b.name == business.name for b in combined_result.businesses):
                    combined_result.add_business(business)
            
            logger.info(f"Found {len(sub_result.businesses)} businesses in subdivision {i+1}, "
                       f"total unique businesses so far: {len(combined_result.businesses)}")
            
            # If we've reached the maximum results, stop
            if len(combined_result.businesses) >= params.max_results:
                logger.info(f"Reached maximum results ({params.max_results}), stopping subdivision search")
                break
        
        return combined_result
    
    def save_results(self, results: SearchResult, output_format: str = None, 
                    output_dir: str = None) -> str:
        """
        Save search results to a file.
        
        Args:
            results: Search results to save
            output_format: Format to save as (csv, json, excel)
            output_dir: Directory to save to
            
        Returns:
            Path to the saved file
        """
        # Use default format if not specified
        if output_format is None:
            output_format = self.config['output']['format']
        
        # Use default output directory if not specified
        if output_dir is None:
            output_dir = self.config['output']['output_dir']
        
        return save_results(results, output_format, output_dir)

def main():
    """Command line interface for the scraper."""
    parser = argparse.ArgumentParser(description='Google Maps Business Scraper for Sri Lanka')
    parser.add_argument('query', help='Search query')
    parser.add_argument('--location', help='Location to search in (city, district, or coordinates)')
    parser.add_argument('--radius', type=float, help='Search radius in kilometers')
    parser.add_argument('--max-results', type=int, help='Maximum number of results to return')
    parser.add_argument('--output-format', choices=['csv', 'json'], help='Output format')
    parser.add_argument('--output-dir', help='Output directory')
    parser.add_argument('--config', help='Path to configuration file')
    parser.add_argument('--headless', action='store_true', help='Run in headless mode')
    
    args = parser.parse_args()
    
    # Initialize scraper
    scraper = GoogleMapsScraper(config_path=args.config)
    
    # Override headless mode if specified
    if args.headless is not None:
        scraper.config['browser']['headless'] = args.headless
    
    # Perform search
    results = scraper.search(
        query=args.query,
        location=args.location,
        radius_km=args.radius,
        max_results=args.max_results
    )
    
    # Save results
    output_path = scraper.save_results(
        results,
        output_format=args.output_format,
        output_dir=args.output_dir
    )
    
    print(f"Found {len(results.businesses)} businesses")
    print(f"Results saved to {output_path}")

if __name__ == '__main__':
    main()
