from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.models import User, CourseProgress, Resource
from app.schemas import (
    CourseProgressOut, CourseProgressCreate, CourseProgressUpdate
)
from app.api.deps import get_current_user
from app.api.v1.resources import build_resource_out

router = APIRouter(prefix="/course-tracker", tags=["Course Tracker"])

@router.get("", response_model=List[CourseProgressOut])
def list_course_progress(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Auto-sync: Ensure all saved courses & certifications have a CourseProgress entry
    untracked_courses = db.query(Resource).filter(
        Resource.user_id == current_user.id,
        Resource.type.in_(["course", "certification"]),
        Resource.is_archived == False,
        ~Resource.id.in_(
            db.query(CourseProgress.resource_id).filter(CourseProgress.user_id == current_user.id)
        )
    ).all()

    if untracked_courses:
        for c in untracked_courses:
            new_cp = CourseProgress(
                user_id=current_user.id,
                resource_id=c.id,
                status="In Progress",
                progress_percentage=0,
                current_module="Getting Started",
                target_completion_date=c.deadline,
                notes=c.notes or ""
            )
            db.add(new_cp)
        db.commit()

    records = db.query(CourseProgress).filter(
        CourseProgress.user_id == current_user.id
    ).order_by(CourseProgress.updated_at.desc()).all()

    results = []
    for cp in records:
        cpo = CourseProgressOut.from_orm(cp)
        if cp.resource:
            cpo.resource = build_resource_out(cp.resource, db)
        results.append(cpo)
    return results

@router.post("", response_model=CourseProgressOut)
def create_course_progress(
    payload: CourseProgressCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    res = db.query(Resource).filter(
        Resource.id == payload.resource_id,
        Resource.user_id == current_user.id
    ).first()
    if not res:
        raise HTTPException(status_code=404, detail="Resource not found.")

    existing = db.query(CourseProgress).filter(
        CourseProgress.resource_id == payload.resource_id,
        CourseProgress.user_id == current_user.id
    ).first()

    if existing:
        existing.status = payload.status or existing.status
        if payload.progress_percentage is not None:
            existing.progress_percentage = max(0, min(100, payload.progress_percentage))
        existing.current_module = payload.current_module or existing.current_module
        existing.target_completion_date = payload.target_completion_date or existing.target_completion_date
        existing.notes = payload.notes or existing.notes
        cp_obj = existing
    else:
        pct = max(0, min(100, payload.progress_percentage or 0))
        cp_obj = CourseProgress(
            user_id=current_user.id,
            resource_id=payload.resource_id,
            status=payload.status or "In Progress",
            progress_percentage=pct,
            current_module=payload.current_module or "Getting Started",
            target_completion_date=payload.target_completion_date,
            notes=payload.notes or ""
        )
        db.add(cp_obj)

    db.commit()
    db.refresh(cp_obj)
    out = CourseProgressOut.from_orm(cp_obj)
    if cp_obj.resource:
        out.resource = build_resource_out(cp_obj.resource, db)
    return out

@router.put("/{cp_id}", response_model=CourseProgressOut)
def update_course_progress(
    cp_id: int,
    payload: CourseProgressUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    cp_obj = db.query(CourseProgress).filter(
        CourseProgress.id == cp_id,
        CourseProgress.user_id == current_user.id
    ).first()
    if not cp_obj:
        raise HTTPException(status_code=404, detail="Course progress item not found.")

    if payload.status is not None:
        cp_obj.status = payload.status
        if payload.status in ("Completed", "Certified") and (payload.progress_percentage is None or payload.progress_percentage < 100):
            cp_obj.progress_percentage = 100
    if payload.progress_percentage is not None:
        cp_obj.progress_percentage = max(0, min(100, payload.progress_percentage))
    if payload.current_module is not None:
        cp_obj.current_module = payload.current_module
    if payload.target_completion_date is not None:
        cp_obj.target_completion_date = payload.target_completion_date
    if payload.notes is not None:
        cp_obj.notes = payload.notes

    db.commit()
    db.refresh(cp_obj)
    out = CourseProgressOut.from_orm(cp_obj)
    if cp_obj.resource:
        out.resource = build_resource_out(cp_obj.resource, db)
    return out

@router.delete("/{cp_id}")
def delete_course_progress(
    cp_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    cp_obj = db.query(CourseProgress).filter(
        CourseProgress.id == cp_id,
        CourseProgress.user_id == current_user.id
    ).first()
    if not cp_obj:
        raise HTTPException(status_code=404, detail="Course progress item not found.")

    db.delete(cp_obj)
    db.commit()
    return {"status": "deleted", "id": cp_id}
