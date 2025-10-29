
import logging

from core.limit_memory import start_memory_monitor
from core.logging import setup_logging
from src.indexer.indexer import IndexBuilder

if __name__ == "__main__":
   
    
    setup_logging(level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.info("Starting the Indexer Engine")

    start_memory_monitor(show_memory_updates=True)
    logger.info("Memory monitor started (2GB limit)")

    corpus_path = r"d:\ptwiki-articles-with-redirects.arrow"

    builder = IndexBuilder(
        corpus_path=corpus_path,
        output_dir="index_data"
    )
    
    # Build index with minimum term frequency of 3
    builder.build_index(min_term_freq=3)

    logger.info("Indexing process finished successfully")
