import heapq
import json
import os
from collections import defaultdict


class SPIMIIndexer:
    def __init__(self, block_dir="index_blocks", block_limit=100000):
        self.block_dir = block_dir
        os.makedirs(block_dir, exist_ok=True)
        self.block_limit = block_limit

        self.term_dict = defaultdict(list)
        self.block_count = 0

        # Statistics
        self.total_docs_indexed = 0
        self.total_terms_seen = 0

    def add_document(self, doc_id, tokens):
        token_list = list(tokens)

        for pos, term in enumerate(token_list):
            # إذا نفس الـ doc_id موجود بالفعل
            if self.term_dict[term] and self.term_dict[term][-1][0] == doc_id:
                self.term_dict[term][-1][1].append(pos)
            else:
                self.term_dict[term].append([doc_id, [pos]])

        self.total_docs_indexed += 1
        self.total_terms_seen += len(token_list)

        if len(self.term_dict) > self.block_limit:
            self._write_block()

    def _write_block(self):
        if not self.term_dict:
            return

        block_path = os.path.join(self.block_dir, f"block_{self.block_count}.json")
        with open(block_path, "w", encoding="utf-8") as f:
            for term in sorted(self.term_dict.keys()):
                postings = self.term_dict[term]
                f.write(json.dumps([term, postings], ensure_ascii=False) + "\n")

        print(f"Block {self.block_count} written ({len(self.term_dict)} terms)")
        self.term_dict.clear()
        self.block_count += 1

    def finalize(self):
        if self.term_dict:
            self._write_block()
        print(f"Indexing complete: {self.block_count} blocks created")

    @staticmethod
    def merge_posting_lists(p1, p2):
        
        result = []
        # جمع doc_freq
        result.append(p1[0] + p2[0])

        new_posting_list = dict()
        [new_posting_list.update(d) for d in (p1[1], p2[1])]

        # ترتيب docIDs تصاعديًا
        for doc_id in sorted(new_posting_list.keys()):
            result.append(doc_id)
            term_freq = new_posting_list[doc_id][0]
            result.append(term_freq)
            for i in range(term_freq):
                result.append(new_posting_list[doc_id][1][i])
        return result

    def merge_blocks(self, output_path="final_index.json", min_term_freq=3):
        if self.block_count == 0:
            return None, {}

        block_files = []
        for i in range(self.block_count):
            block_path = os.path.join(self.block_dir, f"block_{i}.json")
            block_files.append(open(block_path, "r", encoding="utf-8"))

        heap = []
        for block_idx, block_file in enumerate(block_files):
            line = block_file.readline()
            if line.strip():
                term, postings = json.loads(line)
                heapq.heappush(heap, (term, postings, block_idx))

        current_term = None
        current_postings = []
        term_stats = {}
        terms_written = 0
        terms_filtered = 0

        with open(output_path, "w", encoding="utf-8") as out_f:
            while heap:
                term, postings, block_idx = heapq.heappop(heap)

                if term == current_term:
                    current_postings.extend(postings)
                else:
                    if current_term is not None:
                        # حساب total_freq
                        total_freq = sum(len(pos_list) for _, pos_list in current_postings)
                        if total_freq >= min_term_freq:
                            out_f.write(json.dumps([current_term, current_postings], ensure_ascii=False) + "\n")
                            term_stats[current_term] = {
                                "doc_freq": len(current_postings),
                                "term_freq": total_freq
                            }
                            terms_written += 1
                        else:
                            terms_filtered += 1

                    current_term = term
                    current_postings = postings

                # قراءة السطر التالي من نفس block
                line = block_files[block_idx].readline()
                if line.strip():
                    next_term, next_postings = json.loads(line)
                    heapq.heappush(heap, (next_term, next_postings, block_idx))

            # كتابة آخر term
            if current_term is not None:
                total_freq = sum(len(pos_list) for _, pos_list in current_postings)
                if total_freq >= min_term_freq:
                    out_f.write(json.dumps([current_term, current_postings], ensure_ascii=False) +"\n")
                    term_stats[current_term] = {
                        "doc_freq": len(current_postings),
                        "term_freq": total_freq
                    }
                    terms_written += 1
                else:
                    terms_filtered += 1

        for f in block_files:
            f.close()

        print("Merge complete!")
        print(f"Terms kept: {terms_written}")
        print(f"Terms filtered: {terms_filtered}")

        return output_path, term_stats
