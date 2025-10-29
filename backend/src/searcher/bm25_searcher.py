import json
import math
from collections import defaultdict

from src.indexer.tokenizer import Tokenizer


class BM25Searcher:
    """BM25 ranking algorithm for document retrieval."""
    
    def __init__(self, index_dir="data/index", k1=1.2, b=0.75):
        self.index_dir = index_dir
        self.k1 = k1
        self.b = b
        
        # Load index and metadata
        self._load_index()
        self._load_metadata()
        
        # Initialize tokenizer with same config as indexer
        tokenizer_config = self.metadata["tokenizer_config"]
        self.tokenizer = Tokenizer(**tokenizer_config)
    
    def _load_index(self):
        """Load inverted index from disk."""
        index_path = f"{self.index_dir}/inverted_index.json"
        print(f"📖 Loading index from {index_path}...")
        
        self.index = {}
        with open(index_path, "r", encoding="utf-8") as f:
            for line in f:
                term, postings = json.loads(line)
                self.index[term] = postings
        
        print(f"✓ Loaded {len(self.index)} terms")
    
    def _load_metadata(self):
        """Load metadata (doc mapping, term stats, etc.)."""
        metadata_path = f"{self.index_dir}/metadata.json"
        with open(metadata_path, "r", encoding="utf-8") as f:
            self.metadata = json.load(f)
        
        self.doc_mapping = {int(k): v for k, v in self.metadata["doc_mapping"].items()}
        self.doc_lengths = {int(k): v for k, v in self.metadata["doc_lengths"].items()}
        self.term_stats = self.metadata["term_stats"]
        self.num_documents = self.metadata["num_documents"]
        self.avg_doc_length = self.metadata["avg_doc_length"]
        
        print(f"✓ Loaded metadata: {self.num_documents} documents")
    
    def search(self, query, top_k=10):
        """Search for documents matching query using BM25."""
        # Tokenize query
        query_tokens = self.tokenizer.tokenize_list(query)
        
        if not query_tokens:
            return []
        
        # Calculate BM25 scores
        scores = defaultdict(float)
        
        for term in query_tokens:
            if term not in self.index:
                continue
            
            postings = self.index[term]
            df = len(postings)  # document frequency
            idf = math.log((self.num_documents - df + 0.5) / (df + 0.5) + 1.0)
            
            for doc_id, positions in postings:
                tf = len(positions)  # term frequency in document
                doc_len = self.doc_lengths[doc_id]
                
                # BM25 formula
                numerator = tf * (self.k1 + 1)
                denominator = tf + self.k1 * (1 - self.b + self.b * (doc_len / self.avg_doc_length))
                
                scores[doc_id] += idf * (numerator / denominator)
        
        # Sort by score
        ranked_docs = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
        
        # Format results
        results = []
        for doc_id, score in ranked_docs:
            results.append({
                "doc_id": doc_id,
                "score": score,
                "title": self.doc_mapping[doc_id]["title"],
                "url": f"https://pt.wikipedia.org/wiki/{self.doc_mapping[doc_id]['title'].replace(' ', '_')}"
            })
        
        return results
