import os
import sqlite3
from typing import Optional


class ForwardIndex:
    def __init__(self, db_path="forward_index.db"):
        """Initialize or connect to the SQLite forward index."""
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self.create_table()

    def create_table(self):
        """Create the table if it doesn't already exist."""
        cur = self.conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                doc_id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                text  TEXT NOT NULL
            )
        """)
        self.conn.commit()

    def add_document(self, doc_id: int, title: str, text: str):
        """Insert or update a document in the forward index."""
        cur = self.conn.cursor()
        cur.execute(
            "INSERT OR REPLACE INTO documents (doc_id, title, text) VALUES (?, ?, ?)",
            (doc_id, title, text)
        )
        self.conn.commit()

    def get_text_by_id(self, doc_id: int) -> Optional[str]:
        """Retrieve a document’s full text by ID."""
        cur = self.conn.cursor()
        cur.execute("SELECT text FROM documents WHERE doc_id=?", (doc_id,))
        row = cur.fetchone()
        return row[0] if row else None

    def get_text_by_title(self, title: str) -> Optional[str]:
        """Retrieve a document’s full text by title."""
        cur = self.conn.cursor()
        cur.execute("SELECT text FROM documents WHERE title=?", (title,))
        row = cur.fetchone()
        return row[0] if row else None

    def close(self):
        """Close the database connection."""
        self.conn.close()
