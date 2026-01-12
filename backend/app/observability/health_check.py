import time
import asyncio
from typing import Dict, Any
from datetime import datetime

from app.config import settings
from app.datamodels import HealthStatus
from app.observability.logging import get_logger

logger = get_logger(__name__)


class HealthCheckService:
    """Service for health monitoring and status checks."""
    
    def __init__(self):
        self.start_time = time.time()
        self.last_check_time = None
        self.check_history = []
    
    async def check_health(self) -> HealthStatus:
        """Perform comprehensive health check."""
        status = HealthStatus(
            status="healthy",
            timestamp=datetime.utcnow(),
            components={},
            metrics={}
        )
        
        # Check database
        db_status = await self._check_database()
        status.components["database"] = db_status
        
        # Check cache
        cache_status = await self._check_cache()
        status.components["cache"] = cache_status
        
        # Check LLM providers
        llm_status = await self._check_llm()
        status.components["llm_primary"] = llm_status["primary"]
        status.components["llm_fallback"] = llm_status["fallback"]
        
        # Calculate overall status
        component_statuses = [c["status"] for c in status.components.values()]
        
        if any(s == "unhealthy" for s in component_statuses):
            status.status = "unhealthy"
        elif any(s == "degraded" for s in component_statuses):
            status.status = "degraded"
        else:
            status.status = "healthy"
        
        # Add system metrics
        status.metrics = {
            "uptime_seconds": time.time() - self.start_time,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        self.last_check_time = time.time()
        self.check_history.append(status)
        
        # Keep only last 100 checks
        if len(self.check_history) > 100:
            self.check_history = self.check_history[-100:]
        
        return status
    
    async def _check_database(self) -> Dict[str, Any]:
        """Check database connectivity."""
        try:
            from app.database.db import check_db_connection
            import time
            
            start_time = time.time()
            is_connected = check_db_connection()
            latency_ms = (time.time() - start_time) * 1000
            
            if is_connected:
                return {
                    "status": "healthy",
                    "message": "Database connection successful",
                    "latency_ms": round(latency_ms, 2)
                }
            else:
                return {
                    "status": "unhealthy",
                    "message": "Database connection failed",
                    "latency_ms": None
                }
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                "status": "unhealthy",
                "message": str(e),
                "latency_ms": None
            }
    
    async def _check_cache(self) -> Dict[str, Any]:
        """Check cache connectivity."""
        try:
            if not settings.CACHE_ENABLED or not settings.REDIS_URL:
                return {
                    "status": "degraded",
                    "message": "Cache not configured",
                    "latency_ms": None
                }
            
            # Check Redis connection
            import time
            try:
                import redis
                start_time = time.time()
                r = redis.from_url(settings.REDIS_URL, socket_connect_timeout=2)
                r.ping()
                latency_ms = (time.time() - start_time) * 1000
                r.close()
                
                return {
                    "status": "healthy",
                    "message": "Cache operational",
                    "latency_ms": round(latency_ms, 2)
                }
            except (redis.ConnectionError, redis.TimeoutError) as e:
                logger.warning(f"Redis connection failed: {e}")
                return {
                    "status": "degraded",
                    "message": f"Redis unavailable: {str(e)}",
                    "latency_ms": None
                }
        except Exception as e:
            logger.error(f"Cache health check failed: {e}")
            return {
                "status": "degraded",
                "message": str(e),
                "latency_ms": None
            }
    
    async def _check_llm(self) -> Dict[str, Dict[str, Any]]:
        """Check LLM provider availability."""
        result = {
            "primary": {"status": "unknown", "message": "Not checked"},
            "fallback": {"status": "unknown", "message": "Not checked"}
        }
        
        try:
            # Check if API keys are configured
            if settings.GOOGLE_API_KEY:
                result["primary"] = {
                    "status": "healthy",
                    "message": "Gemini API key configured",
                    "provider": "gemini"
                }
            else:
                result["primary"] = {
                    "status": "degraded",
                    "message": "No primary LLM configured",
                    "provider": None
                }
            
            if settings.OPENAI_API_KEY:
                result["fallback"] = {
                    "status": "healthy",
                    "message": "OpenAI API key configured",
                    "provider": "openai"
                }
            elif settings.ANTHROPIC_API_KEY:
                result["fallback"] = {
                    "status": "healthy",
                    "message": "Anthropic API key configured",
                    "provider": "anthropic"
                }
            else:
                result["fallback"] = {
                    "status": "degraded",
                    "message": "No fallback LLM configured",
                    "provider": None
                }
            
        except Exception as e:
            logger.error(f"LLM health check failed: {e}")
            result["primary"]["status"] = "unhealthy"
            result["primary"]["message"] = str(e)
        
        return result
    
    def get_readiness(self) -> bool:
        """Check if service is ready to accept requests."""
        # Service is ready if at least one LLM provider is available
        return settings.GOOGLE_API_KEY is not None or \
               settings.OPENAI_API_KEY is not None or \
               settings.ANTHROPIC_API_KEY is not None
    
    def get_liveness(self) -> bool:
        """Check if service is alive."""
        # Service is alive if it's running
        return True
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get health metrics."""
        return {
            "uptime_seconds": time.time() - self.start_time,
            "last_check_time": self.last_check_time,
            "total_checks": len(self.check_history),
            "recent_status": self.check_history[-1].status if self.check_history else "unknown"
        }


# Global instance
health_service = HealthCheckService()


def get_health_service() -> HealthCheckService:
    """Get health service instance."""
    return health_service
