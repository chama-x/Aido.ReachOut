"""
Configuration settings for the Google Maps Business Scraper.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Union

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Default configuration
DEFAULT_CONFIG = {
    # API Settings
    "api": {
        "preferred_provider": "playwright",  # Options: "bright_data", "oxylabs", "smartproxy", "apify", "scraperapi", "playwright"
        "api_keys": {
            "bright_data": os.environ.get("BRIGHT_DATA_API_KEY", ""),
            "oxylabs": os.environ.get("OXYLABS_API_KEY", ""),
            "smartproxy": os.environ.get("SMARTPROXY_API_KEY", ""),
            "apify": os.environ.get("APIFY_API_KEY", ""),
            "scraperapi": os.environ.get("SCRAPERAPI_API_KEY", ""),
        },
        "timeout": 60,  # seconds
        "max_retries": 3,
    },
    
    # Proxy Settings
    "proxy": {
        "use_proxy": True,
        "proxy_type": "rotating",  # Options: "rotating", "residential", "datacenter", "none"
        "proxy_list_path": str(BASE_DIR / "config" / "proxies.txt"),
        "proxy_rotation_interval": 10,  # requests
        "proxy_countries": ["LK", "IN", "SG"],  # Sri Lanka, India, Singapore
    },
    
    # Browser Settings
    "browser": {
        "headless": True,
        "user_agent_rotation": True,
        "stealth_mode": True,
        "viewport_randomization": True,
        "language": "en-US,si-LK,ta-LK",  # English, Sinhala, Tamil
        "wait_time": {
            "min": 2,  # seconds
            "max": 5,  # seconds
        },
    },
    
    # Location Settings for Sri Lanka
    "location": {
        "default_radius": 5,  # km
        "max_radius": 50,  # km
        "urban_radius": 2,  # km for urban areas
        "rural_radius": 10,  # km for rural areas
        "subdivision_threshold": 20,  # km - subdivide areas larger than this
        "sri_lanka_bounds": {
            "north": 9.9,  # Northern point latitude
            "south": 5.9,  # Southern point latitude
            "east": 82.0,  # Eastern point longitude
            "west": 79.5,  # Western point longitude
        },
        "major_cities": [
            {"name": "Colombo", "lat": 6.9271, "lng": 79.8612},
            {"name": "Kandy", "lat": 7.2906, "lng": 80.6337},
            {"name": "Galle", "lat": 6.0535, "lng": 80.2210},
            {"name": "Jaffna", "lat": 9.6615, "lng": 80.0255},
            {"name": "Batticaloa", "lat": 7.7170, "lng": 81.7000},
        ],
        "districts": [
            "Ampara", "Anuradhapura", "Badulla", "Batticaloa", "Colombo",
            "Galle", "Gampaha", "Hambantota", "Jaffna", "Kalutara",
            "Kandy", "Kegalle", "Kilinochchi", "Kurunegala", "Mannar",
            "Matale", "Matara", "Monaragala", "Mullaitivu", "Nuwara Eliya",
            "Polonnaruwa", "Puttalam", "Ratnapura", "Trincomalee", "Vavuniya"
        ],
    },
    
    # Data Extraction Settings
    "extraction": {
        "target_fields": [
            "business_name", "phone_number", "address", "website", 
            "category", "rating", "reviews_count", "latitude", "longitude"
        ],
        "required_fields": ["business_name", "phone_number"],
        "max_results_per_query": 120,  # Google Maps typically limits to ~120 results
        "pagination_scroll_count": 20,  # Number of scrolls to attempt for pagination
    },
    
    # Phone Number Validation for Sri Lanka
    "phone_validation": {
        "country_code": "LK",
        "international_prefix": "+94",
        "local_prefix": "0",
        "mobile_prefixes": ["70", "71", "72", "74", "75", "76", "77", "78"],
        "landline_prefixes": {
            "Colombo": "11",
            "Gampaha": "33",
            "Kalutara": "34",
            "Kandy": "81",
            "Matale": "66",
            "Nuwara Eliya": "52",
            "Galle": "91",
            "Matara": "41",
            "Hambantota": "47",
            "Jaffna": "21",
            "Kilinochchi": "21",
            "Mannar": "23",
            "Vavuniya": "24",
            "Mullaitivu": "24",
            "Batticaloa": "65",
            "Ampara": "63",
            "Trincomalee": "26",
            "Kurunegala": "37",
            "Puttalam": "32",
            "Anuradhapura": "25",
            "Polonnaruwa": "27",
            "Badulla": "55",
            "Monaragala": "55",
            "Ratnapura": "45",
            "Kegalle": "35",
        },
        "phone_number_length": {
            "mobile": 10,  # Including leading 0
            "landline": 10,  # Including leading 0
        },
    },
    
    # Output Settings
    "output": {
        "format": "csv",  # Options: "csv", "json", "excel"
        "output_dir": str(BASE_DIR / "output"),
        "filename_template": "sri_lanka_businesses_{location}_{date}.{ext}",
        "encoding": "utf-8-sig",  # UTF-8 with BOM for Excel compatibility with Sinhala/Tamil
    },
    
    # Caching Settings
    "cache": {
        "enabled": True,
        "cache_dir": str(BASE_DIR / "cache"),
        "expiration": 86400,  # 24 hours in seconds
    },
    
    # Logging Settings
    "logging": {
        "level": "INFO",  # Options: "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"
        "log_dir": str(BASE_DIR / "logs"),
        "log_to_console": True,
        "log_to_file": True,
    },
    
    # Rate Limiting
    "rate_limiting": {
        "requests_per_minute": 10,
        "max_concurrent_requests": 2,
        "backoff_factor": 2,  # For exponential backoff
        "jitter": True,  # Add randomness to delays
    },
    
    # Error Handling
    "error_handling": {
        "retry_on_errors": [
            "ConnectionError", 
            "Timeout", 
            "ProxyError",
            "CaptchaDetected"
        ],
        "max_consecutive_errors": 5,
        "circuit_breaker_timeout": 300,  # seconds to wait after circuit breaks
    },
}

# User configuration will be loaded and merged with defaults
user_config = {}

def get_config() -> Dict:
    """
    Get the merged configuration (default + user overrides).
    
    Returns:
        Dict: The complete configuration dictionary
    """
    # Start with default config
    config = DEFAULT_CONFIG.copy()
    
    # Override with user config if available
    if user_config:
        # Deep merge would be implemented here
        pass
    
    return config

def load_user_config(config_path: Optional[str] = None) -> None:
    """
    Load user configuration from a file.
    
    Args:
        config_path: Path to the configuration file
    """
    global user_config
    
    if not config_path:
        config_path = str(BASE_DIR / "config" / "user_config.yaml")
    
    # Implementation would load and parse YAML config
    # For now, just a placeholder
    user_config = {}
