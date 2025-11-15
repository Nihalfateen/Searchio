import json
import math
import re
import sqlite3
import time
from collections import defaultdict
from pathlib import Path

from backend.src.indexer.tokenizer import Tokenizer


class FastBM25Searcher:
    """
    Fast BM25 searcher that doesn't load the entire index into memory.
    Only loads terms when they're actually searched.
    """
    
    def __init__(self, index_dir="index_data", k1=1.2, b=0.75):
        self.index_dir = Path(index_dir)
        self.k1 = k1
        self.b = b
        
        # Build term offset map (FAST - just positions, not data)
        self._build_term_offset_map()
        
        # Load metadata (small, fast)
        self._load_doc_mapping()

        # Load the tokenizer configuration used during indexing
        tokenizer_config_path = self.index_dir / "tokenizer_config.json"
        with open(tokenizer_config_path, "r", encoding="utf-8") as f:
            tokenizer_config = json.load(f)

        self.tokenizer = Tokenizer.from_config(tokenizer_config)
        print("✓ Tokenizer loaded from configuration")

        print(f"✓ Fast searcher ready! (index loaded on-demand)")
    
    def _build_term_offset_map(self):
        """
        Build a map of term -> file offset.
        This is FAST because we don't parse the postings, just record positions.
        """
        index_path = self.index_dir / "final_index.json"
        print(f" Building term offset map from {index_path}...")
        
        self.term_offsets = {}
        
        with open(index_path, "r", encoding="utf-8") as f:
            offset = 0
            count = 0
            
            while True:
                line = f.readline()
                if not line:
                    break
                
                # Extract just the term (fast!)
                term = json.loads(line)[0]
                self.term_offsets[term] = offset
                
                offset = f.tell()  # Save current position
                count += 1
                
                if count % 50000 == 0:
                    print(f"   ... indexed {count:,} terms", end='\r')
        
        print(f" Indexed {len(self.term_offsets):,} terms" + " " * 20)
    
    def _load_doc_mapping(self):
        """Load document mapping (small, fast)."""
        doc_map_path = self.index_dir / "doc_map.json"
        
        with open(doc_map_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        self.doc_mapping = {}
        self.doc_lengths = {}
        
        for doc_id_str, doc_info in data.items():
            doc_id = int(doc_id_str)
            self.doc_mapping[doc_id] = {"title": doc_info["title"]}
            self.doc_lengths[doc_id] = doc_info["length"]
        
        self.num_documents = len(self.doc_mapping)
        self.avg_doc_length = sum(self.doc_lengths.values()) / self.num_documents
        
        print(f"✓ Loaded {self.num_documents:,} documents (avg length: {self.avg_doc_length:.1f})")
    
    def _get_postings(self, term):
        """
        Load postings for a specific term (on-demand).
        This is FAST because we only load what we need!
        """
        if term not in self.term_offsets:
            return []
        
        index_path = self.index_dir / "final_index.json"
        
        with open(index_path, "r", encoding="utf-8") as f:
            # Jump directly to this term's position
            f.seek(self.term_offsets[term])
            line = f.readline()
            _, postings = json.loads(line)
            return postings
    
    def tokenize(self, text):
        return list(self.tokenizer.tokenize(text))

    
    def search(self, query, top_k=20, verbose=False):
        """
        Search using BM25 (FAST - only loads needed terms!).
        """
        # Tokenize
        query_tokens = self.tokenize(query)
        
        if not query_tokens:
            return []
        
        if verbose:
            print(f" Query tokens: {query_tokens}")
        
        scores = defaultdict(float)
        
        for term in query_tokens:
            # Load this term's postings (on-demand!)
            postings = self._get_postings(term)
            
            if not postings:
                if verbose:
                    print(f" Term '{term}' not in index")
                continue
            
            df = len(postings)
            idf = math.log((self.num_documents - df + 0.5) / (df + 0.5) + 1.0)
            
            if verbose:
                print(f"  Term '{term}': df={df}, idf={idf:.3f}")
            
            for doc_id, positions in postings:
                tf = len(positions)
                doc_len = self.doc_lengths[doc_id]
                
                numerator = tf * (self.k1 + 1)
                denominator = tf + self.k1 * (1 - self.b + self.b * (doc_len / self.avg_doc_length))
                
                scores[doc_id] += idf * (numerator / denominator)
        
        if not scores:
            return []
        
        # Sort and return top-k
        ranked_docs = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
        
        results = []
        for doc_id, score in ranked_docs:
            text = self._get_document_text(doc_id)  # stored in database

            results.append({
                "doc_id": doc_id,
                "score": score,
                "title": self.doc_mapping[doc_id]["title"],
                "text": text,
                "url": f"https://pt.wikipedia.org/wiki/{self.doc_mapping[doc_id]['title'].replace(' ', '_')}"
            })
        
        return results


    def _get_document_text(self, doc_id):
        """Fetch full text for a document by its doc_id."""
        db_path = self.index_dir / "forward_index.db"
        if not db_path.exists():
            return None

        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("SELECT text FROM documents WHERE doc_id = ?", (doc_id,))
        row = cur.fetchone()
        conn.close()

        return row[0] if row else None
    
    def get_statistics(self):
        """Get index statistics."""
        return {
            "num_documents": self.num_documents,
            "num_terms": len(self.term_offsets),
            "avg_doc_length": self.avg_doc_length,
            "k1": self.k1,
            "b": self.b
        }

def interactive_search():
    """Interactive search with the FAST searcher."""
    
    print("\n" + "="*70)
    print("FAST BM25 SEARCH (On-Demand Index Loading)")
    print("="*70 + "\n")
    
    import time
    start = time.time()
    
    try:
        searcher = FastBM25Searcher(index_dir="index_data")
        
        load_time = time.time() - start
        print(f"✓ Initialized in {load_time:.2f} seconds\n")
        
        stats = searcher.get_statistics()
        print(" Index Statistics:")
        print(f"  Documents: {stats['num_documents']:,}")
        print(f"  Terms: {stats['num_terms']:,}")
        print(f"  Avg doc length: {stats['avg_doc_length']:.1f}")
        print()
        
        print("Commands:")
        print("  - Enter a query to search")
        print("  - Type 'quit' to exit")
        print()
        
        while True:
            query = input("🔍 Search: ").strip()
            
            if query.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break
            
            if not query:
                continue
            
            # Time the search
            search_start = time.time()
            results = searcher.search(query, top_k=20)
            search_time = time.time() - search_start
            
            print(f"\n  Search time: {search_time:.3f} seconds")
            
            if results:
                print(f" Found {len(results)} results:\n")
                for i, result in enumerate(results, 1):
                    print(f"{i}. {result['title']}")
                    print(f"   Score: {result['score']:.3f}")
                    print(f"   Snippet: {result['text'][:200].replace('\n', ' ')}...")
                    print(f"   {result['url']}")
                    print()
            else:
                print("⚠ No results found\n")
    
    except Exception as e:
        print(f"\n ERROR: {e}")
        import traceback
        traceback.print_exc()

def benchmark():
    """Benchmark the fast searcher."""
    
    print("\n" + "="*70)
    print("BENCHMARK: Fast BM25 Searcher")
    print("="*70 + "\n")
    
    import time
    
    # Initialize
    print("Initializing...")
    start = time.time()
    searcher = FastBM25Searcher(index_dir="index_data")
    init_time = time.time() - start
    
    print(f"\n✓ Initialization: {init_time:.2f} seconds\n")
    
    # Test queries
    test_queries = [
        "Portugal",
        "futebol",
        "Lisboa capital",
        "história portuguesa",
        "Cristiano Ronaldo",
        "economia europeia",
        "cultura arte",
        "música tradicional",
        "gastronomia portuguesa",
        "desporto olímpico"
    ]
    
    print("Running test queries...\n")
    
    times = []
    for query in test_queries:
        start = time.time()
        results = searcher.search(query, top_k=20)
        elapsed = time.time() - start
        times.append(elapsed)
        
        print(f"Query: '{query:25}' → {len(results):2} results in {elapsed:.4f}s")
    
    print(f"\n{'='*70}")
    print(f"Average search time: {sum(times)/len(times):.4f} seconds")
    print(f"Total queries: {len(test_queries)}")
    print(f"Queries/second: {len(test_queries)/sum(times):.1f}")
    print(f"{'='*70}\n")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "benchmark":
        benchmark()
    else:
        interactive_search()