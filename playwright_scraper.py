"""
Browser automation module for Google Maps scraping using Playwright.
"""

import logging
import time
import random
import re
from typing import Dict, List, Optional, Tuple, Union
from pathlib import Path

from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext
import json

from ..models.business import Business, PhoneNumber, Location, SearchParameters, SearchResult
from ..utils.helpers import (
    extract_phone_numbers, validate_sri_lankan_phone, random_delay, 
    get_random_user_agent, is_within_sri_lanka, get_district_from_coordinates
)
from ..config.settings import get_config

# Configure logger
logger = logging.getLogger(__name__)

class PlaywrightScraper:
    """
    Google Maps scraper using Playwright for browser automation.
    Implements anti-detection measures and robust error handling.
    """
    
    def __init__(self, headless: bool = True, stealth_mode: bool = True):
        """
        Initialize the scraper.
        
        Args:
            headless: Whether to run the browser in headless mode
            stealth_mode: Whether to use stealth mode to avoid detection
        """
        self.config = get_config()
        self.headless = headless
        self.stealth_mode = stealth_mode
        self.browser = None
        self.context = None
        self.page = None
        
    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()
        
    def start(self):
        """Start the browser."""
        logger.info("Starting Playwright browser")
        
        playwright = sync_playwright().start()
        
        # Configure browser options
        browser_type = playwright.chromium
        browser_args = []
        
        if self.stealth_mode:
            # Add stealth mode arguments to avoid detection
            browser_args.extend([
                '--disable-blink-features=AutomationControlled',
                '--disable-features=IsolateOrigins,site-per-process',
                '--disable-site-isolation-trials',
                '--disable-web-security',
            ])
        
        # Launch browser
        self.browser = browser_type.launch(
            headless=self.headless,
            args=browser_args
        )
        
        # Create a new context with a random viewport size
        viewport_width = random.randint(1280, 1920)
        viewport_height = random.randint(800, 1080)
        
        self.context = self.browser.new_context(
            viewport={'width': viewport_width, 'height': viewport_height},
            user_agent=get_random_user_agent(),
            locale='en-US',
            timezone_id='Asia/Colombo',  # Sri Lanka timezone
        )
        
        # Apply stealth mode scripts if enabled
        if self.stealth_mode:
            self._apply_stealth_scripts()
        
        # Create a new page
        self.page = self.context.new_page()
        
        # Set default timeout
        self.page.set_default_timeout(30000)  # 30 seconds
        
        return self
    
    def stop(self):
        """Stop the browser."""
        if self.browser:
            logger.info("Stopping Playwright browser")
            self.browser.close()
            self.browser = None
            self.context = None
            self.page = None
    
    def _apply_stealth_scripts(self):
        """Apply scripts to avoid detection."""
        # Mask WebDriver
        self.context.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {
            get: () => false,
        });
        """)
        
        # Mask automation
        self.context.add_init_script("""
        window.navigator.chrome = {
            runtime: {},
        };
        """)
        
        # Modify plugins
        self.context.add_init_script("""
        Object.defineProperty(navigator, 'plugins', {
            get: () => [
                {
                    0: {type: 'application/x-google-chrome-pdf', suffixes: 'pdf', description: 'Portable Document Format'},
                    name: 'Chrome PDF Plugin',
                    filename: 'internal-pdf-viewer',
                    description: 'Portable Document Format',
                },
                {
                    0: {type: 'application/pdf', suffixes: 'pdf', description: 'Portable Document Format'},
                    name: 'Chrome PDF Viewer',
                    filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai',
                    description: 'Portable Document Format',
                },
                {
                    0: {type: 'application/x-shockwave-flash', suffixes: 'swf', description: 'Shockwave Flash'},
                    name: 'Shockwave Flash',
                    filename: 'internal-flash-player',
                    description: 'Shockwave Flash',
                },
            ],
        });
        """)
        
        # Modify languages
        self.context.add_init_script("""
        Object.defineProperty(navigator, 'languages', {
            get: () => ['en-US', 'en', 'si', 'ta'],
        });
        """)
    
    def search_businesses(self, params: SearchParameters) -> SearchResult:
        """
        Search for businesses on Google Maps.
        
        Args:
            params: Search parameters
            
        Returns:
            Search results
        """
        if not self.browser:
            self.start()
        
        start_time = time.time()
        result = SearchResult(parameters=params)
        
        try:
            # Navigate to Google Maps
            logger.info(f"Searching for businesses with query: {params.query}")
            self.page.goto('https://www.google.com/maps', wait_until='networkidle')
            random_delay(1.0, 2.0)
            
            # Accept cookies if prompted
            try:
                if self.page.query_selector('button:has-text("Accept all")'):
                    self.page.click('button:has-text("Accept all")')
                    random_delay(1.0, 2.0)
            except Exception as e:
                logger.debug(f"No cookie prompt or error handling it: {e}")
            
            # Enter search query
            search_box = self.page.query_selector('input[name="q"]')
            if not search_box:
                raise Exception("Could not find search box")
            
            # Clear search box and type query with random delays
            search_box.click()
            search_box.fill('')
            self._type_with_random_delays(search_box, params.query)
            random_delay(0.5, 1.0)
            
            # Press Enter to search
            search_box.press('Enter')
            
            # Wait for results to load
            self.page.wait_for_load_state('networkidle')
            random_delay(2.0, 3.0)
            
            # Check if we need to click on "Businesses" section
            try:
                businesses_section = self.page.query_selector('button:has-text("Businesses")')
                if businesses_section:
                    businesses_section.click()
                    self.page.wait_for_load_state('networkidle')
                    random_delay(1.0, 2.0)
            except Exception as e:
                logger.debug(f"No businesses section or error clicking it: {e}")
            
            # Extract businesses
            businesses = self._extract_businesses(params.max_results)
            
            # Add businesses to result
            for business in businesses:
                result.add_business(business)
            
            logger.info(f"Found {len(businesses)} businesses")
            
        except Exception as e:
            logger.error(f"Error searching for businesses: {e}", exc_info=True)
            result.success = False
            result.error_message = str(e)
        
        # Calculate search time
        result.search_time = time.time() - start_time
        
        return result
    
    def _type_with_random_delays(self, element, text: str):
        """
        Type text with random delays between keystrokes to simulate human typing.
        
        Args:
            element: Page element to type into
            text: Text to type
        """
        for char in text:
            element.type(char, delay=random.uniform(50, 150))
    
    def _extract_businesses(self, max_results: int = 120) -> List[Business]:
        """
        Extract businesses from search results.
        
        Args:
            max_results: Maximum number of results to extract
            
        Returns:
            List of businesses
        """
        businesses = []
        
        # Scroll through results to load more
        scrolls_needed = min(20, max_results // 5)  # Estimate scrolls needed
        
        for _ in range(scrolls_needed):
            # Find the results container
            results_container = self.page.query_selector('div[role="feed"]')
            if not results_container:
                break
            
            # Get current results
            result_items = self.page.query_selector_all('div[role="feed"] > div')
            
            # Extract visible businesses
            visible_count = len(businesses)
            self._extract_visible_businesses(result_items, businesses)
            
            # If we've reached max results or no new results were found, stop scrolling
            if len(businesses) >= max_results or len(businesses) == visible_count:
                break
            
            # Scroll down
            self.page.evaluate('document.querySelector(\'div[role="feed"]\').scrollTop += 500')
            random_delay(1.0, 2.0)
        
        # Limit to max_results
        return businesses[:max_results]
    
    def _extract_visible_businesses(self, result_items, businesses: List[Business]):
        """
        Extract data from visible business result items.
        
        Args:
            result_items: List of result item elements
            businesses: List to append extracted businesses to
        """
        for item in result_items:
            try:
                # Check if this is a business result (has a title)
                title_elem = item.query_selector('h3, .fontHeadlineSmall')
                if not title_elem:
                    continue
                
                # Extract business name
                business_name = title_elem.inner_text().strip()
                
                # Create business object
                business = Business(name=business_name)
                
                # Click on the result to view details
                title_elem.click()
                random_delay(1.5, 2.5)
                
                # Wait for details panel to load
                self.page.wait_for_selector('button[data-item-id="phone"]', state='visible', timeout=5000)
                
                # Extract business details
                self._extract_business_details(business)
                
                # Add to list if it has a phone number
                if business.phone_numbers:
                    businesses.append(business)
                
                # Go back to results
                back_button = self.page.query_selector('button[jsaction="pane.back"]')
                if back_button:
                    back_button.click()
                    random_delay(1.0, 2.0)
                
            except Exception as e:
                logger.debug(f"Error extracting business: {e}")
                # Continue with next result
                continue
    
    def _extract_business_details(self, business: Business):
        """
        Extract details for a business from its details panel.
        
        Args:
            business: Business object to update with details
        """
        try:
            # Extract category
            category_elem = self.page.query_selector('.fontBodyMedium span:first-child')
            if category_elem:
                business.category = category_elem.inner_text().strip()
            
            # Extract rating
            rating_elem = self.page.query_selector('span.fontDisplayLarge')
            if rating_elem:
                try:
                    rating_text = rating_elem.inner_text().strip()
                    business.rating = float(rating_text)
                except ValueError:
                    pass
            
            # Extract reviews count
            reviews_elem = self.page.query_selector('span.fontBodyMedium a')
            if reviews_elem:
                reviews_text = reviews_elem.inner_text().strip()
                reviews_match = re.search(r'(\d+(?:,\d+)*)', reviews_text)
                if reviews_match:
                    business.reviews_count = int(reviews_match.group(1).replace(',', ''))
            
            # Extract phone number
            phone_button = self.page.query_selector('button[data-item-id="phone"]')
            if phone_button:
                phone_text = phone_button.inner_text().strip()
                phone_numbers = extract_phone_numbers(phone_text)
                
                for phone in phone_numbers:
                    # Validate and add phone number
                    is_valid, metadata = validate_sri_lankan_phone(phone)
                    if is_valid:
                        phone_obj = PhoneNumber(
                            number=metadata['normalized'],
                            is_mobile=metadata.get('is_mobile'),
                            is_validated=True,
                            region=metadata.get('region')
                        )
                        business.phone_numbers.append(phone_obj)
            
            # Extract website
            website_button = self.page.query_selector('a[data-item-id="authority"]')
            if website_button:
                business.website = website_button.get_attribute('href')
            
            # Extract address and location
            address_button = self.page.query_selector('button[data-item-id="address"]')
            if address_button:
                address_text = address_button.inner_text().strip()
                
                # Try to extract coordinates from the URL
                try:
                    url = self.page.url
                    coords_match = re.search(r'@(-?\d+\.\d+),(-?\d+\.\d+)', url)
                    if coords_match:
                        lat = float(coords_match.group(1))
                        lng = float(coords_match.group(2))
                        
                        # Create location object
                        location = Location(
                            latitude=lat,
                            longitude=lng,
                            address=address_text,
                            district=get_district_from_coordinates(lat, lng)
                        )
                        business.location = location
                except Exception as e:
                    logger.debug(f"Error extracting coordinates: {e}")
            
        except Exception as e:
            logger.debug(f"Error extracting business details: {e}")
