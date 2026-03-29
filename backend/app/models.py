import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, Float, Text, DateTime,
    ForeignKey, JSON, Boolean, Enum as SAEnum
)
from sqlalchemy.orm import relationship
from app.database import Base


def gen_uuid():
    return str(uuid.uuid4())


class Document(Base):
    __tablename__ = "documents"

    id = Column(String, primary_key=True, default=gen_uuid)
    name = Column(String(255), nullable=False)
    file_type = Column(String(20), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)  # bytes
    status = Column(String(50), default="processing")  # processing | ready | error
    chunk_count = Column(Integer, default=0)
    preview_text = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    chunks = relationship("Chunk", back_populates="document", cascade="all, delete-orphan")
    test_cases = relationship("TestCase", back_populates="document", cascade="all, delete-orphan")


class Chunk(Base):
    __tablename__ = "chunks"

    id = Column(String, primary_key=True, default=gen_uuid)
    document_id = Column(String, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    content = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    token_count = Column(Integer, default=0)
    embedding_vector = Column(JSON, nullable=True)  # stored as list for fallback
    created_at = Column(DateTime, default=datetime.utcnow)

    document = relationship("Document", back_populates="chunks")


class TestCase(Base):
    __tablename__ = "test_cases"

    id = Column(String, primary_key=True, default=gen_uuid)
    document_id = Column(String, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    feature = Column(String(500), nullable=False)
    scenario = Column(String(500), nullable=False)
    gherkin_text = Column(Text, nullable=False)
    domain = Column(String(50), default="Web")  # Web | API | Mobile | Database | Security
    status = Column(String(50), default="draft")  # draft | approved | rejected | pending_edit
    jira_url = Column(String(500), nullable=True)
    jira_key = Column(String(100), nullable=True)
    reviewer_comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    document = relationship("Document", back_populates="test_cases")
    audit_logs = relationship("AuditLog", back_populates="test_case", cascade="all, delete-orphan")


class JiraConfig(Base):
    __tablename__ = "jira_config"

    id = Column(String, primary_key=True, default=gen_uuid)
    base_url = Column(String(500), nullable=False)
    project_key = Column(String(50), nullable=False)
    issue_type = Column(String(100), default="Task")
    email = Column(String(200), nullable=False)
    api_token_encrypted = Column(Text, nullable=False)  # store token (in prod, use Key Vault)
    labels = Column(JSON, default=["auto-generated"])
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(String, primary_key=True, default=gen_uuid)
    entity_type = Column(String(50), nullable=False)  # test_case | document
    entity_id = Column(String, nullable=False)
    test_case_id = Column(String, ForeignKey("test_cases.id", ondelete="CASCADE"), nullable=True)
    action = Column(String(50), nullable=False)  # approved | rejected | edited | generated
    actor = Column(String(200), default="qa_user")
    previous_status = Column(String(50), nullable=True)
    new_status = Column(String(50), nullable=True)
    comment = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    test_case = relationship("TestCase", back_populates="audit_logs")
