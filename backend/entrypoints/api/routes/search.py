"""Search endpoints."""

# from fastapi import APIRouter
# from sapien.core.model import Document
# from sapien.entrypoints.api.model import SearchResponse

# router = APIRouter(tags=["search engine"])


# @router.get("/search")
# def search(query: str, num_results: int = 10) -> SearchResponse:
#     """Search for documents matching the given query."""
#     return SearchResponse(
#         results=[
#             Document(id=1, title="Document 1", content="Content 1"),
#             Document(id=2, title="Document 2", content="Content 2"),
#             Document(id=3, title="Document 3", content="Content 3"),
#         ]
#     )


# @router.get("/search_like")
# def search_like(doc_id: int, num_results: int = 10) -> SearchResponse:
#     """Search for documents similar to the given document ID."""
#     return SearchResponse(results=[])


import os
import sys

from flask import Flask, jsonify, request
from flask_cors import CORS

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.src.searcher.bm25_searcher import BM25Searcher
from backend.src.searcher.relevance_feedback import RelevanceFeedback

app = Flask(__name__)
CORS(app)  # Enable CORS for Flutter app

# Initialize searcher and relevance feedback
searcher = None
relevance_feedback = None


@app.before_request
def initialize():
    """Initialize searcher on first request."""
    global searcher, relevance_feedback
    if searcher is None:
        print("🚀 Initializing searcher...")
        searcher = BM25Searcher(index_dir="data/index")
        relevance_feedback = RelevanceFeedback(index_dir="data/index")
        print("✓ Searcher ready!")


@app.route('/search', methods=['GET'])
def search():
   
    query = request.args.get('q', '')
    top_k = int(request.args.get('k', 10))
    
    if not query:
        return jsonify({"error": "Query parameter 'q' is required"}), 400
    
    results = searcher.search(query, top_k=top_k)
    
    return jsonify({
        "query": query,
        "num_results": len(results),
        "results": results
    })


@app.route('/similar/<int:doc_id>', methods=['GET'])
def similar(doc_id):
   
    top_k = int(request.args.get('k', 10))
    
    results = relevance_feedback.find_similar(doc_id, top_k=top_k)
    
    return jsonify({
        "doc_id": doc_id,
        "num_results": len(results),
        "results": results
    })


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({"status": "ok", "message": "Searcher API is running"})


if __name__ == "__main__":
    print("=" * 70)
    print("STARTING SEARCHER API")
    print("=" * 70)
    print("Endpoints:")
    print("  GET /search?q=<query>&k=<num_results>")
    print("  GET /similar/<doc_id>?k=<num_results>")
    print("  GET /health")
    print("=" * 70)
    app.run(host='0.0.0.0', port=5000, debug=True)