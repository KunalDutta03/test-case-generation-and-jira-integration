"""
Documents router: upload, list, delete, preview.
"""
import os
import logging
from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Document, Chunk
from app.schemas import DocumentOut, DocumentListOut
from app.config import settings
from app.services.parser import parse_document
from app.services.chunker import chunk_text
from app.services.embedder import embed_texts
from app.services import vector_store

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/documents", tags=["documents"])

ALLOWED_EXTENSIONS = {".txt", ".pdf", ".docx", ".json", ".xlsx", ".xls", ".csv"}


@router.post("/upload", response_model=DocumentOut)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    # Validate extension
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, f"Unsupported file type: {ext}. Allowed: {', '.join(ALLOWED_EXTENSIONS)}")

    # Validate size
    content = await file.read()
    max_bytes = settings.upload_max_size_mb * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(413, f"File too large. Max size: {settings.upload_max_size_mb}MB")

    # Save file
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    safe_name = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{file.filename}"
    file_path = upload_dir / safe_name
    with open(file_path, "wb") as f:
        f.write(content)

    # Create document record
    doc = Document(
        name=file.filename,
        file_type=ext,
        file_path=str(file_path),
        file_size=len(content),
        status="processing",
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    # Process in background
    background_tasks.add_task(_process_document, doc.id, str(file_path), ext, db.bind)
    return doc


def _process_document(document_id: str, file_path: str, ext: str, engine):
    """Background task: parse → chunk → embed → store."""
    from sqlalchemy.orm import Session as S
    with S(engine) as db:
        doc = db.get(Document, document_id)
        if not doc:
            return
        try:
            # Parse
            text = parse_document(file_path, ext)
            doc.preview_text = text[:800]

            # Chunk
            chunks = chunk_text(text)

            # Embed
            texts = [c["content"] for c in chunks]
            embeddings = embed_texts(texts)

            # Store in FAISS
            vector_store.add_document_chunks(
                document_id, chunks, embeddings,
                index_dir=settings.faiss_index_path
            )

            # Store chunk metadata in DB
            for chunk, embedding in zip(chunks, embeddings):
                db_chunk = Chunk(
                    document_id=document_id,
                    content=chunk["content"],
                    chunk_index=chunk["chunk_index"],
                    token_count=chunk["token_count"],
                )
                db.add(db_chunk)

            doc.chunk_count = len(chunks)
            doc.status = "ready"
            db.commit()
            logger.info(f"Document {document_id} processed: {len(chunks)} chunks")

        except Exception as e:
            logger.error(f"Error processing document {document_id}: {e}")
            doc.status = "error"
            doc.error_message = str(e)
            db.commit()


@router.get("", response_model=DocumentListOut)
def list_documents(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    docs = db.query(Document).order_by(Document.uploaded_at.desc()).offset(skip).limit(limit).all()
    total = db.query(Document).count()
    return DocumentListOut(documents=docs, total=total)


@router.get("/{document_id}", response_model=DocumentOut)
def get_document(document_id: str, db: Session = Depends(get_db)):
    doc = db.get(Document, document_id)
    if not doc:
        raise HTTPException(404, "Document not found")
    return doc


@router.delete("/{document_id}")
def delete_document(document_id: str, db: Session = Depends(get_db)):
    doc = db.get(Document, document_id)
    if not doc:
        raise HTTPException(404, "Document not found")
    # Remove FAISS index
    try:
        vector_store.delete_document_index(document_id, settings.faiss_index_path)
    except Exception as e:
        logger.warning(f"Failed to delete FAISS index: {e}")
    # Remove file
    try:
        if os.path.exists(doc.file_path):
            os.remove(doc.file_path)
    except Exception as e:
        logger.warning(f"Failed to delete file: {e}")
    db.delete(doc)
    db.commit()
    return {"message": "Document deleted successfully", "id": document_id}


@router.get("/{document_id}/preview")
def preview_document(document_id: str, db: Session = Depends(get_db)):
    doc = db.get(Document, document_id)
    if not doc:
        raise HTTPException(404, "Document not found")
    return {"id": document_id, "preview_text": doc.preview_text or "No preview available"}
