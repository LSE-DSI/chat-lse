from setup_duckdb_database.py import create_table, insert_document

create_table()
insert_document(1, 'Document 1', 'This is the content of document 1', 'vector1')
insert_document(2, 'Document 2', 'This is the content of document 2', 'vector2')
