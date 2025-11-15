from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class SearchQuery(BaseModel):
    """Model for search query request"""
    query: str = Field(..., min_length=1, description="Search query string")
    # top_k: int = Field(default=10, ge=1, le=100, description="Number of results")
    # k1: float = Field(default=1.2, ge=0, description="BM25 k1 parameter")
    # b: float = Field(default=0.75, ge=0, le=1, description="BM25 b parameter")


class RelevanceFeedbackQuery(BaseModel):
    """Model for relevance feedback request"""
    doc_id: int = Field(..., description="Document ID")
    top_k: int = Field(default=10, ge=1, le=100)
    k1: float = Field(default=1.2, ge=0)
    b: float = Field(default=0.75, ge=0, le=1)
    num_terms: Optional[int] = Field(default=20, ge=5, le=100)


class SearchResult(BaseModel):
    """Single search result"""
    doc_id: int
    title: str
    text_snippet: str
    score: float
    url: str


class SearchResponse(BaseModel):
    """Search response"""
    query: str
    total_results: int
    results: List[SearchResult]
    search_time: float
    parameters: Dict[str, Any]


class IndexStats(BaseModel):
    """Index statistics"""
    total_documents: int
    total_terms: int
    avg_doc_length: float
    index_size_mb: Optional[float] = None
    tokenizer_config: Dict[str, Any]


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    index_loaded: bool
    message: Optional[str] = None

