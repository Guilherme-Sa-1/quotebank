import sqlite3
from datetime import datetime
import csv
from pathlib import Path

class QuoteDB:
    def __init__(self, db_path=None):
        if not db_path:
            base_dir = Path(__file__).parent.parent
            self.db_path = base_dir / 'data' / 'quotes.db'
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
        else:
            self.db_path = Path(db_path)

        self.conn = sqlite3.connect(str(self.db_path))
        self.create_table()

    def create_table(self):
        query = '''
        CREATE TABLE IF NOT EXISTS quotes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            quote TEXT NOT NULL,
            author TEXT,
            category TEXT,
            source TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )'''
        self.conn.execute(query)
        self.conn.commit()

    def add_quote(self, quote, author='', category='', source=''):
        query = '''
        INSERT INTO quotes (quote, author, category, source, created_at)
        VALUES (?, ?, ?, ?, ?)'''
        self.conn.execute(query, (quote, author, category, source, datetime.now()))
        self.conn.commit()

    def get_quote(self, quote_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM quotes WHERE id=?', (quote_id,))
        return cursor.fetchone()

    def search_quotes(self, search_term):
        cursor = self.conn.cursor()
        query = '''
        SELECT * FROM quotes 
        WHERE quote LIKE ? OR author LIKE ? OR category LIKE ?'''
        search_pattern = f'%{search_term}%'
        cursor.execute(query, (search_pattern, search_pattern, search_pattern))
        return cursor.fetchall()

    def update_quote(self, quote_id, quote, author, category, source):
        query = '''
        UPDATE quotes 
        SET quote=?, author=?, category=?, source=?
        WHERE id=?'''
        self.conn.execute(query, (quote, author, category, source, quote_id))
        self.conn.commit()

    def delete_quote(self, quote_id):
        self.conn.execute('DELETE FROM quotes WHERE id=?', (quote_id,))
        self.conn.commit()

    def get_all_quotes(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM quotes ORDER BY created_at DESC')
        return cursor.fetchall()

    def export_csv(self, filename):
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['ID', 'Quote', 'Author', 'Category', 'Source', 'Created At'])
            for quote in self.get_all_quotes():
                writer.writerow(quote)

    def close(self):
        self.conn.close()