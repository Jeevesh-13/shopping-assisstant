from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, JSON
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()


class MobilePhoneDB(Base):
    __tablename__ = "mobile_phones"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # Basic Info
    name = Column(String(200), nullable=False, index=True)
    brand = Column(String(50), nullable=False, index=True)
    price = Column(Float, nullable=False, index=True)
    price_range = Column(String(20), nullable=False, index=True)
    
    # Display
    display_size = Column(Float, nullable=False)
    display_type = Column(String(50), nullable=False)
    refresh_rate = Column(Integer, nullable=False)
    resolution = Column(String(50), nullable=False)
    
    # Performance
    processor = Column(String(100), nullable=False)
    ram = Column(Integer, nullable=False, index=True)
    storage = Column(Integer, nullable=False, index=True)
    
    # Camera
    rear_camera = Column(String(100), nullable=False)
    front_camera = Column(String(50), nullable=False)
    has_ois = Column(Boolean, default=False, index=True)
    has_eis = Column(Boolean, default=False)
    
    # Battery
    battery_capacity = Column(Integer, nullable=False, index=True)
    fast_charging = Column(Integer, nullable=True)
    wireless_charging = Column(Boolean, default=False, index=True)
    
    # Features
    os = Column(String(50), nullable=False)
    five_g = Column(Boolean, default=False, index=True)
    nfc = Column(Boolean, default=False, index=True)
    ip_rating = Column(String(10), nullable=True)
    
    # Dimensions
    weight = Column(Integer, nullable=False)
    thickness = Column(Float, nullable=False)
    
    # Additional Info (stored as JSON)
    highlights = Column(JSON, nullable=False, default=list)
    pros = Column(JSON, nullable=False, default=list)
    cons = Column(JSON, nullable=False, default=list)
    
    # Metadata
    launch_date = Column(DateTime, nullable=True)
    availability = Column(Boolean, default=True, index=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<MobilePhone(id={self.id}, name='{self.name}', brand='{self.brand}', price={self.price})>"
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "brand": self.brand,
            "price": self.price,
            "price_range": self.price_range,
            "display_size": self.display_size,
            "display_type": self.display_type,
            "refresh_rate": self.refresh_rate,
            "resolution": self.resolution,
            "processor": self.processor,
            "ram": self.ram,
            "storage": self.storage,
            "rear_camera": self.rear_camera,
            "front_camera": self.front_camera,
            "has_ois": self.has_ois,
            "has_eis": self.has_eis,
            "battery_capacity": self.battery_capacity,
            "fast_charging": self.fast_charging,
            "wireless_charging": self.wireless_charging,
            "os": self.os,
            "five_g": self.five_g,
            "nfc": self.nfc,
            "ip_rating": self.ip_rating,
            "weight": self.weight,
            "thickness": self.thickness,
            "highlights": self.highlights,
            "pros": self.pros,
            "cons": self.cons,
            "launch_date": self.launch_date,
            "availability": self.availability,
        }


class SearchHistoryDB(Base):
    """Search history for analytics."""
    
    __tablename__ = "search_history"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), nullable=False, index=True)
    query = Column(Text, nullable=False)
    intent = Column(String(50), nullable=False)
    filters_applied = Column(JSON, nullable=True)
    results_count = Column(Integer, nullable=False)
    response_time_ms = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<SearchHistory(id={self.id}, query='{self.query[:50]}...', intent='{self.intent}')>"


class ProductViewDB(Base):
    """Product view tracking for analytics."""
    
    __tablename__ = "product_views"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), nullable=False, index=True)
    product_id = Column(Integer, nullable=False, index=True)
    product_name = Column(String(200), nullable=False)
    brand = Column(String(50), nullable=False)
    viewed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<ProductView(product_id={self.product_id}, product_name='{self.product_name}')>"


class ComparisonHistoryDB(Base):
    """Comparison history for analytics."""
    
    __tablename__ = "comparison_history"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), nullable=False, index=True)
    product_ids = Column(JSON, nullable=False)  # List of product IDs
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<ComparisonHistory(id={self.id}, products={self.product_ids})>"


class SafetyLogDB(Base):
    """Safety incidents log."""
    
    __tablename__ = "safety_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), nullable=True, index=True)
    query = Column(Text, nullable=False)
    incident_type = Column(String(50), nullable=False, index=True)  # prompt_injection, key_extraction, etc.
    blocked = Column(Boolean, default=True, nullable=False)
    severity = Column(String(20), nullable=False)  # low, medium, high, critical
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<SafetyLog(id={self.id}, type='{self.incident_type}', blocked={self.blocked})>"
