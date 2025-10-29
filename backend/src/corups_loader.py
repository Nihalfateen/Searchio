import pyarrow.parquet as pq


class CorpusLoader:
    """Load and preprocess Wikipedia corpus."""
    
    def __init__(self, corpus_path):
        self.corpus_path = corpus_path
    
    def load_documents(self):
        """Load documents from Arrow/Parquet file."""
        print(f"📖 Loading corpus from {self.corpus_path}...")
        
        # Read Arrow/Parquet file
        table = pq.read_table(self.corpus_path)
        df = table.to_pandas()
        
        # Filter out redirects
        df = df[df['redirect'] == False]
        
        # Convert to list of dicts
        documents = df.to_dict('records')
        
        print(f"✓ Loaded {len(documents)} documents (redirects filtered)")
        return documents