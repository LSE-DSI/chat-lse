import duckdb
import os
import PyPDF2
from sentence_transformers import SentenceTransformer
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List

# Define FastAPI app
app = FastAPI()

# Check and print current working directory
print(f"Current Working Directory: {os.getcwd()}")

# Define database file path
db_path = 'mydb.duckdb'

# Delete the WAL file if it exists
wal_path = db_path + '.wal'
if os.path.exists(wal_path):
    os.remove(wal_path)

# Connect to DuckDB (use a file-based database)
conn = duckdb.connect(database=db_path)

# Install and load the VSS extension
conn.execute("INSTALL vss")
conn.execute("LOAD vss")

# Enable experimental persistence for HNSW indexes after loading VSS extension
conn.execute("SET hnsw_enable_experimental_persistence=true")

# Drop the existing table if it exists to ensure schema changes take effect
conn.execute('DROP TABLE IF EXISTS embeddings')

# Create table with vector embeddings (384-dimensional)
conn.execute('''
CREATE TABLE embeddings (
    id INTEGER PRIMARY KEY,
    title TEXT,
    content TEXT,
    vec FLOAT[384]
)
''')

# Create HNSW index on the vector column
conn.execute('CREATE INDEX hnsw_index ON embeddings USING HNSW (vec)')

# Clear existing data to avoid duplicate primary key errors
conn.execute('DELETE FROM embeddings')

# Function to insert documents
def insert_document(id, title, content, vec):
    conn.execute('INSERT INTO embeddings (id, title, content, vec) VALUES (?, ?, ?, ?)', (id, title, content, vec))

# Extract text from PDFs using PyPDF2
def extract_text_from_pdf(pdf_path):
    text = ""
    with open(pdf_path, "rb") as file:
        reader = PyPDF2.PdfReader(file)
        for page in reader.pages:
            text += page.extract_text()
    return text

# Paths to PDF files
exam_procedures_path = '/Users/akshsabherwal/Desktop/Exam-Procedures-for-Candidates.pdf'
exam_timetable_path = '/Users/akshsabherwal/Desktop/Spring-Exam-Timetable-2024-Final.pdf'

# Print paths for verification
print(f"Exam Procedures Path: {exam_procedures_path}")
print(f"Spring Exam Timetable Path: {exam_timetable_path}")

# Extract text from the provided PDFs using relative paths
exam_procedures_text = extract_text_from_pdf(exam_procedures_path)
exam_timetable_text = extract_text_from_pdf(exam_timetable_path)

# Verify extraction
print(f"Exam Procedures Text: {exam_procedures_text[:500]}")  # Print first 500 characters
print(f"Spring Exam Timetable Text: {exam_timetable_text[:500]}")  # Print first 500 characters

# Convert text to embeddings
model = SentenceTransformer('all-MiniLM-L6-v2')

exam_procedures_embedding = model.encode(exam_procedures_text)
exam_timetable_embedding = model.encode(exam_timetable_text)

# Inserting the documents
insert_document(1, 'Exam Procedures for Candidates', exam_procedures_text, exam_procedures_embedding.tolist())
insert_document(2, 'Spring Exam Timetable 2024', exam_timetable_text, exam_timetable_embedding.tolist())

# Define models for request bodies
class SearchRequest(BaseModel):
    keyword: str
    query_vector: List[float]

class TextToVectorRequest(BaseModel):
    text: str

# FastAPI route for text to vector conversion
@app.post("/convert-to-vector")
async def convert_to_vector(request: TextToVectorRequest):
    try:
        query_vector = model.encode(request.text).tolist()
        return {"query_vector": query_vector}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# FastAPI route for searching
@app.post("/search")
async def search(request: SearchRequest):
    try:
        keyword_results = keyword_search(request.keyword)
        vector_results = vector_search(request.query_vector)

        results_dict = {result[0]: result for result in keyword_results}
        for result in vector_results:
            if result[0] not in results_dict:
                results_dict[result[0]] = result

        combined_results = list(results_dict.values())
        combined_results.sort(key=lambda x: x[3] if len(x) > 3 else float('inf'))

        return combined_results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def keyword_search(keyword):
    query = '''
    SELECT id, title, content FROM embeddings
    WHERE title ILIKE ? OR content ILIKE ?
    '''
    return conn.execute(query, [f'%{keyword}%', f'%{keyword}%']).fetchall()

def vector_search(query_vector):
    query_vector_str = ', '.join(map(str, query_vector))
    query = f'''
    SELECT id, title, content, array_distance(vec, ARRAY[{query_vector_str}]::FLOAT[384]) as distance
    FROM embeddings
    ORDER BY distance
    LIMIT 3
    '''
    return conn.execute(query).fetchall()

def unified_search(keyword, query_vector):
    keyword_results = keyword_search(keyword)
    vector_results = vector_search(query_vector)

    # Convert results to a dictionary for easier combination and elimination of duplicates
    results_dict = {result[0]: result for result in keyword_results}
    for result in vector_results:
        if result[0] not in results_dict:
            results_dict[result[0]] = result

    # Combine and sort results (you can choose your own sorting strategy)
    combined_results = list(results_dict.values())
    combined_results.sort(key=lambda x: x[3] if len(x) > 3 else float('inf'))

    return combined_results

# Example usage
keyword = "exam"
query_vector = model.encode("exam procedures").tolist()  # Replace with the actual query vector
results = unified_search(keyword, query_vector)
for result in results:
    print(result)
