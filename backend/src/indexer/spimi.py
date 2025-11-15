# indexer/spimi_indexer.py
import heapq
import json
from collections import defaultdict
from pathlib import Path
from typing import Dict, List


class SPIMIIndexer:
    """
    SPIMI positional index with block flushing + k-way merge.
    - Keeps lexicographic order of terms.
    - Keeps postings sorted by doc_id and positions.
    - Applies min_term_freq at merge time.
    - Emits term_offsets.json for fast on-demand searchers.
    """

    def __init__(self, block_dir: str = "index_blocks", block_limit: int = 100000):
        self.block_dir = Path(block_dir)
        self.block_dir.mkdir(parents=True, exist_ok=True)
        self.block_limit = block_limit

        # in-memory partial dictionary: term -> list[[doc_id, [pos...]], ...]
        self.term_dict: Dict[str, List[List]] = defaultdict(list)
        self.block_count = 0

        # stats
        self.total_docs_indexed = 0
        self.total_terms_seen = 0

    def add_document(self, doc_id: int, tokens):
        """
        Add a document tokens stream (already tokenized) and record positions.
        Positions are indices in the filtered token stream (consistent with query pipeline).
        """
        token_list = list(tokens)
        for pos, term in enumerate(token_list):
            # Fast append; if same doc repeats consecutively for this term, append pos only
            if self.term_dict[term] and self.term_dict[term][-1][0] == doc_id:
                self.term_dict[term][-1][1].append(pos)
            else:
                self.term_dict[term].append([doc_id, [pos]])

        self.total_docs_indexed += 1
        self.total_terms_seen += len(token_list)

        # Flush by number of distinct terms
        if len(self.term_dict) > self.block_limit:
            self._write_block()

    def _write_block(self):
        """
        Write a block as JSONL:
          [term, [[doc_id, [pos...]], ...]]
        Ensures postings sorted by doc_id and positions within the block.
        """
        if not self.term_dict:
            return

        block_path = self.block_dir / f"block_{self.block_count}.jsonl"
        with open(block_path, "w", encoding="utf-8") as f:
            for term in sorted(self.term_dict.keys()):
                postings = self.term_dict[term]
                # sort by doc_id, and ensure positions sorted
                postings_sorted = []
                for did, poss in postings:
                    postings_sorted.append([did, sorted(poss)])
                postings_sorted.sort(key=lambda x: x[0])
                f.write(json.dumps([term, postings_sorted], ensure_ascii=False) + "\n")

        print(f"Block {self.block_count} written ({len(self.term_dict)} terms) -> {block_path}")
        self.term_dict.clear()
        self.block_count += 1

    def finalize(self):
        """Flush last block if present."""
        if self.term_dict:
            self._write_block()
        print(f"Indexing complete: {self.block_count} blocks created")

    def merge_blocks(self, output_path: str = "final_index.jsonl", min_term_freq: int = 3):
        """
        K-way merge for sorted blocks. Produces:
          - final_index.jsonl (JSON Lines; one [term, postings] per line)
          - term_offsets.json  (term -> byte offset into final_index.jsonl)
        Keeps doc_id order ascending; merges duplicate doc entries; applies min_term_freq.
        """
        if self.block_count == 0:
            return None, {}

        # Open all block files
        block_files = []
        for i in range(self.block_count):
            block_path = self.block_dir / f"block_{i}.jsonl"
            block_files.append(open(block_path, "r", encoding="utf-8"))

        # Min-heap by term
        heap = []
        for idx, fp in enumerate(block_files):
            line = fp.readline()
            if line.strip():
                term, postings = json.loads(line)
                heapq.heappush(heap, (term, idx, postings))

        current_term = None
        accum_postings = []  # [[doc_id, [pos...]], ...]

        term_stats = {}
        terms_written = 0
        terms_filtered = 0

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        term_offsets = {}

        with open(output_path, "w", encoding="utf-8") as out_f:
            def flush_term(term: str, postings: List[List]):
                nonlocal terms_written, terms_filtered
                # Merge duplicates by doc_id
                by_doc = defaultdict(list)
                for did, poss in postings:
                    by_doc[did].extend(poss)

                final_postings = []
                total_tf = 0
                for did in sorted(by_doc.keys()):
                    poss = sorted(by_doc[did])
                    total_tf += len(poss)
                    final_postings.append([did, poss])

                if total_tf >= min_term_freq:
                    term_offsets[term] = out_f.tell()
                    out_f.write(json.dumps([term, final_postings], ensure_ascii=False) + "\n")
                    term_stats[term] = {
                        "doc_freq": len(final_postings),
                        "term_freq": total_tf
                    }
                    terms_written += 1
                else:
                    terms_filtered += 1

            while heap:
                term, bidx, postings = heapq.heappop(heap)
                if current_term is None:
                    current_term = term
                    accum_postings = postings
                elif term == current_term:
                    accum_postings.extend(postings)
                else:
                    flush_term(current_term, accum_postings)
                    current_term = term
                    accum_postings = postings

                # advance this block
                nxt = block_files[bidx].readline()
                if nxt.strip():
                    nterm, npost = json.loads(nxt)
                    heapq.heappush(heap, (nterm, bidx, npost))

            if current_term is not None:
                flush_term(current_term, accum_postings)

        for fp in block_files:
            fp.close()

        # Write offsets alongside final index
        offsets_path = output_path.parent / "term_offsets.json"
        with open(offsets_path, "w", encoding="utf-8") as f:
            json.dump(term_offsets, f, ensure_ascii=False)

        print("Merge complete!")
        print(f"Terms kept: {terms_written}")
        print(f"Terms filtered (< min_term_freq): {terms_filtered}")
        print(f"Final index: {output_path}")
        print(f"Term offsets: {offsets_path}")

        return str(output_path), term_stats