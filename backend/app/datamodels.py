from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator
from enum import Enum


class PriceRange(str, Enum):
    """Price range categories."""
    BUDGET = "budget"  # < 15000
    MID_RANGE = "mid_range"  # 15000-30000
    PREMIUM = "premium"  # 30000-60000
    FLAGSHIP = "flagship"  # > 60000


class Brand(str, Enum):
    """Mobile phone brands."""
    SAMSUNG = "Samsung"
    APPLE = "Apple"
    XIAOMI = "Xiaomi"
    ONEPLUS = "OnePlus"
    GOOGLE = "Google"
    OPPO = "Oppo"
    VIVO = "Vivo"
    REALME = "Realme"
    MOTOROLA = "Motorola"
    NOKIA = "Nokia"
    IQOO = "iQOO"
    NOTHING = "Nothing"
    POCO = "Poco"


class MobilePhone(BaseModel):
    """Mobile phone model."""
    id: int
    name: str
    brand: Brand
    price: float
    price_range: PriceRange
    
    # Display
    display_size: float  # inches
    display_type: str  # AMOLED, LCD, etc.
    refresh_rate: int  # Hz
    resolution: str
    
    # Performance
    processor: str
    ram: int  # GB
    storage: int  # GB
    
    # Camera
    rear_camera: str
    front_camera: str
    has_ois: bool = False
    has_eis: bool = False
    
    # Battery
    battery_capacity: int  # mAh
    fast_charging: Optional[int] = None  # Watts
    wireless_charging: bool = False
    
    # Features
    os: str
    five_g: bool = False
    nfc: bool = False
    ip_rating: Optional[str] = None
    
    # Dimensions
    weight: int  # grams
    thickness: float  # mm
    
    # Additional
    highlights: List[str] = []
    pros: List[str] = []
    cons: List[str] = []
    
    # Metadata
    launch_date: Optional[datetime] = None
    availability: bool = True
    
    class Config:
        use_enum_values = True


class QueryIntent(str, Enum):
    """User query intent classification."""
    SEARCH = "search"
    COMPARE = "compare"
    DETAILS = "details"
    EXPLAIN = "explain"
    RECOMMENDATION = "recommendation"
    ADVERSARIAL = "adversarial"
    IRRELEVANT = "irrelevant"


class SearchFilters(BaseModel):
    """Search filters extracted from user query."""
    brands: Optional[List[Brand]] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    price_range: Optional[PriceRange] = None
    
    min_ram: Optional[int] = None
    min_storage: Optional[int] = None
    min_battery: Optional[int] = None
    
    five_g: Optional[bool] = None
    nfc: Optional[bool] = None
    wireless_charging: Optional[bool] = None
    
    camera_focus: Optional[bool] = None  # User wants good camera
    battery_focus: Optional[bool] = None  # User wants good battery
    performance_focus: Optional[bool] = None  # User wants good performance
    compact_size: Optional[bool] = None  # User wants compact phone
    
    keywords: List[str] = []
    
    class Config:
        use_enum_values = True


class ChatMessage(BaseModel):
    """Chat message model."""
    role: str  # user, assistant, system
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = None


class ChatRequest(BaseModel):
    """Chat request from user."""
    message: str = Field(..., min_length=1, max_length=500)
    session_id: Optional[str] = None
    conversation_history: List[ChatMessage] = []
    
    @validator("message")
    def validate_message(cls, v):
        """Validate message content."""
        if not v.strip():
            raise ValueError("Message cannot be empty")
        return v.strip()


class ProductCard(BaseModel):
    """Product card for UI display."""
    id: int
    name: str
    brand: str
    price: float
    image_url: Optional[str] = None
    
    key_specs: Dict[str, str]
    highlights: List[str]
    rating: Optional[float] = None
    
    match_score: Optional[float] = None  # Relevance score


class ComparisonTable(BaseModel):
    """Comparison table for multiple products."""
    products: List[MobilePhone]
    comparison_points: List[str]
    winner_categories: Dict[str, int]  # category -> product_id
    summary: str


class ChatResponse(BaseModel):
    """Chat response to user."""
    message: str
    intent: QueryIntent
    
    # Results
    products: List[ProductCard] = []
    comparison: Optional[ComparisonTable] = None
    
    # Metadata
    confidence: float = Field(ge=0.0, le=1.0)
    sources: List[str] = []
    suggestions: List[str] = []
    
    # Safety
    is_safe: bool = True
    safety_message: Optional[str] = None
    
    # Session
    session_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class HealthStatus(BaseModel):
    """Health check status."""
    status: str  # healthy, degraded, unhealthy
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    components: Dict[str, Dict[str, Any]] = {
        "database": {"status": "unknown"},
        "cache": {"status": "unknown"},
        "llm_primary": {"status": "unknown"},
        "llm_fallback": {"status": "unknown"},
    }
    
    metrics: Dict[str, Any] = {}


class MetricData(BaseModel):
    """Metric data point."""
    name: str
    value: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    labels: Dict[str, str] = {}


class AnomalyAlert(BaseModel):
    """Anomaly detection alert."""
    metric_name: str
    current_value: float
    expected_range: tuple[float, float]
    severity: str  # low, medium, high, critical
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    message: str
