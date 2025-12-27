Searchio

Portuguese Wikipedia Search Engine




Overview

Searchio is a complete Information Retrieval (IR) system.
It integrates a FastAPI backend and a Flutter-based web interface, enabling real-time search and ranking over millions of Portuguese Wikipedia articles.
The project provides practical experience with:

	•	Document parsing and tokenization
	
	•	Indexing using SPIMI
	
	•	Search ranking via BM25
	
	•	Relevance feedback
	
	•	Web integration using FastAPI + Flutter Web

⸻⸻⸻⸻⸻⸻⸻⸻⸻⸻⸻⸻

Project Structure

```text
├── backend/
│   ├── core/
│   │   ├── limit_memory.py       # Memory monitor (2GB limit)
│   │   ├── logging.py            # Custom logger
│   │   ├── model.py              # Base models
│   ├── entrypoints/
│   │   ├── asgi.py               # ASGI entrypoint (run FastAPI here)
│   │   ├── cli.py                # CLI for indexing
│   │   ├── server.py             # Uvicorn server setup
│   │   ├── routes/
│   │   │   ├── healthcheck.py    # API health endpoint
│   │   │   ├── search.py         # Main search routes
│   │   │   ├── model.py          # Response models
│   ├── src/
│   │   ├── indexer/
│   │   │   ├── spimi.py          # SPIMI indexing algorithm
│   │   │   ├── tokenizer.py      # Tokenizer with Portuguese stemmer
│   │   ├── searcher/
│   │   │   ├── bm25_searcher.py  # BM25 ranking implementation
│   │   │   ├── relevance_feedback.py # Similar document retrieval
│   │   │   ├── demo.py           # Test demo search
│   │   ├── corpus_loader.py      # Corpus loader using PyArrow
│   ├── index_data/               # Final indexed data
│   │   ├── blocks/               # Partial SPIMI blocks
│   │   ├── doc_map.json
│   │   ├── final_index.json
│   │   ├── forward_index.db
│   │   ├── forward_index.json
│   │   ├── index_stats.json
│   │   ├── term_offsets.json
│   │   ├── term_stats.json
│   │   ├── tokenizer_config.json
│   │   └── bm25_params.json
│   ├── requirements.txt          # Dependencies
│   └── pyproject.toml
│
├── web/                          # Flutter web client
│   ├── lib/
│   │   ├── main.dart
│   │   ├── constant/
│   │   │   └── app_colors.dart
│   │   ├── services/
│   │   │   └── api_service.dart  # Connects Flutter → FastAPI
│   │   ├── widgets/
│   │   │   ├── search_page.dart
│   │   │   ├── document_detail_page.dart
│   │   │   └── results_list.dart
│   ├── .firebaserc
│   ├── build/
│   └── pubspec.yaml
│
└── README.md
```
⸻⸻⸻⸻⸻⸻⸻⸻⸻⸻

How to Run
1. Clone the Repository

	git clone https://github.com/detiuaveiro/practical-assignments-pri_g15.git

2. Place the Corpus File
	
	Download the Portuguese Wikipedia dataset "ptwiki-articles-with-redirects.arrow", from this link:
	https://www.dropbox.com/scl/fi/5jgmnyb6r6fqz1jheqogn/ptwiki-articles-with-redirects.arrow?rlkey=fp888qbb0v1urffhw5lcqlppd&st=prqkboqd&dl=0
	and place it inside the Assignment 1/ directory, next to the backend/ folder like this:
	```text
	├── backend/
	├── web/
	└── ptwiki-articles-with-redirects.arrow
    ```
4. Set up the environment

   cd backend
   
   python -m venv venv
   
   source venv/bin/activate
   
   pip install -r requirements.txt




5. Build the Index

	python -m backend.entrypoints.cli
	This will:
   
	•	Parse and tokenize each document
	
	•	Build the inverted index using SPIMI
	
	•	Merge partial blocks
	
	•	Save the index into /index_data/

   Memory usage will not exceed 2GB, verified via limit_memory.py.



6. Run the API Server

	Run the backend using:
  
	python -m uvicorn backend.entrypoints.asgi:app --reload

  	This starts the FastAPI backend at:
  
  	-> http://127.0.0.1:8000￼

	API Documentation is available at:

	-> http://127.0.0.1:8000/docs￼




7. Run the Flutter Web App

	Open a new terminal and run:
  
	cd web
	
	flutter run -d chrome
	
	The Flutter interface will connect automatically to the FastAPI endpoints and provide:

	•	Real-time BM25 search
	
	•	Document detail viewing
	
	•	Relevance feedback (“find similar documents”)
	
	•	A clean, minimal UI for query exploration



Key Features

	•	Fast search (<1s) for millions of documents
	
	•	BM25 ranking with tunable parameters (k1=1.2, b=0.75)
	
	•	Relevance feedback – find similar documents by doc_id
	
	•	Integrated backend + frontend (FastAPI ↔ Flutter)
	
	•	Efficient indexing with SPIMI and <2GB memory usage
	
	•	Portuguese tokenization (lowercasing, stemming, stopword removal)



Output Files (index_data/)

| File | Description |
|------|--------------|
| `blocks/` | Temporary SPIMI blocks generated during partial indexing |
| `final_index.json` | Final merged inverted index (term → postings) |
| `doc_map.json` | Mapping of document IDs to Wikipedia page titles |
| `forward_index.json` / `forward_index.db` | Forward index: terms associated with each document |
| `term_offsets.json` | Byte offsets for efficient term lookup in the index |
| `term_stats.json` | Term frequency and document occurrence statistics |
| `index_stats.json` | Global statistics about the indexed collection |
| `tokenizer_config.json` | Configuration of the tokenizer (stemming, stopwords, min_len, etc.) |
| `bm25_params.json` | Stores BM25 hyperparameters (`k1`, `b`) used for ranking |



Design Summary

| Component | Description |
|------------|--------------|
| **Corpus Reader** | Efficiently loads `.arrow` dataset using **PyArrow**, reading only the necessary columns to minimize memory usage |
| **Tokenizer** | Implements **Portuguese stemming**, stopword removal, lowercasing, and token length filtering via **NLTK** |
| **Indexing Algorithm** | Uses **SPIMI (Single-Pass In-Memory Indexing)** to build a positional inverted index under a 2GB memory limit |
| **Memory Limit** | Enforced through a custom monitor (`limit_memory.py`) that terminates execution above 2GB |
| **Ranking Model** | Implements **BM25** scoring with configurable parameters (`k1=1.2`, `b=0.75`) |
| **Relevance Feedback** | Allows finding similar documents based on vector similarity from indexed data |
| **Backend** | **FastAPI**-based REST API served via `asgi.py` (Uvicorn ASGI server) |
| **Frontend** | **Flutter Web** client connected to FastAPI, providing live search and document visualization |
| **Storage Format** | Compact **JSON + SQLite hybrid** for index persistence and quick loading |
| **Performance** | Achieves sub-second query response for over 1M+ indexed documents |











