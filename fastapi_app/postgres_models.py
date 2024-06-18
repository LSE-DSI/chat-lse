from __future__ import annotations

from dataclasses import asdict

from pgvector.sqlalchemy import Vector
from sqlalchemy import Index, JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, MappedAsDataclass, mapped_column


# Define the models
class Base(DeclarativeBase, MappedAsDataclass):
    pass


from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.orm import declarative_base, relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.types import JSON


Base = declarative_base()

class Item(Base):
    __tablename__ = 'items'
    id = Column(Integer, primary_key=True, autoincrement=True)
    type = Column(String)
    name = Column(String)
    description = Column(String)
    link = Column(String)
    # Relationship to embeddings
    embeddings = relationship("Embedding", back_populates="item")

class Embedding(Base):
    __tablename__ = 'embeddings'
    id = Column(Integer, primary_key=True, autoincrement=True)
    item_id = Column(Integer, ForeignKey('items.id'))
    vector = Column(Vector)  # pgvector type for efficient vector operations
    item = relationship("Item", back_populates="embeddings")

    
    def to_str_for_rag(self):
        return f"Name:{self.name} Description:{self.description} Type:{self.type} Link:{self.link}" 

    def to_str_for_embedding(self):
        return f"Name: {self.name} Description: {self.description} Type: {self.type}"


# Define HNSW index to support vector similarity search through the vector_cosine_ops access method (cosine distance).
index = Index(
    "hnsw_index_for_innerproduct_item_embedding",
    Item.embeddings,
    postgresql_using="hnsw",
    postgresql_with={"m": 16, "ef_construction": 64},
    postgresql_ops={"embedding": "vector_ip_ops"},
)