import sys
from pathlib import Path

from fastapi import APIRouter, HTTPException

import backend.entrypoints.asgi as asgi_module
from backend.entrypoints.api.model import HealthResponse, IndexStats

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))



router = APIRouter(prefix="/health", tags=["Health"])


@router.get("", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    # Import here to avoid circular imports
    
    searcher = asgi_module.searcher
    
    return HealthResponse(
        status="healthy" if searcher is not None else "degraded",
        index_loaded=searcher is not None,
        message="Search engine is ready" if searcher else "Index not loaded"
    )


@router.get("/stats", response_model=IndexStats)
async def get_statistics():
    """Get index statistics"""
    
    searcher = asgi_module.searcher
    
    if searcher is None:
        raise HTTPException(
            status_code=503,
            detail="Search index not loaded"
        )
    
    try:
        stats = searcher.get_statistics()
        tokenizer_config = searcher.tokenizer.get_config()
        
        # Calculate index size
        index_dir = Path(searcher.index_dir)
        index_size_bytes = sum(
            f.stat().st_size 
            for f in index_dir.rglob('*') 
            if f.is_file()
        )
        index_size_mb = index_size_bytes / (1024 * 1024)
        
        return IndexStats(
            total_documents=stats["num_documents"],
            total_terms=stats["num_terms"],
            avg_doc_length=stats["avg_doc_length"],
            index_size_mb=round(index_size_mb, 2),
            tokenizer_config=tokenizer_config
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

