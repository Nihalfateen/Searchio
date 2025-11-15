from pydantic import BaseModel

class SearchResult(BaseModel):
    """Single search result"""
    doc_id: int
    title: str
    text_snippet: str
    score: float
    url: str
