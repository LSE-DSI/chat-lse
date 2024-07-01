from __future__ import annotations

from pgvector.sqlalchemy import Vector
from sqlalchemy import Index, Column, Integer, String, ForeignKey, text 
from sqlalchemy.orm import DeclarativeBase, Mapped, MappedAsDataclass
from sqlalchemy.orm import declarative_base, relationship, Mapped

from postgres_engine import create_postgres_engine_from_env_sync


# Define the models
class Base(DeclarativeBase, MappedAsDataclass):
    pass


Base = declarative_base()


class Doc(Base):
    __tablename__ = "docs"
    id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True)
    doc_id: Mapped[int] = Column(Integer)
    chunk_id: Mapped[int] = Column(Integer)
    type: Mapped[str] = Column(String)
    name: Mapped[str] = Column(String)
    description: Mapped[str] = Column(String)
    content: Mapped[str] = Column(String)
    url: Mapped[str] = Column(String)
    embedding: Mapped[Vector] = Column(Vector(1024)) # GTE-large

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
    "hnsw_index_for_innerproduct_item_embedding",
    Doc.embedding,
    postgresql_using="hnsw",
    postgresql_with={"m": 16, "ef_construction": 64},
    postgresql_ops={"embedding": "vector_ip_ops"},
)