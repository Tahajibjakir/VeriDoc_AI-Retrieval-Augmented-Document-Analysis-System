import fitz  # PyMuPDF
from app.models.models import Document, DocumentChunk, ChunkType
from sqlalchemy.orm import Session
from app.core.chroma import get_collection
import uuid
import json

def process_document(db: Session, document: Document, file_path: str, job_id: int = None):
    """
    Ingests a document: parses PDF, chunks text, generates embeddings, stores in DB and Chroma.
    Commits page-by-page to prevent database locks and update progress.
    """
    from app.services.jobs import update_job_status
    from app.models.models import JobStatus
    
    # 1. Parse PDF
    doc = fitz.open(file_path)
    total_pages = len(doc)
    
    collection = get_collection()
    
    try:
        for page_num, page in enumerate(doc):
            text = page.get_text()
            
            # Simple page-level chunking for now (parent)
            parent_chunk = DocumentChunk(
                document_id=document.id,
                chunk_text=text,
                chunk_type=ChunkType.PARENT,
                page_number=page_num + 1,
            )
            db.add(parent_chunk)
            db.flush() # Get ID
            
            # Split into child chunks
            paragraphs = text.split('\n\n')
            
            for para in paragraphs:
                if len(para.strip()) < 50:
                    continue
                    
                chunk_id = str(uuid.uuid4())
                
                child_chunk = DocumentChunk(
                    document_id=document.id,
                    parent_section_id=parent_chunk.id,
                    chunk_text=para,
                    chunk_type=ChunkType.CHILD,
                    page_number=page_num + 1,
                    embedding_id=chunk_id
                )
                db.add(child_chunk)
                db.flush() # Get ID for child_chunk before adding to Chroma
                
                # Add to vector DB
                collection.add(
                    documents=[para],
                    metadatas=[{"document_id": document.id, "page": page_num + 1, "chunk_id": child_chunk.id}],
                    ids=[chunk_id]
                )
                
            # Commit after every page to release DB locks
            db.commit()
            
            # Update job progress if job_id is provided
            if job_id:
                progress = int(((page_num + 1) / total_pages) * 100)
                update_job_status(db, job_id, JobStatus.RUNNING, progress=progress)
                
        # Mark document as completed only when all pages are done
        document.status = "COMPLETED"
        db.commit()
        
    except Exception as e:
        # If ingestion fails mid-way, rollback the current page's uncommitted chunks
        db.rollback()
        # Mark document as failed
        document.status = "FAILED"
        db.commit()
        # Note: We keep the already-embedded pages in ChromaDB so we don't lose partial progress,
        # but to cleanly retry we might want to sweep ChromaDB in the future.
        raise e
