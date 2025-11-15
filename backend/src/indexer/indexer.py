import json
import logging
import os
from collections import defaultdict
from functools import partial
from multiprocessing import Pool, cpu_count

from backend.src.indexer.forward_index import ForwardIndex
from backend.src.indexer.spimi import SPIMIIndexer
from backend.src.indexer.tokenizer import Tokenizer
from pyarrow import ipc
from tqdm import tqdm


def process_document(doc_data, tokenizer_config):
    """
    Process a single document tuple (doc_id, title, text, redirect) with the given tokenizer config.
    Returns (doc_id, title, tokens) or None if filtered out.
    """
    doc_id, title_str, text_str, redirect_str = doc_data

    # Filter out redirects
    if redirect_str:
        return None

    # Filter out empty or very short pages
    if not text_str or len(text_str.strip()) < 50:
        return None

    # Tokenize
    tokenizer = Tokenizer(**tokenizer_config)
    tokens = list(tokenizer.tokenize(text_str))

    # Skip documents with too few tokens
    if len(tokens) < 3:
        return None

    return doc_id, title_str, tokens


class IndexBuilder:
    def __init__(self, corpus_path, output_dir="index_data", num_workers=None):
        self.logger = logging.getLogger(__name__)
        self.corpus_path = corpus_path
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

        self.num_workers = num_workers or max(1, cpu_count() - 1)
        self.logger.info("Using %d worker processes", self.num_workers)

        # Components
        self.tokenizer = Tokenizer(min_len=2, use_stem=True, use_stopwords=True)
        self.indexer = SPIMIIndexer(
            block_dir=os.path.join(output_dir, "blocks"),
            block_limit=100000,
        )

        # Forward index path (we'll open it inside build_index via a context manager)
        self.forward_path = os.path.join(self.output_dir, "forward_index.jsonl")
        # Metadata
        self.doc_map = {}
        self.stats = {
            "total_docs": 0,
            "indexed_docs": 0,
            "filtered_docs": 0,
            "avg_doc_length": 0.0,
        }

    def build_index(self, min_term_freq=3, max_batches=None):

        self.logger.info("Opening corpus: %s", self.corpus_path)
        reader = ipc.open_file(self.corpus_path)

        doc_id_counter = 0
        total_batches = reader.num_record_batches
        batches_to_process = min(max_batches, total_batches) if max_batches else total_batches
        self.logger.info("Processing %d/%d batches", batches_to_process, total_batches)

        total_doc_length = 0
        tokenizer_config = self.tokenizer.get_config()

        # <<< Create SQLite forward index
        forward_db_path = os.path.join(self.output_dir, "forward_index.db")
        forward_index = ForwardIndex(db_path=forward_db_path)

        # Keep your existing forward JSONL (if you still need it)
        with open(self.forward_path, "w", encoding="utf-8") as forward_fp:

            for batch_idx in range(batches_to_process):
                batch = reader.get_batch(batch_idx)
                titles = batch.column("title")
                texts = batch.column("text")
                redirects = batch.column("redirect")

                doc_data_list = []
                batch_size = len(titles)
                for i in range(batch_size):
                    title_str = titles[i].as_py()
                    text_str = texts[i].as_py()
                    redirect_val = redirects[i].as_py()
                    redirect_str = redirect_val if redirect_val else ""

                    doc_data_list.append(
                        (doc_id_counter + i, title_str, text_str, redirect_str)
                    )
                    self.stats["total_docs"] += 1

                # Parallel tokenization/filtering
                with Pool(processes=self.num_workers) as pool:
                    process_func = partial(process_document, tokenizer_config=tokenizer_config)
                    results = list(
                        tqdm(
                            pool.imap(process_func, doc_data_list),
                            total=batch_size,
                            desc=f"Batch {batch_idx + 1}/{batches_to_process}",
                        )
                    )

                for result in results:
                    if result is None:
                        self.stats["filtered_docs"] += 1
                        continue

                    doc_id, title_str, tokens = result

                    # <<< Store raw text in SQLite
                    # (We retrieve text_str again by matching doc_id)
                    text_str = next(t[2] for t in doc_data_list if t[0] == doc_id)
                    forward_index.add_document(doc_id, title_str, text_str)

                    # SPIMI indexing (existing)
                    self.indexer.add_document(doc_id, tokens)

                    positions_by_term = defaultdict(list)
                    for pos, tok in enumerate(tokens):
                        positions_by_term[tok].append(pos)

                    forward_fp.write(
                        json.dumps([doc_id, dict(positions_by_term)], ensure_ascii=False) + "\n"
                    )

                    self.doc_map[doc_id] = {"title": title_str, "length": len(tokens)}
                    total_doc_length += len(tokens)
                    self.stats["indexed_docs"] += 1

                doc_id_counter += batch_size

        # <<< Close DB connection at end
        forward_index.close()


        # Finalize indexing blocks
        self.logger.info("Finalizing index blocks...")
        self.indexer.finalize()

        # Calculate statistics
        if self.stats["indexed_docs"] > 0:
            self.stats["avg_doc_length"] = float(
                total_doc_length / self.stats["indexed_docs"]
            )

        # Merge blocks → final_index.json + term_offsets.json
        self.logger.info("Merging index blocks...")
        index_path, term_stats = self.indexer.merge_blocks(
            output_path=os.path.join(self.output_dir, "final_index.json"),
            min_term_freq=min_term_freq,
        )

        # Save all metadata
        self._save_metadata(term_stats)

        self.logger.info("=" * 60)
        self.logger.info("INDEX BUILD COMPLETE!")
        self.logger.info("Workers used: %d", self.num_workers)
        self.logger.info("Total documents: %d", self.stats["total_docs"])
        self.logger.info("Indexed documents: %d", self.stats["indexed_docs"])
        self.logger.info("Filtered documents: %d", self.stats["filtered_docs"])
        self.logger.info(
            "Average document length: %.2f tokens", self.stats["avg_doc_length"]
        )
        self.logger.info("Index saved to: %s", self.output_dir)
        self.logger.info("=" * 60)

    def _save_metadata(self, term_stats):
        # 1) Document mapping
        doc_map_path = os.path.join(self.output_dir, "doc_map.json")
        with open(doc_map_path, "w", encoding="utf-8") as f:
            json.dump(self.doc_map, f, ensure_ascii=False, indent=2)
        self.logger.info("✓ Document map saved (%d docs)", len(self.doc_map))

        # 2) Tokenizer configuration
        tokenizer_config_path = os.path.join(self.output_dir, "tokenizer_config.json")
        with open(tokenizer_config_path, "w", encoding="utf-8") as f:
            json.dump(self.tokenizer.get_config(), f, indent=2)
        self.logger.info("Tokenizer config saved")

        # 3) Index statistics
        stats_path = os.path.join(self.output_dir, "index_stats.json")
        self.stats["vocabulary_size"] = len(term_stats)
        with open(stats_path, "w", encoding="utf-8") as f:
            json.dump(self.stats, f, indent=2)
        self.logger.info("Index statistics saved")

        # 4) Term-level statistics
        term_stats_path = os.path.join(self.output_dir, "term_stats.json")
        with open(term_stats_path, "w", encoding="utf-8") as f:
            json.dump(term_stats, f, ensure_ascii=False, indent=2)
        self.logger.info("Term statistics saved (%d terms)", len(term_stats))