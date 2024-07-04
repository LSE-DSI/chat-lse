from __future__ import annotations

from pgvector.sqlalchemy import Vector
from datetime import datetime
from sqlalchemy import Index, Column, Integer, String, ForeignKey, text, inspect 
from sqlalchemy.orm import DeclarativeBase, Mapped, MappedAsDataclass, mapped_column



# Define the models
class Base(DeclarativeBase, MappedAsDataclass):
    pass

class Doc(Base):
    __tablename__ = "lse_doc"
    id: Mapped[str] = mapped_column(primary_key=True, autoincrement=True)
    doc_id: Mapped[str] = mapped_column()
    chunk_id: Mapped[str] = mapped_column()
    type: Mapped[str] = mapped_column()
    url: Mapped[str] = mapped_column()
    title: Mapped[str] = mapped_column()
    content: Mapped[str] = mapped_column()
    date_scraped: Mapped[datetime] = mapped_column()
    embedding: Mapped[Vector] = mapped_column(Vector(1024)) # GTE-large

    def to_dict(self, include_embedding: bool = False):
        # Manually construct the dictionary
        model_dict = {
            "id": self.id,
            "doc_id": self.doc_id, 
            "chunk_id": self.chunk_id, 
            "type": self.type,
            "url": self.url, 
            "title": self.title,
            "content": self.content, 
        }
        if include_embedding:
            # assuming embedding is a list or similar structure
            model_dict["embedding"] = self.embedding.tolist()
        return model_dict

    def to_str_for_rag(self):
        return f"Title:{self.title} URL: {self.url} Content: {self.content} Type:{self.type}"

    def to_str_for_embedding(self):
        return f"Title: {self.title} URL: {self.url} Content: {self.content} Type: {self.type}"


# Define HNSW index to support vector similarity search through the vector_cosine_ops access method (cosine distance).
index = Index(
    "hnsw_index_for_innerproduct_doc_embedding",
    Doc.embedding,
    postgresql_using="hnsw",
    postgresql_with={"m": 16, "ef_construction": 64},
    postgresql_ops={"embedding": "vector_ip_ops"},
)