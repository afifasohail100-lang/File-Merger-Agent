import sqlite3
import json
from datetime import datetime

DB_FILE = "books_database.db"

def get_db_connection():
    """Create a connection to the SQLite database."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def create_tables():
    """Create the necessary tables if they do not exist."""
    conn = get_db_connection()
    
    # Create books table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author TEXT,
            total_pages INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            json_data TEXT  -- Store full JSON for backup
        );
    """)
    
    # Create pages table for structured querying
    conn.execute("""
        CREATE TABLE IF NOT EXISTS pages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            book_id INTEGER NOT NULL,
            page_number INTEGER NOT NULL,
            text_count INTEGER DEFAULT 0,
            image_count INTEGER DEFAULT 0,
            FOREIGN KEY (book_id) REFERENCES books (id) ON DELETE CASCADE
        );
    """)
    
    conn.commit()
    conn.close()
    print("✅ Database tables created/verified")

def save_book(book_data):
    """Save a book to the database."""
    conn = get_db_connection()
    
    # Convert book_data to JSON string for storage
    json_str = json.dumps(book_data)
    
    # Insert book
    cursor = conn.execute("""
        INSERT INTO books (title, author, total_pages, json_data)
        VALUES (?, ?, ?, ?)
    """, (book_data['title'], book_data['author'], book_data['total_pages'], json_str))
    
    book_id = cursor.lastrowid
    
    # Insert pages
    for page in book_data['pages']:
        conn.execute("""
            INSERT INTO pages (book_id, page_number, text_count, image_count)
            VALUES (?, ?, ?, ?)
        """, (book_id, page['page_number'], page['text_count'], page['image_count']))
    
    conn.commit()
    conn.close()
    return book_id

def save_merged_books(merged_data):
    """Save merged books data to database."""
    conn = get_db_connection()
    
    # Create a record for the merge operation
    cursor = conn.execute("""
        INSERT INTO books (title, author, total_pages, json_data)
        VALUES (?, ?, ?, ?)
    """, (
        f"Merged Collection ({merged_data['total_books']} books)",
        "Multiple Authors",
        sum(book['total_pages'] for book in merged_data['books']),
        json.dumps(merged_data)
    ))
    
    merge_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return merge_id

def get_all_books():
    """Retrieve all books from database."""
    conn = get_db_connection()
    books = conn.execute("SELECT id, title, author, total_pages, created_at FROM books ORDER BY created_at DESC").fetchall()
    conn.close()
    return books

def get_book_by_id(book_id):
    """Retrieve a specific book by ID."""
    conn = get_db_connection()
    result = conn.execute("SELECT json_data FROM books WHERE id = ?", (book_id,)).fetchone()
    conn.close()
    
    if result:
        return json.loads(result['json_data'])
    return None