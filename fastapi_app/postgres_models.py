from __future__ import annotations

from pgvector.sqlalchemy import Vector
from datetime import datetime
from sqlalchemy import Index 
from sqlalchemy.orm import DeclarativeBase, Mapped, MappedAsDataclass, mapped_column



# Define the models
class Base(DeclarativeBase, MappedAsDataclass):
    pass

class Doc(Base):
    __tablename__ = "lse_doc"
    id: Mapped[str] = mapped_column(primary_key=True)
    doc_id: Mapped[str] = mapped_column()
    type: Mapped[str] = mapped_column()
    url: Mapped[str] = mapped_column()
    title: Mapped[str] = mapped_column()
    content: Mapped[str] = mapped_column()
    date_scraped: Mapped[datetime] = mapped_column()

    def to_dict(self, include_embedding: bool = False):
        # Manually construct the dictionary
        model_dict = {
            "id": self.id,
            "doc_id": self.doc_id, 
            "type": self.type,
            "url": self.url, 
            "title": self.title,
            "content": self.content, 
        }
        return model_dict

    def to_str_for_rag(self):
        return f"Title: {self.title} URL: {self.url} Content: {self.content} Type:{self.type}"

    def to_str_for_embedding(self):
        return f"Title: {self.title} URL: {self.url} Content: {self.content} Type: {self.type}"
