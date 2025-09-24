from pydantic import BaseModel

from sapien.core.model import Document


class SearchRequest(BaseModel):
    query: str
    num_results: int = 10


class SearchResponse(BaseModel):
    results: list[Document]
