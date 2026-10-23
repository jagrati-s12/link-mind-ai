from typing import List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from app.core.db import get_db, SessionLocal
from app.core.ssrf import validate_safe_url
from app.models import User, ImportJob, Source
from app.schemas import SourceBulkCreate, ImportJobOut
from app.services.extractor import process_source
from app.api.deps import get_current_user

router = APIRouter(prefix="/imports", tags=["Imports"])

async def run_bulk_import_job(job_id: int, user_id: int, urls: List[str]):
    db: Session = SessionLocal()
    try:
        job = db.query(ImportJob).filter(ImportJob.id == job_id).first()
        if not job:
            return
        
        job.status = "processing"
        db.commit()

        processed_count = 0
        success_count = 0
        errors = []

        for url in urls:
            url_clean = url.strip()
            if not url_clean:
                continue

            is_safe, reason = validate_safe_url(url_clean)
            if not is_safe:
                errors.append(f"{url_clean}: {reason}")
                processed_count += 1
                job.processed_items = processed_count
                db.commit()
                continue

            # Find or create source
            source = db.query(Source).filter(
                Source.user_id == user_id,
                Source.original_url == url_clean
            ).first()

            if not source:
                source = Source(
                    user_id=user_id,
                    original_url=url_clean,
                    source_type="url",
                    title=url_clean,
                    extraction_status="pending"
                )
                db.add(source)
                db.commit()
                db.refresh(source)

            await process_source(db, source.id)
            processed_count += 1
            success_count += 1
            job.processed_items = processed_count
            db.commit()

        job.status = "completed" if success_count > 0 or not errors else "failed"
        job.result_summary = {
            "total": len(urls),
            "successful": success_count,
            "failed": len(errors),
            "errors": errors[:10]
        }
        db.commit()

    except Exception as e:
        job = db.query(ImportJob).filter(ImportJob.id == job_id).first()
        if job:
            job.status = "failed"
            job.error_message = str(e)
            db.commit()
    finally:
        db.close()

@router.post("", response_model=ImportJobOut)
async def start_bulk_import(
    payload: SourceBulkCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    urls = [u.strip() for u in payload.urls if u.strip()]
    if not urls:
        raise HTTPException(status_code=400, detail="Please provide at least one valid URL.")

    job = ImportJob(
        user_id=current_user.id,
        status="pending",
        total_items=len(urls),
        processed_items=0
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    background_tasks.add_task(run_bulk_import_job, job.id, current_user.id, urls)

    return job

@router.get("", response_model=List[ImportJobOut])
def list_import_jobs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return db.query(ImportJob).filter(
        ImportJob.user_id == current_user.id
    ).order_by(ImportJob.created_at.desc()).limit(20).all()

@router.get("/{job_id}", response_model=ImportJobOut)
def get_import_job(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    job = db.query(ImportJob).filter(
        ImportJob.id == job_id,
        ImportJob.user_id == current_user.id
    ).first()
    if not job:
        raise HTTPException(status_code=404, detail="Import job not found.")
    return job
