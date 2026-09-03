from sqlalchemy import Column, Integer, Text, String
from app.db.database import Base


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, index=True)

    filename = Column(String, nullable=False)

    chunk_text = Column(Text, nullable=False)

    embedding = Column(Text, nullable=False)