
import json
from collections import Counter
from pathlib import Path


class RelevanceFeedback:
    """
    Builds a pseudo-query from a given document using the forward index.
    forward_index.jsonl format per line:
      [doc_id, {term: [pos, ...], ...}]
    """

    def __init__(self, index_dir="index_data", top_terms=20):
        self.index_dir = Path(index_dir)
        self.forward_path = self.index_dir / "forward_index.jsonl"
        self.top_terms = top_terms
        self._cache = {}
        self._offsets = {}

        # Build doc_id -> offset map (fast random access)
        with open(self.forward_path, "r", encoding="utf-8") as f:
            pos = 0
            while True:
                line = f.readline()
                if not line:
                    break
                try:
                    doc_id = json.loads(line)[0]
                    self._offsets[int(doc_id)] = pos
                except Exception:
                    pass
                pos = f.tell()

    def _get_doc_counter(self, doc_id: int) -> Counter:
        if doc_id in self._cache:
            return self._cache[doc_id]

        with open(self.forward_path, "r", encoding="utf-8") as f:
            off = self._offsets.get(int(doc_id))
            if off is not None:
                f.seek(off)
                line = f.readline()
                if not line:
                    return Counter()
                did, term_positions = json.loads(line)
                if int(did) != int(doc_id):
                    # Fallback scan (should be rare)
                    f.seek(0)
                    for line in f:
                        did2, term_positions = json.loads(line)
                        if int(did2) == int(doc_id):
                            break
                    else:
                        return Counter()
            else:
                # no offset known, scan
                for line in f:
                    did2, term_positions = json.loads(line)
                    if int(did2) == int(doc_id):
                        break
                else:
                    return Counter()

        cnt = Counter({t: len(poss) for t, poss in term_positions.items()})
        self._cache[doc_id] = cnt
        return cnt

    def build_pseudo_query(self, doc_id: int, num_terms: int = None) -> str:
        num_terms = num_terms or self.top_terms
        cnt = self._get_doc_counter(doc_id)
        if not cnt:
            return ""
        terms = [t for t, _ in cnt.most_common(num_terms)]
        return " ".join(terms)

    def find_similar(self, searcher, doc_id: int, top_k: int = 10, num_terms: int = None):
        pseudo = self.build_pseudo_query(doc_id, num_terms)
        if not pseudo:
            return []
        # ask the BM25 searcher
        res = searcher.search(pseudo, top_k=top_k + 1)
        return [r for r in res if r["doc_id"] != doc_id][:top_k]