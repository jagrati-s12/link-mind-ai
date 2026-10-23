import os
import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.core.config import settings
from app.core.ssrf import validate_safe_url
from app.models import User, Source, Resource
from app.schemas import SourceCreateUrl, SourceOut
from app.services.fetcher import extract_document_file
from app.services.extractor import process_source
from app.api.deps import get_current_user

router = APIRouter(prefix="/sources", tags=["Sources"])

@router.post("", response_model=SourceOut)
async def submit_url(
    payload: SourceCreateUrl,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    url = payload.url.strip()
    is_safe, reason = validate_safe_url(url)
    if not is_safe:
        raise HTTPException(status_code=400, detail=f"Invalid or prohibited URL: {reason}")

    # Check for existing source with same URL for this user
    existing_source = db.query(Source).filter(
        Source.user_id == current_user.id,
        Source.original_url == url
    ).first()

    if existing_source:
        # Reprocess or return existing
        if existing_source.extraction_status == "completed":
            res_count = db.query(Resource).filter(Resource.source_id == existing_source.id).count()
            out = SourceOut.from_orm(existing_source)
            out.resource_count = res_count
            return out
        source = existing_source
    else:
        source = Source(
            user_id=current_user.id,
            original_url=url,
            source_type="url",
            title=url,
            extraction_status="pending"
        )
        db.add(source)
        db.commit()
        db.refresh(source)

    # Process extraction
    await process_source(db, source.id)
    db.refresh(source)
    res_count = db.query(Resource).filter(Resource.source_id == source.id).count()
    out = SourceOut.from_orm(source)
    out.resource_count = res_count
    return out

@router.post("/upload", response_model=SourceOut)
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    filename = file.filename or "uploaded_document"
    ext = os.path.splitext(filename)[1].lower()
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format '{ext}'. Allowed: {', '.join(settings.ALLOWED_EXTENSIONS)}"
        )

    saved_name = f"{uuid.uuid4()}_{filename}"
    file_path = os.path.join(settings.UPLOAD_DIR, saved_name)
    content_bytes = await file.read()
    if len(content_bytes) > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=400, detail="File size exceeds maximum limit of 15MB.")

    with open(file_path, "wb") as f:
        f.write(content_bytes)

    # Extract text
    doc_res = extract_document_file(file_path, filename)
    if doc_res.error:
        raise HTTPException(status_code=400, detail=doc_res.error)

    source = Source(
        user_id=current_user.id,
        original_url=None,
        source_type=ext.replace(".", ""),
        title=filename,
        raw_content=doc_res.content,
        mime_type=doc_res.mime_type,
        content_hash=doc_res.content_hash,
        extraction_status="pending"
    )
    db.add(source)
    db.commit()
    db.refresh(source)

    # Process extraction
    await process_source(db, source.id)
    db.refresh(source)

    res_count = db.query(Resource).filter(Resource.source_id == source.id).count()
    out = SourceOut.from_orm(source)
    out.resource_count = res_count
    return out

@router.get("", response_model=List[SourceOut])
def list_sources(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    sources = db.query(Source).filter(Source.user_id == current_user.id).order_by(Source.created_at.desc()).all()
    results = []
    for s in sources:
        count = db.query(Resource).filter(Resource.source_id == s.id).count()
        so = SourceOut.from_orm(s)
        so.resource_count = count
        results.append(so)
    return results

@router.get("/{source_id}", response_model=SourceOut)
def get_source(
    source_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    source = db.query(Source).filter(Source.id == source_id, Source.user_id == current_user.id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found.")
    count = db.query(Resource).filter(Resource.source_id == source.id).count()
    so = SourceOut.from_orm(source)
    so.resource_count = count
    return so

@router.post("/{source_id}/reprocess", response_model=SourceOut)
async def reprocess_source(
    source_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    source = db.query(Source).filter(Source.id == source_id, Source.user_id == current_user.id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found.")
    await process_source(db, source.id)
    db.refresh(source)
    count = db.query(Resource).filter(Resource.source_id == source.id).count()
    so = SourceOut.from_orm(source)
    so.resource_count = count
    return so

@router.delete("/{source_id}")
def delete_source(
    source_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    source = db.query(Source).filter(Source.id == source_id, Source.user_id == current_user.id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found.")
    db.delete(source)
    db.commit()
    return {"status": "success", "message": "Source deleted successfully."}
