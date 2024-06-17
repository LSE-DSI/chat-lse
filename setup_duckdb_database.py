import duckdb

conn = duckdb.connect(database=':memory:')  # or specify a file

def create_table():
    conn.execute('''
    CREATE TABLE lse_documents (
        id INTEGER PRIMARY KEY,
        title TEXT,
        content TEXT,
        vector TEXT
    )
    ''')

def insert_document(id, title, content, vector):
    conn.execute('INSERT INTO lse_documents VALUES (?, ?, ?, ?)', (id, title, content, vector))
