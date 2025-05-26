"""
Package initialization file for Google Maps Business Scraper.
"""

from .main import GoogleMapsScraper
from .models.business import Business, PhoneNumber, Location, SearchParameters, SearchResult

__version__ = "1.0.0"
__author__ = "Manus AI"
