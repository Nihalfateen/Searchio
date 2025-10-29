# Searchio
 Searchio is a full-featured Information Retrieval (IR) system designed for indexing and searching a large document collection. This project was developed as part of the PRI 2025 course at the University of Aveiro. It provides hands-on experience with core IR concepts including document parsing, tokenization, indexing, and search ranking models.


# Overview
This project implements an **Information Retrieval (IR) Indexer** for the Portuguese Wikipedia corpus. 
It parses, tokenizes, and indexes approximately 2.7 million documents efficiently, respecting a 2GB memory limit using the SPIMI algorithm.


## Project Structure

src/
├─ indexer/
│  ├─ __init__.py        # Makes 'indexer' a package
│  ├─ indexer.py         # Main IndexBuilder class
│  ├─ spimi.py           # SPIMIIndexer for building inverted index
│  ├─ tokenizer.py       # Tokenizer with Portuguese stemmer & stopwords
├─ entrypoints/
│  ├─ cli.py             # CLI to run the indexer


## How it Works
1. **PyArrow** reads the `.arrow` corpus efficiently in columnar format (reads only 'text' column).  
2. **Tokenizer** processes each document:
   - Converts text to lowercase
   - Removes Portuguese stopwords
   - Applies stemming
   - Ignores tokens shorter than `min_len`
3. **SPIMIIndexer**:
   - Builds a positional inverted index in memory (`term_dict`)
   - Writes partial JSON blocks to disk when memory reaches `block_limit`
     why we choose the block_limit to be 100000 ?
     first to not exceed the memory limitation 2GB still why?
     Number of terms = 100,000
     Average term length + overhead ≈ 20 bytes
     Average postings per term = 5 × 16 = 80 bytes
     Memory per term ≈ 20 + 80 = 100 bytes
     Total memory = 100,000 × 100 ≈ 10,000,000 bytes ≈ 10 MB
     **This shows that with 100,000 terms per block, the memory usage is well below the 2GB limit**
   - Merges blocks and filters out terms with frequency < `min_term_freq`
4. **Output**:
   - `final_index.json` → inverted index
   - `doc_map.json` → doc_id to title mapping
   - `tokenizer_config.json` → tokenizer settings

## How to Run
1- if yuou want to download the wikipedia file you can check this link
https://www.dropbox.com/scl/fi/5jgmnyb6r6fqz1jheqogn/ptwiki-articles-with-redirects.arrow?rlkey=fp888qbb0v1urffhw5lcqlppd&st=prqkboqd&dl=0


2 - Install dependencies:
```bash
pip install pyarrow nltk tqdm

3 - Download NLTK stopwords:
import nltk
nltk.download('stopwords')
4 - Run the indexer:
python -m backend.entrypoints.cli

5 - Monitor progress via tqdm. Ensure RAM < 2GB during execution.


**Indexing System Flowchart**

Corpus: ptwiki-articles-with-redirects.arrow
(Wikipedia ~2.7M documents)
│
│  (1) PyArrow: Read the file
│     - Read only the needed column (Text)
│     - Keeps memory usage low
▼
Table (PyArrow Table)
- columns: ['title', 'text', 'out_links', 'redirect']
- RAM: small because it is columnar
│
│  (2) IndexBuilder.build_index()
│     - For each document (doc_id, text)
│
│    ├─ Tokenizer.tokenize(text)
│    │   - lowercase
│    │   - remove stopwords
│    │   - stemming
│    │   - ignore short words (< min_len)
│    ▼
│    List of tokens
│
│    ├─ SPIMIIndexer.add_document(doc_id, tokens)
│    │   - For each token: term_dict[token].append((doc_id, position))##positional index
│    │   - If len(term_dict) > block_limit → SPIMIIndexer._write_block()##Exceeded Block_limit
│    │
│    ▼
│    Partial Blocks (JSON) on Disk
│
└─ After all documents: SPIMIIndexer.finalize()
      - Save remaining data in term_dict
      - RAM: term_dict cleared after each block

┌─ SPIMIIndexer.merge_blocks(min_term_freq=3)
│    - Merge all partial blocks
│    - Filter out low-frequency terms
│    ▼
final_index.json
- Each word: posting list [(doc_id, position), ...]
- Ready for searching
- RAM: may be large during merge, but 2GB limit is not enforced for search


