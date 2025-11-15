import sys
import time
from pathlib import Path

from fastapi import APIRouter, HTTPException

import backend.entrypoints.asgi as asgi_module
from backend.entrypoints.api.model import (
    RelevanceFeedbackQuery,
    SearchQuery,
    SearchResponse,
    SearchResult,
)

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))



router = APIRouter(prefix="/search", tags=["Search"])


@router.get("", response_model=SearchResponse)
async def search_documents(search_query: str):
    """Search documents using BM25"""

    searcher = asgi_module.searcher
    if searcher is None:
        raise HTTPException(status_code=503, detail="Search engine not initialized")


    if not search_query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    try:
        start_time = time.time()

        results = searcher.search(query=search_query, verbose=False)

        search_time = round(time.time() - start_time, 4)

        
        formatted_results = []
        for r in results:
            snippet = r["text"][:300].replace("\n", " ").strip()
            if len(r["text"]) > 300:
                snippet += "..."
            formatted_results.append(
                SearchResult(
                    doc_id=r["doc_id"],
                    title=r["title"],
                    text_snippet=snippet,
                    score=round(r["score"], 4),
                    url=r["url"],
                )
            )

       
        return SearchResponse(
            
            query=search_query,
            total_results=len(formatted_results),
            results=formatted_results,
            search_time=search_time,
            parameters={
                "k1": 1.2,
                "b": 0.75,
               
                "top_k": len(results)
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")

@router.post("/similar", response_model=SearchResponse)
async def search_similar_documents(feedback_query: RelevanceFeedbackQuery):
    """Find similar documents (Relevance Feedback)"""
 
    searcher = asgi_module.searcher
    relevance_feedback = asgi_module.relevance_feedback
    
    if searcher is None or relevance_feedback is None:
        raise HTTPException(status_code=503, detail="Search engine not initialized")
    
    try:
        start_time = time.time()
        
        # Update parameters
        original_k1, original_b = searcher.k1, searcher.b
        searcher.k1, searcher.b = feedback_query.k1, feedback_query.b
        
        # Find similar
        results = relevance_feedback.find_similar(
            searcher=searcher,
            doc_id=feedback_query.doc_id,
            top_k=feedback_query.top_k,
            num_terms=feedback_query.num_terms
        )
        
        # Restore parameters
        searcher.k1, searcher.b = original_k1, original_b
        
        search_time = time.time() - start_time
        
        # Get source document
        source_doc = searcher.doc_mapping.get(feedback_query.doc_id, {})
        source_title = source_doc.get('title', f'Document {feedback_query.doc_id}')
        
        # Format results
        formatted_results = []
        for result in results:
            text_snippet = result['text'][:300].replace('\n', ' ').strip()
            if len(result['text']) > 300:
                text_snippet += "..."
            
            formatted_results.append(SearchResult(
                doc_id=result['doc_id'],
                title=result['title'],
                text_snippet=text_snippet,
                score=round(result['score'], 4),
                url=result['url']
            ))
        
        return SearchResponse(
            query=f"Similar to: {source_title}",
            total_results=len(formatted_results),
            results=formatted_results,
            search_time=round(search_time, 4),
            parameters={
                "doc_id": feedback_query.doc_id,
                "k1": feedback_query.k1,
                "b": feedback_query.b,
                "top_k": feedback_query.top_k,
                "num_terms": feedback_query.num_terms
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/document/{doc_id}")
async def get_document(doc_id: int):
    """Get full document by ID"""
    searcher = asgi_module.searcher
    
    if searcher is None:
        raise HTTPException(status_code=503, detail="Search engine not initialized")
    
    try:
        if doc_id not in searcher.doc_mapping:
            raise HTTPException(status_code=404, detail=f"Document {doc_id} not found")
        
        doc_info = searcher.doc_mapping[doc_id]
        doc_text = searcher._get_document_text(doc_id)
        
        return {
            "doc_id": doc_id,
            "title": doc_info['title'],
            "text": doc_text,
            "length": searcher.doc_lengths.get(doc_id, 0),
            "url": f"https://pt.wikipedia.org/wiki/{doc_info['title'].replace(' ', '_')}"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

