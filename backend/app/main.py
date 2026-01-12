import uuid
from contextlib import asynccontextmanager
from typing import List

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time

from app.config import settings
from app.datamodels import (
    ChatRequest, ChatResponse, QueryIntent, ProductCard,
    HealthStatus, MobilePhone
)
from app.services.llm_service import get_llm_service
from app.services.search_service import get_search_service
from app.services.safety_service import get_safety_service
from app.observability.health_check import get_health_service
from app.observability.logging import get_logger
from app.constants import RESPONSE_TEMPLATES

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    yield
    
    # Shutdown
    pass


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-powered shopping assistant for mobile phones",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add request timing header."""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


# Global exception handler to prevent 5xx errors
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch all unhandled exceptions and return user-friendly errors."""
    logger.error(f"UNHANDLED_ERROR | path={request.url.path} | error={str(exc)}", exc_info=True)
    
    # Return generic error message to user
    return JSONResponse(
        status_code=500,
        content={
            "detail": "An unexpected error occurred. Please try again later.",
            "error_id": str(uuid.uuid4())  # For tracking in logs
        }
    )


# HTTP exception handler for better error messages
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions gracefully."""
    # Log 5xx errors only
    if exc.status_code >= 500:
        logger.error(f"HTTP_ERROR | path={request.url.path} | status={exc.status_code} | detail={exc.detail}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "operational",
        "docs": "/docs"
    }


@app.get("/health", response_model=HealthStatus)
async def health_check():
    """Comprehensive health check."""
    health_service = get_health_service()
    return await health_service.check_health()


@app.get("/health/ready")
async def readiness_check():
    """Readiness probe for Kubernetes."""
    health_service = get_health_service()
    if health_service.get_readiness():
        return {"status": "ready"}
    raise HTTPException(status_code=503, detail="Service not ready")


@app.get("/health/live")
async def liveness_check():
    """Liveness probe for Kubernetes."""
    health_service = get_health_service()
    if health_service.get_liveness():
        return {"status": "alive"}
    raise HTTPException(status_code=503, detail="Service not alive")


@app.post(f"{settings.API_PREFIX}/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Main chat endpoint for shopping queries.
    """
    session_id = request.session_id or str(uuid.uuid4())
    
    try:
        # Safety check
        safety_service = get_safety_service()
        is_safe, safety_reason = safety_service.check_query_safety(request.message)
        
        if not is_safe:
            return ChatResponse(
                message=safety_service.get_safe_error_message("adversarial"),
                intent=QueryIntent.ADVERSARIAL,
                confidence=1.0,
                is_safe=False,
                safety_message=safety_reason,
                session_id=session_id
            )
        
        # Get services
        llm_service = get_llm_service()
        search_service = get_search_service()
        
        # Classify intent
        intent = await llm_service.classify_intent(request.message)
        
        # Handle adversarial/irrelevant queries
        if intent in [QueryIntent.ADVERSARIAL, QueryIntent.IRRELEVANT]:
            return ChatResponse(
                message=safety_service.get_safe_error_message("inappropriate"),
                intent=intent,
                confidence=0.9,
                is_safe=True,
                session_id=session_id
            )
        
        # Extract filters for search
        filters = await llm_service.extract_filters(request.message)
        
        # Search for products
        products = search_service.search(filters, limit=settings.MAX_SEARCH_RESULTS)
        
        # Create context for LLM
        context = "\n\n".join([
            f"Phone {i+1}: {p.name} by {p.brand}\n"
            f"Price: ₹{p.price:,.0f}\n"
            f"Display: {p.display_size}\" {p.display_type}, {p.refresh_rate}Hz\n"
            f"Processor: {p.processor}\n"
            f"RAM/Storage: {p.ram}GB / {p.storage}GB\n"
            f"Camera: {p.rear_camera} (OIS: {p.has_ois})\n"
            f"Battery: {p.battery_capacity}mAh, {p.fast_charging}W charging\n"
            f"Highlights: {', '.join(p.highlights)}\n"
            f"Pros: {', '.join(p.pros)}"
            for i, p in enumerate(products[:5])  # Top 5 for context
        ])
        
        # Generate response
        response_text = await llm_service.generate_response(
            query=request.message,
            context=context,
            conversation_history=request.conversation_history
        )
        
        # Create product cards
        product_cards = [
            ProductCard(
                id=p.id,
                name=p.name,
                brand=p.brand,
                price=p.price,
                key_specs={
                    "Display": f"{p.display_size}\" {p.display_type}",
                    "Processor": p.processor,
                    "RAM": f"{p.ram}GB",
                    "Camera": p.rear_camera,
                    "Battery": f"{p.battery_capacity}mAh"
                },
                highlights=p.highlights[:3]
            )
            for p in products
        ]
        
        return ChatResponse(
            message=response_text,
            intent=intent,
            products=product_cards,
            confidence=0.85,
            is_safe=True,
            session_id=session_id,
            suggestions=RESPONSE_TEMPLATES["comparison_suggestions"] if products else []
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Log error and return user-friendly message
        logger.error(f"CHAT_ERROR | session_id={session_id} | error={str(e)}", exc_info=True)
        return ChatResponse(
            message="I'm having trouble processing your request right now. Please try again.",
            intent=QueryIntent.SEARCH,
            confidence=0.0,
            is_safe=True,
            session_id=session_id
        )


@app.get(f"{settings.API_PREFIX}/products", response_model=List[MobilePhone])
async def get_products(
    brand: str = None,
    min_price: float = None,
    max_price: float = None,
    limit: int = 20
):
    """Get products with optional filters."""
    try:
        search_service = get_search_service()
        
        from app.models import SearchFilters, Brand
        filters = SearchFilters(
            brands=[Brand(brand)] if brand else None,
            min_price=min_price,
            max_price=max_price
        )
        
        products = search_service.search(filters, limit=limit)
        return products
        
    except Exception as e:
        logger.error(f"PRODUCTS_ERROR | error={str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "Unable to fetch products. Please try again later."}
        )


@app.get(f"{settings.API_PREFIX}/products/{{product_id}}", response_model=MobilePhone)
async def get_product(product_id: int):
    """Get product by ID."""
    search_service = get_search_service()
    product = search_service.get_by_id(product_id)
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return product


@app.post(f"{settings.API_PREFIX}/compare")
async def compare_products(product_ids: List[int]):
    """Compare multiple products."""
    try:
        if len(product_ids) < 2:
            raise HTTPException(
                status_code=400,
                detail="At least 2 products required for comparison"
            )
        
        if len(product_ids) > 3:
            raise HTTPException(
                status_code=400,
                detail="Maximum 3 products can be compared"
            )
        
        search_service = get_search_service()
        products = search_service.compare_phones(product_ids)
        
        if len(products) < 2:
            raise HTTPException(
                status_code=404,
                detail="One or more products not found"
            )
        
        return {"products": products}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"COMPARE_ERROR | error={str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "Unable to compare products. Please try again later."}
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.is_development
    )
