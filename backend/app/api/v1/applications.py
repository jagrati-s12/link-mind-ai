from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.models import User, Application, Resource
from app.schemas import ApplicationOut, ApplicationCreate, ApplicationUpdate
from app.api.deps import get_current_user
from app.api.v1.resources import build_resource_out

router = APIRouter(prefix="/applications", tags=["Applications"])

@router.get("", response_model=List[ApplicationOut])
def list_applications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    apps = db.query(Application).filter(
        Application.user_id == current_user.id
    ).order_by(Application.created_at.desc()).all()

    results = []
    for a in apps:
        ao = ApplicationOut.from_orm(a)
        if a.resource:
            ao.resource = build_resource_out(a.resource, db)
        results.append(ao)
    return results

@router.post("", response_model=ApplicationOut)
def create_application(
    payload: ApplicationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    res = db.query(Resource).filter(
        Resource.id == payload.resource_id,
        Resource.user_id == current_user.id
    ).first()
    if not res:
        raise HTTPException(status_code=404, detail="Resource not found.")

    # Check if application already exists for this resource
    existing = db.query(Application).filter(
        Application.resource_id == payload.resource_id,
        Application.user_id == current_user.id
    ).first()

    if existing:
        existing.status = payload.status or existing.status
        existing.application_date = payload.application_date or existing.application_date
        existing.deadline = payload.deadline or existing.deadline
        existing.notes = payload.notes or existing.notes
        existing.follow_up_date = payload.follow_up_date or existing.follow_up_date
        app_obj = existing
    else:
        app_obj = Application(
            user_id=current_user.id,
            resource_id=payload.resource_id,
            status=payload.status or "Saved",
            application_date=payload.application_date,
            deadline=payload.deadline or res.deadline,
            notes=payload.notes or "",
            follow_up_date=payload.follow_up_date
        )
        db.add(app_obj)

    db.commit()
    db.refresh(app_obj)
    ao = ApplicationOut.from_orm(app_obj)
    ao.resource = build_resource_out(res, db)
    return ao

@router.patch("/{application_id}", response_model=ApplicationOut)
def update_application(
    application_id: int,
    payload: ApplicationUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    app_obj = db.query(Application).filter(
        Application.id == application_id,
        Application.user_id == current_user.id
    ).first()
    if not app_obj:
        raise HTTPException(status_code=404, detail="Application record not found.")

    for k, v in payload.dict(exclude_unset=True).items():
        setattr(app_obj, k, v)

    db.commit()
    db.refresh(app_obj)
    ao = ApplicationOut.from_orm(app_obj)
    if app_obj.resource:
        ao.resource = build_resource_out(app_obj.resource, db)
    return ao

@router.delete("/{application_id}")
def delete_application(
    application_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    app_obj = db.query(Application).filter(
        Application.id == application_id,
        Application.user_id == current_user.id
    ).first()
    if not app_obj:
        raise HTTPException(status_code=404, detail="Application record not found.")

    db.delete(app_obj)
    db.commit()
    return {"status": "success", "message": "Application removed."}
