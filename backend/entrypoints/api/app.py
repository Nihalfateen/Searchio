import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.src.api.routes import health_check, search
from backend.src.searcher.fast_bm25_searcher import FastBM25Searcher
from backend.src.searcher.relevance_feedback import RelevanceFeedback

# Add backend to path if needed
backend_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_path))



# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global instances
searcher = None
relevance_feedback = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events
    """
    # Startup
    global searcher, relevance_feedback
    
    logger.info("=" * 70)
    logger.info("Starting Portuguese Wikipedia Search Engine API")
    logger.info("=" * 70)
    
    try:
        # Load index
        index_dir = "index_data"
        logger.info(f"Loading index from: {index_dir}")
        
        searcher = FastBM25Searcher(index_dir=index_dir, k1=1.2, b=0.75)
        relevance_feedback = RelevanceFeedback(index_dir=index_dir, top_terms=20)
        
        stats = searcher.get_statistics()
        logger.info("✓ Index loaded successfully!")
        logger.info(f"  - Documents: {stats['num_documents']:,}")
        logger.info(f"  - Terms: {stats['num_terms']:,}")
        logger.info(f"  - Avg doc length: {stats['avg_doc_length']:.1f}")
        logger.info("=" * 70)
        
    except Exception as e:
        logger.error(f"Failed to load index: {e}")
        logger.error("API will start but search functionality will be unavailable")
        searcher = None
        relevance_feedback = None
    
    yield
    
    # Shutdown
    logger.info("Shutting down API...")


# Create FastAPI app
app = FastAPI(
    title="Portuguese Wikipedia Search Engine",
    description="Information Retrieval System with BM25 and Relevance Feedback",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers


app.include_router(health_check.router)
app.include_router(search.router)


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Portuguese Wikipedia Search Engine API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "search": "/search"
    }


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error_type": type(exc).__name__
        }
    )


if __name__ == "__main__":
    
    
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )