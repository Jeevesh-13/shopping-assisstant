from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
import time

from app.datamodels import MobilePhone, SearchFilters, Brand, PriceRange
from app.database.db import get_db_context
from app.database.models import MobilePhoneDB, SearchHistoryDB, ProductViewDB
from app.observability.logging import get_logger

logger = get_logger(__name__)


class SearchService:
    """Product search and filtering service using database."""
    
    def __init__(self):
        pass
    
    def search(
        self,
        filters: SearchFilters,
        limit: int = 10,
        session_id: Optional[str] = None
    ) -> List[MobilePhone]:
        """
        Search phones based on filters using database queries.
        """
        start_time = time.time()
        
        with get_db_context() as db:
            # Start with base query
            query = db.query(MobilePhoneDB).filter(MobilePhoneDB.availability == True)
            
            # Apply brand filter
            if filters.brands:
                query = query.filter(MobilePhoneDB.brand.in_(filters.brands))
            
            # Apply price filters
            if filters.min_price is not None:
                query = query.filter(MobilePhoneDB.price >= filters.min_price)
            
            if filters.max_price is not None:
                query = query.filter(MobilePhoneDB.price <= filters.max_price)
            
            if filters.price_range:
                query = query.filter(MobilePhoneDB.price_range == filters.price_range)
            
            # Apply spec filters
            if filters.min_ram:
                query = query.filter(MobilePhoneDB.ram >= filters.min_ram)
            
            if filters.min_storage:
                query = query.filter(MobilePhoneDB.storage >= filters.min_storage)
            
            if filters.min_battery:
                query = query.filter(MobilePhoneDB.battery_capacity >= filters.min_battery)
            
            # Apply feature filters
            if filters.five_g is not None:
                query = query.filter(MobilePhoneDB.five_g == filters.five_g)
            
            if filters.nfc is not None:
                query = query.filter(MobilePhoneDB.nfc == filters.nfc)
            
            if filters.wireless_charging is not None:
                query = query.filter(MobilePhoneDB.wireless_charging == filters.wireless_charging)
            
            # Apply focus-based sorting
            if filters.camera_focus:
                query = query.order_by(MobilePhoneDB.has_ois.desc(), MobilePhoneDB.has_eis.desc())
            elif filters.battery_focus:
                query = query.order_by(MobilePhoneDB.battery_capacity.desc())
            elif filters.performance_focus:
                query = query.order_by(MobilePhoneDB.ram.desc())
            elif filters.compact_size:
                query = query.order_by(MobilePhoneDB.weight.asc(), MobilePhoneDB.display_size.asc())
            else:
                # Default sorting by price
                query = query.order_by(MobilePhoneDB.price.asc())
            
            # Execute query with limit
            results_db = query.limit(limit).all()
            
            # Convert to Pydantic models
            results = [self._db_to_pydantic(phone) for phone in results_db]
            
            # Keyword filtering (post-query for flexibility)
            if filters.keywords:
                results = self._filter_by_keywords(results, filters.keywords)
            
            # Calculate latency
            latency = time.time() - start_time
            
            # Log search history
            if session_id:
                self._log_search(db, session_id, filters, len(results), latency * 1000)
            
            return results[:limit]
    
    def _db_to_pydantic(self, phone_db: MobilePhoneDB) -> MobilePhone:
        """Convert database model to Pydantic model."""
        return MobilePhone(**phone_db.to_dict())
    
    def _filter_by_keywords(self, phones: List[MobilePhone], keywords: List[str]) -> List[MobilePhone]:
        """Filter and score phones by keywords."""
        scored_results = []
        
        for phone in phones:
            score = self._calculate_keyword_score(phone, keywords)
            if score > 0:
                scored_results.append((phone, score))
        
        # Sort by score
        scored_results.sort(key=lambda x: x[1], reverse=True)
        return [phone for phone, _ in scored_results]
    
    def _calculate_keyword_score(self, phone: MobilePhone, keywords: List[str]) -> float:
        """Calculate relevance score based on keywords."""
        score = 0.0
        
        # Create searchable text
        searchable = " ".join([
            phone.name.lower(),
            phone.brand.lower(),
            phone.processor.lower(),
            " ".join(phone.highlights).lower(),
            " ".join(phone.pros).lower(),
        ])
        
        for keyword in keywords:
            keyword_lower = keyword.lower()
            if keyword_lower in searchable:
                score += 1.0
                
                # Bonus for name/brand match
                if keyword_lower in phone.name.lower():
                    score += 0.5
                if keyword_lower in phone.brand.lower():
                    score += 0.5
        
        return score
    
    def _log_search(self, db: Session, session_id: str, filters: SearchFilters, 
                    results_count: int, response_time_ms: float):
        """Log search to database for analytics."""
        try:
            search_log = SearchHistoryDB(
                session_id=session_id,
                query=str(filters.dict()),
                intent="search",
                filters_applied=filters.dict(),
                results_count=results_count,
                response_time_ms=response_time_ms
            )
            db.add(search_log)
            db.commit()
        except Exception as e:
            logger.error(f"Failed to log search: {e}")
    
    def get_by_id(self, phone_id: int) -> Optional[MobilePhone]:
        """Get phone by ID from database."""
        with get_db_context() as db:
            phone_db = db.query(MobilePhoneDB).filter(MobilePhoneDB.id == phone_id).first()
            if phone_db:
                return self._db_to_pydantic(phone_db)
            return None
    
    def get_by_name(self, name: str) -> Optional[MobilePhone]:
        """Get phone by name (fuzzy match) from database."""
        with get_db_context() as db:
            # Exact match
            phone_db = db.query(MobilePhoneDB).filter(
                MobilePhoneDB.name.ilike(name)
            ).first()
            
            if phone_db:
                return self._db_to_pydantic(phone_db)
            
            # Partial match
            phone_db = db.query(MobilePhoneDB).filter(
                MobilePhoneDB.name.ilike(f"%{name}%")
            ).first()
            
            if phone_db:
                return self._db_to_pydantic(phone_db)
            
            return None
    
    def compare_phones(self, phone_ids: List[int], session_id: Optional[str] = None) -> List[MobilePhone]:
        """Get phones for comparison from database."""
        with get_db_context() as db:
            phones_db = db.query(MobilePhoneDB).filter(
                MobilePhoneDB.id.in_(phone_ids)
            ).all()
            
            # Log comparison
            if session_id and phones_db:
                try:
                    from app.database.models import ComparisonHistoryDB
                    comparison_log = ComparisonHistoryDB(
                        session_id=session_id,
                        product_ids=phone_ids
                    )
                    db.add(comparison_log)
                    db.commit()
                except Exception as e:
                    logger.error(f"Failed to log comparison: {e}")
            
            return [self._db_to_pydantic(phone) for phone in phones_db]
    
    def get_recommendations(
        self,
        price_range: Optional[PriceRange] = None,
        use_case: Optional[str] = None,
        limit: int = 5
    ) -> List[MobilePhone]:
        """Get phone recommendations based on criteria from database."""
        with get_db_context() as db:
            query = db.query(MobilePhoneDB).filter(MobilePhoneDB.availability == True)
            
            if price_range:
                query = query.filter(MobilePhoneDB.price_range == price_range)
            
            # Use case based sorting
            if use_case:
                use_case_lower = use_case.lower()
                
                if "camera" in use_case_lower or "photography" in use_case_lower:
                    query = query.order_by(MobilePhoneDB.has_ois.desc(), MobilePhoneDB.has_eis.desc())
                elif "battery" in use_case_lower:
                    query = query.order_by(MobilePhoneDB.battery_capacity.desc())
                elif "gaming" in use_case_lower or "performance" in use_case_lower:
                    query = query.order_by(MobilePhoneDB.ram.desc())
                elif "compact" in use_case_lower or "small" in use_case_lower:
                    query = query.order_by(MobilePhoneDB.weight.asc())
            
            results_db = query.limit(limit).all()
            return [self._db_to_pydantic(phone) for phone in results_db]
    
    def log_product_view(self, session_id: str, product_id: int):
        """Log product view for analytics."""
        with get_db_context() as db:
            try:
                phone = db.query(MobilePhoneDB).filter(MobilePhoneDB.id == product_id).first()
                if phone:
                    view_log = ProductViewDB(
                        session_id=session_id,
                        product_id=product_id,
                        product_name=phone.name,
                        brand=phone.brand
                    )
                    db.add(view_log)
                    db.commit()
            except Exception as e:
                logger.error(f"Failed to log product view: {e}")
    
    def get_all_phones(self, limit: int = 100) -> List[MobilePhone]:
        """Get all phones from database."""
        with get_db_context() as db:
            phones_db = db.query(MobilePhoneDB).filter(
                MobilePhoneDB.availability == True
            ).limit(limit).all()
            return [self._db_to_pydantic(phone) for phone in phones_db]


# Global instance
search_service = SearchService()


def get_search_service() -> SearchService:
    """Get search service instance."""
    return search_service
