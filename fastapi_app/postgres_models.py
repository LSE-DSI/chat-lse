from __future__ import annotations

from pgvector.sqlalchemy import Vector
from sqlalchemy.types import Column, Integer, String, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, MappedAsDataclass
from sqlalchemy.orm import declarative_base, relationship, Mapped
from sqlalchemy import Index, ForeignKey

# Define the models
class Base(DeclarativeBase, MappedAsDataclass):
    pass


Base = declarative_base()


class Document(Base):
    __tablename__ = "documents"
    id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True)
    type: Mapped[str] = Column(String) # Either HTML or PDF
    title: Mapped[str] = Column(String)
    description: Mapped[str] = Column(String)
    content: Mapped[str] = Column(String)
    url: Mapped[str] = Column(String)

    # Relationship to link PDFs to their chunks
    items: Mapped[list["Item"]] = relationship("Item", back_populates="pdf")

class Item(Base):
    __tablename__ = "items"
    id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True)
    # Type indicates whether this Item is a 
    # - Chunk (when using SentenceSplitter) or 
    # - A Semantic Section (e.g. 'Webpage Div', 'PDF page')
    type: Mapped[str] = Column(String) 
    name: Mapped[str] = Column(String)
    description: Mapped[str] = Column(String)
    embedding: Mapped[Vector] = Column(Vector(1024))

    # Foreign Key to reference the PDF table
    doc_id: Mapped[int] = Column(Integer, ForeignKey("documents.id"))
    doc: Mapped[Document] = relationship("documents", back_populates="items")

    def to_dict(self, include_embedding: bool = False):
        # Manually construct the dictionary
        model_dict = {
            "id": self.id,
            "type": self.type,
            "name": self.name,
            "description": self.description,
            "doc_id": self.doc_id,
        }
        if include_embedding:
            # assuming embedding is a list or similar structure
            model_dict["embedding"] = self.embedding.tolist()
        return model_dict

    def to_str_for_rag(self):
        return f"Name:{self.name} Description:{self.description} URL:{self.url} Type:{self.type}"

    def to_str_for_embedding(self):
        return f"Name: {self.name} Description: {self.description} Type: {self.type}"


# Define HNSW index to support vector similarity search through the vector_cosine_ops access method (cosine distance).
index = Index(
    "hnsw_index_for_innerproduct_item_embedding",
    Item.embedding,
    postgresql_using="hnsw",
    postgresql_with={"m": 16, "ef_construction": 64},
    postgresql_ops={"embedding": "vector_ip_ops"},
)

    