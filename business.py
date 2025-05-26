"""
Models for the Google Maps Business Scraper.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime


@dataclass
class Location:
    """Represents a geographical location."""
    latitude: float
    longitude: float
    address: Optional[str] = None
    city: Optional[str] = None
    district: Optional[str] = None
    country: str = "Sri Lanka"
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "address": self.address,
            "city": self.city,
            "district": self.district,
            "country": self.country
        }


@dataclass
class PhoneNumber:
    """Represents a Sri Lankan phone number with validation."""
    number: str
    is_mobile: Optional[bool] = None
    is_validated: bool = False
    region: Optional[str] = None
    
    def __post_init__(self):
        """Normalize the phone number format."""
        # Remove spaces, dashes, etc.
        self.number = ''.join(filter(lambda x: x.isdigit() or x == '+', self.number))
        
        # Convert local format to international if needed
        if self.number.startswith('0'):
            self.number = '+94' + self.number[1:]
        elif not self.number.startswith('+'):
            # Assume it's a local number without the leading 0
            self.number = '+94' + self.number
    
    def to_local_format(self) -> str:
        """Convert to local Sri Lankan format (0XX XXX XXXX)."""
        if self.number.startswith('+94'):
            return '0' + self.number[3:]
        return self.number
    
    def to_international_format(self) -> str:
        """Ensure number is in international format (+94 XX XXX XXXX)."""
        return self.number
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "number": self.number,
            "local_format": self.to_local_format(),
            "international_format": self.to_international_format(),
            "is_mobile": self.is_mobile,
            "is_validated": self.is_validated,
            "region": self.region
        }


@dataclass
class Business:
    """Represents a business entity extracted from Google Maps."""
    name: str
    phone_numbers: List[PhoneNumber] = field(default_factory=list)
    location: Optional[Location] = None
    website: Optional[str] = None
    category: Optional[str] = None
    rating: Optional[float] = None
    reviews_count: Optional[int] = None
    place_id: Optional[str] = None
    hours: Optional[Dict[str, str]] = None
    extracted_at: datetime = field(default_factory=datetime.now)
    
    def add_phone_number(self, number: str) -> None:
        """Add a phone number to the business."""
        phone = PhoneNumber(number=number)
        self.phone_numbers.append(phone)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "phone_numbers": [p.to_dict() for p in self.phone_numbers],
            "location": self.location.to_dict() if self.location else None,
            "website": self.website,
            "category": self.category,
            "rating": self.rating,
            "reviews_count": self.reviews_count,
            "place_id": self.place_id,
            "hours": self.hours,
            "extracted_at": self.extracted_at.isoformat()
        }


@dataclass
class SearchParameters:
    """Parameters for a Google Maps search."""
    query: str
    location: Optional[Location] = None
    radius_km: float = 5.0
    language: str = "en"
    max_results: int = 120
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "query": self.query,
            "location": self.location.to_dict() if self.location else None,
            "radius_km": self.radius_km,
            "language": self.language,
            "max_results": self.max_results
        }


@dataclass
class SearchResult:
    """Results of a Google Maps search."""
    parameters: SearchParameters
    businesses: List[Business] = field(default_factory=list)
    total_found: int = 0
    success: bool = True
    error_message: Optional[str] = None
    search_time: float = 0.0  # seconds
    
    def add_business(self, business: Business) -> None:
        """Add a business to the results."""
        self.businesses.append(business)
        self.total_found = len(self.businesses)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "parameters": self.parameters.to_dict(),
            "businesses": [b.to_dict() for b in self.businesses],
            "total_found": self.total_found,
            "success": self.success,
            "error_message": self.error_message,
            "search_time": self.search_time
        }
