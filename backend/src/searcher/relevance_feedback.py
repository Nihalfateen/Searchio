from collections import Counter

from .bm25_searcher import BM25Searcher


class RelevanceFeedback:
    """Find similar documents using relevance feedback."""
    
    def __init__(self, index_dir="data/index"):
        self.searcher = BM25Searcher(index_dir=index_dir)
    
    def find_similar(self, doc_id, top_k=10, num_terms=20):
        """Find documents similar to given document."""
        # Get document tokens
        doc_tokens = self._get_document_tokens(doc_id)
        
        if not doc_tokens:
            return []
        
        # Get most frequent terms (excluding stopwords)
        term_counts = Counter(doc_tokens)
        top_terms = [term for term, _ in term_counts.most_common(num_terms)]
        
        # Create pseudo-query from top terms
        pseudo_query = " ".join(top_terms)
        
        # Search using BM25
        results = self.searcher.search(pseudo_query, top_k=top_k + 1)
        
        # Remove the query document itself
        results = [r for r in results if r["doc_id"] != doc_id][:top_k]
        
        return results
    
    def _get_document_tokens(self, doc_id):
        """Get tokens from document by reading from index."""
        tokens = []
        
        # Extract all terms that appear in this document
        for term, postings in self.searcher.index.items():
            for posting_doc_id, positions in postings:
                if posting_doc_id == doc_id:
                    # Add term multiple times based on frequency
                    tokens.extend([term] * len(positions))
        
        return tokens