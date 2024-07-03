from __future__ import annotations

from pgvector.sqlalchemy import Vector
from datetime import datetime
from sqlalchemy import Index, Column, Integer, String, ForeignKey, text, inspect 
from sqlalchemy.orm import DeclarativeBase, Mapped, MappedAsDataclass, mapped_column



# Define the models
class Base(DeclarativeBase, MappedAsDataclass):
    pass

class Webpage(Base): 
    __tablename__ = "webpages" 
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True) 
    original_url: Mapped[str] = mapped_column()
    link: Mapped[str] = mapped_column()
    title: Mapped[str] = mapped_column()
    content: Mapped[str] = mapped_column()
    date_scraped: Mapped[datetime] = mapped_column()
    current_has: Mapped[str] = mapped_column()

class Doc(Base):
    __tablename__ = "docs"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    doc_id: Mapped[int] = mapped_column()
    chunk_id: Mapped[int] = mapped_column()
    type: Mapped[str] = mapped_column()
    name: Mapped[str] = mapped_column()
    description: Mapped[str] = mapped_column()
    content: Mapped[str] = mapped_column()
    url: Mapped[str] = mapped_column()
    embedding: Mapped[Vector] = mapped_column(Vector(1024)) # GTE-large

    def to_dict(self, include_embedding: bool = False):
        # Manually construct the dictionary
        model_dict = {
            "id": self.id,
            "doc_id": self.doc_id, 
            "chunk_id": self.chunk_id, 
            "type": self.type,
            "name": self.name,
            "description": self.description,
            "content": self.content, 
            "url": self.url, 
        }
        if include_embedding:
            # assuming embedding is a list or similar structure
            model_dict["embedding"] = self.embedding.tolist()
        return model_dict

    def to_str_for_rag(self):
        return f"Name:{self.name} Description:{self.description} Content: {self.content} Type:{self.type}"

    def to_str_for_embedding(self):
        return f"Name: {self.name} Description: {self.description} Content: {self.content} Type: {self.type}"


# Define HNSW index to support vector similarity search through the vector_cosine_ops access method (cosine distance).
index = Index(
    "hnsw_index_for_innerproduct_doc_embedding",
    Doc.embedding,
    postgresql_using="hnsw",
    postgresql_with={"m": 16, "ef_construction": 64},
    postgresql_ops={"embedding": "vector_ip_ops"},
)