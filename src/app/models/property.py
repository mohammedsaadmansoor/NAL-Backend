from pydantic import BaseModel, Field, HttpUrl, validator
from pydantic.types import condecimal
from typing import Optional, List, Dict, Any
from datetime import datetime, date, time
from enum import Enum
import uuid
import re

# ======================================================
# ENUM CLASSES
# ======================================================

class PropertyType(str, Enum):
    APARTMENT = "apartment"
    VILLA = "villa"
    HOUSE = "house"
    COMMERCIAL = "commercial"
    PG_COLIVING = "pg-coliving"


class ListingType(str, Enum):
    SELL = "sell"
    RENT = "rent"
    URGENT_SALE = "urgent-sale"
    BIDDING = "bidding"


class Facing(str, Enum):
    NORTH = "north"
    SOUTH = "south"
    EAST = "east"
    WEST = "west"
    NORTH_EAST = "north-east"
    NORTH_WEST = "north-west"
    SOUTH_EAST = "south-east"
    SOUTH_WEST = "south-west"


class Furnishing(str, Enum):
    FULLY_FURNISHED = "fully-furnished"
    SEMI_FURNISHED = "semi-furnished"
    UNFURNISHED = "unfurnished"


class PropertyStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SOLD = "sold"
    RENTED = "rented"
    UNDER_REVIEW = "under_review"


class DocumentType(str, Enum):
    OWNERSHIP = "property_ownership"
    APPROVALS = "building_approvals"
    TAX_RECEIPTS = "tax_receipts"
    NOC = "noc_certificates"
    FLOOR_PLANS = "floor_plans"
    OTHER = "other"


class DocumentStatus(str, Enum):
    UPLOADED = "uploaded"
    PENDING_REVIEW = "pending_review"
    VERIFIED = "verified"
    REJECTED = "rejected"


# ======================================================
# PROPERTY CREATE MODEL
# ======================================================

class PropertyCreate(BaseModel):
    """Request model for creating a property listing."""
    # Basic info
    title: str = Field(..., max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    listing_type: ListingType = Field(..., description="Type of listing (sell/rent/bidding)")
    property_type: PropertyType = Field(..., description="Type of property")
    status: PropertyStatus = Field(PropertyStatus.ACTIVE)

    # Location
    address: str = Field(..., description="Full address of property")
    city: str = Field(..., max_length=100)
    locality: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field("Karnataka", max_length=100)
    pincode: Optional[str] = Field(None, max_length=10)
    landmark: Optional[str] = Field(None, max_length=200)
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    # Property Details
    built_up_area: Optional[int] = None
    carpet_area: Optional[int] = None
    plot_area: Optional[int] = None
    super_area: Optional[int] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[int] = None
    balconies: Optional[int] = None
    floor_number: Optional[str] = None
    total_floors: Optional[str] = None
    facing: Optional[Facing] = None
    furnishing: Optional[Furnishing] = Furnishing.UNFURNISHED
    property_age: Optional[str] = None

    # Pricing
    sale_price: Optional[condecimal(max_digits=12, decimal_places=2)] = None
    monthly_rent: Optional[condecimal(max_digits=10, decimal_places=2)] = None
    security_deposit: Optional[condecimal(max_digits=10, decimal_places=2)] = None
    price_negotiable: bool = False
    loan_available: bool = False
    possession_status: Optional[str] = None

    # Bidding / Auction
    starting_bid_price: Optional[condecimal(max_digits=12, decimal_places=2)] = None
    reserve_price: Optional[condecimal(max_digits=12, decimal_places=2)] = None
    minimum_increment: Optional[condecimal(max_digits=10, decimal_places=2)] = None
    bidding_enabled: bool = False
    auction_start_date: Optional[date] = None
    auction_start_time: Optional[time] = None
    auction_end_date: Optional[date] = None
    auction_end_time: Optional[time] = None
    auction_timezone: Optional[str] = None
    starting_bid_amount: Optional[condecimal(max_digits=12, decimal_places=2)] = None
    bid_increment_amount: Optional[condecimal(max_digits=10, decimal_places=2)] = None
    bidder_registration_fee: Optional[condecimal(max_digits=10, decimal_places=2)] = None
    auction_eligibility: Optional[str] = None

    # Features & Amenities
    amenities: List[str] = Field(default_factory=list)
    custom_amenities: List[str] = Field(default_factory=list)
    property_highlights: List[str] = Field(default_factory=list)
    nearby_places: List[str] = Field(default_factory=list)

    # Media
    primary_image: Optional[HttpUrl] = None
    virtual_tour_url: Optional[HttpUrl] = None
    image_urls: List[HttpUrl] = Field(default_factory=list)

    # Analytics
    views: int = 0
    inquiries: int = 0

    # Ownership
    listed_by_id: str = Field(..., description="User ID of the agent/seller who listed the property")

    @validator('pincode')
    def validate_pincode(cls, v):
        if v and not re.match(r'^\d{5,6}$', v):
            raise ValueError("Invalid pincode format")
        return v

    @validator('latitude')
    def validate_latitude(cls, v):
        if v is not None and not (-90 <= v <= 90):
            raise ValueError("Latitude must be between -90 and 90")
        return v

    @validator('longitude')
    def validate_longitude(cls, v):
        if v is not None and not (-180 <= v <= 180):
            raise ValueError("Longitude must be between -180 and 180")
        return v

    @validator('bedrooms', 'bathrooms', 'balconies')
    def validate_positive_numbers(cls, v):
        if v is not None and v < 0:
            raise ValueError("Value must be positive")
        return v

    @validator('floor_number', 'total_floors')
    def validate_floor_numbers(cls, v):
        if v is not None:
            # Allow positive integers or special string values
            if v.isdigit() and int(v) > 0:
                return v
            elif v.lower() in ['ground', 'basement', 'mezzanine', 'penthouse']:
                return v
            else:
                raise ValueError("Floor must be a positive integer or valid floor name (Ground, Basement, Mezzanine, Penthouse)")
        return v

    @validator('auction_end_date')
    def validate_auction_dates(cls, v, values):
        if v and values.get('auction_start_date'):
            if v <= values['auction_start_date']:
                raise ValueError("Auction end date must be after start date")
        return v

    @validator('sale_price', 'monthly_rent')
    def validate_pricing_by_listing_type(cls, v, values, field):
        listing_type = values.get('listing_type')
        if listing_type == ListingType.SELL and field.name == 'sale_price' and not v:
            raise ValueError("Sale price is required for sell listings")
        if listing_type == ListingType.RENT and field.name == 'monthly_rent' and not v:
            raise ValueError("Monthly rent is required for rent listings")
        return v


# ======================================================
# UPDATE MODEL
# ======================================================

class PropertyUpdate(BaseModel):
    """Request model for updating property details."""
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[PropertyStatus] = None
    sale_price: Optional[condecimal(max_digits=12, decimal_places=2)] = None
    monthly_rent: Optional[condecimal(max_digits=10, decimal_places=2)] = None
    security_deposit: Optional[condecimal(max_digits=10, decimal_places=2)] = None
    price_negotiable: Optional[bool] = None
    loan_available: Optional[bool] = None
    furnishing: Optional[Furnishing] = None
    amenities: Optional[List[str]] = None
    image_urls: Optional[List[HttpUrl]] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# ======================================================
# RESPONSE MODEL
# ======================================================

class PropertyResponse(BaseModel):
    """Response model for property data."""
    id: int
    title: str
    description: Optional[str]
    listing_type: ListingType
    property_type: PropertyType
    status: PropertyStatus
    price_negotiable: bool
    city: str
    state: str
    locality: Optional[str]
    address: str
    sale_price: Optional[float]
    monthly_rent: Optional[float]
    furnishing: Optional[Furnishing]
    bedrooms: Optional[int]
    bathrooms: Optional[int]
    amenities: List[str]
    primary_image: Optional[str]
    views: int
    inquiries: int
    listed_by_id: str
    created_at: datetime
    updated_at: datetime


# ======================================================
# PAGINATED LIST MODEL
# ======================================================

class PropertyListResponse(BaseModel):
    """Paginated list of properties."""
    properties: List[PropertyResponse]
    total_count: int
    page: int
    limit: int


# ======================================================
# MEDIA / DOCUMENT MODELS
# ======================================================

class PropertyImageResponse(BaseModel):
    id: uuid.UUID
    property_id: int
    image_url: HttpUrl
    category: str
    is_primary: bool
    alt_text: Optional[str]
    order: int
    created_at: datetime


class PropertyVideoResponse(BaseModel):
    id: uuid.UUID
    property_id: int
    video_url: HttpUrl
    thumbnail_url: Optional[HttpUrl]
    title: Optional[str]
    duration: Optional[int]
    order: int
    created_at: datetime


class PropertyDocumentResponse(BaseModel):
    id: uuid.UUID
    property_id: int
    document_type: DocumentType
    custom_name: Optional[str]
    file_url: HttpUrl
    file_size: Optional[int]
    status: DocumentStatus
    uploaded_at: datetime
    verified_at: Optional[datetime]
    verified_by_id: Optional[str]
