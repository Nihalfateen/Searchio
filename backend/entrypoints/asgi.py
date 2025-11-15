"""
ASGI entry point
Run: python3 -m uvicorn backend.entrypoints.asgi:app --reload
"""

import json
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.entrypoints.api.routes.healthcheck import router as health_router
from backend.entrypoints.api.routes.search import router as search_router
from backend.src.searcher.bm25_searcher import FastBM25Searcher
from backend.src.searcher.relevance_feedback import RelevanceFeedback

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global instances
searcher = None
relevance_feedback = None

class UTF8JSONResponse(JSONResponse):
    media_type = "application/json; charset=utf-8"
    def render(self, content) -> bytes:
        return json.dumps(
            content,
            ensure_ascii=False,        # keep non-ASCII like "História"
            allow_nan=False,
            separators=(",", ":"),
        ).encode("utf-8")
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan events"""
    global searcher, relevance_feedback
    
    logger.info("=" * 70)
    logger.info("Starting Portuguese Wikipedia Search Engine API")
    logger.info("=" * 70)
    
    try:
        
        
        index_dir = "index_data"
        logger.info(f"Loading index from: {index_dir}")
        
        searcher = FastBM25Searcher(index_dir=index_dir, k1=1.2, b=0.75)
        relevance_feedback = RelevanceFeedback(index_dir=index_dir, top_terms=20)
        
        stats = searcher.get_statistics()
        logger.info("✓ Index loaded!")
        logger.info(f"  Documents: {stats['num_documents']:,}")
        logger.info(f"  Terms: {stats['num_terms']:,}")
        logger.info("=" * 70)
        
    except Exception as e:
        logger.error(f"Failed to load index: {e}")
        import traceback
        traceback.print_exc()
    
    yield
    logger.info("Shutting down...")


# Create app
app = FastAPI(
    title="Portuguese Wikipedia Search Engine",
    description="IR System with BM25 and Relevance Feedback",
    version="1.0.0",
    lifespan=lifespan,
    default_response_class=UTF8JSONResponse
    
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import routers (after app creation)


app.include_router(health_router)
app.include_router(search_router)


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint"""
    return {
        "message": "Portuguese Wikipedia Search Engine API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "docs": "/docs",
            "health": "/health",
            "stats": "/health/stats",
            "search": "POST /search",
            "similar": "POST /search/similar"
        }
    }


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error": str(exc)}
    )
