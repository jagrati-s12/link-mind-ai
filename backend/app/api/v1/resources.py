from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.core.db import get_db
from app.models import (
    User, Resource, Collection, Recommendation, Application,
    UserProfile, Resume, UserSkill, ResourceRelation, CourseProgress, ListingFeedback
)
from app.schemas import (
    ResourceOut, ResourceCreate, ResourceUpdate,
    CollectionMiniOut, RecommendationMiniOut, ApplicationMiniOut
)
from app.services.matcher import calculate_recommendation
from app.services.relationship_engine import auto_connect_resources
from app.api.deps import get_current_user

router = APIRouter(prefix="/resources", tags=["Resources"])

def build_resource_out(res: Resource, db: Session) -> ResourceOut:
    out = ResourceOut.from_orm(res)
    if res.source and res.source.original_url:
        out.source_url = res.source.original_url

    # Populate collections
    out.collections = [
        CollectionMiniOut(id=c.id, name=c.name, color=c.color, icon=c.icon)
        for c in res.collections
    ]

    # Populate recommendation
    rec = db.query(Recommendation).filter(
        Recommendation.resource_id == res.id,
        Recommendation.user_id == res.user_id
    ).first()
    if rec:
        out.recommendation = RecommendationMiniOut(
            id=rec.id,
            fit_score=rec.fit_score,
            skill_score=rec.skill_score,
            explanation=rec.explanation,
            matching_skills=rec.matching_skills or [],
            missing_skills=rec.missing_skills or [],
            eligibility_status=rec.eligibility_status
        )

    # Populate application
    app = db.query(Application).filter(
        Application.resource_id == res.id,
        Application.user_id == res.user_id
    ).first()

    # Automatically initialize application tracker for internships & jobs
    if not app and res.type in ("internship", "job"):
        app = Application(
            user_id=res.user_id,
            resource_id=res.id,
            status="Saved",
            deadline=res.deadline,
            notes=res.notes or ""
        )
        db.add(app)
        db.commit()
        db.refresh(app)

    if app:
        out.application = ApplicationMiniOut(
            id=app.id,
            status=app.status,
            deadline=app.deadline,
            application_date=app.application_date
        )

    return out

@router.get("", response_model=List[ResourceOut])
def list_resources(
    type: Optional[str] = None,
    collection_id: Optional[int] = None,
    search: Optional[str] = None,
    verification_status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Resource).filter(
        Resource.user_id == current_user.id,
        Resource.is_archived == False
    )

    if type:
        if type == "courses":
            query = query.filter(Resource.type.in_(["course", "certification"]))
        elif type == "internships":
            query = query.filter(Resource.type == "internship")
        elif type == "jobs":
            query = query.filter(Resource.type == "job")
        elif type == "hackathons":
            query = query.filter(Resource.type == "hackathon")
        else:
            query = query.filter(Resource.type == type)

    if collection_id:
        query = query.join(Resource.collections).filter(Collection.id == collection_id)

    if verification_status:
        query = query.filter(Resource.verification_status == verification_status)

    if search:
        search_term = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Resource.title.ilike(search_term),
                Resource.organization.ilike(search_term),
                Resource.description.ilike(search_term)
            )
        )

    resources = query.order_by(Resource.created_at.desc()).all()
    return [build_resource_out(r, db) for r in resources]

@router.get("/{resource_id}", response_model=ResourceOut)
def get_resource(
    resource_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    resource = db.query(Resource).filter(
        Resource.id == resource_id,
        Resource.user_id == current_user.id
    ).first()
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found.")

    return build_resource_out(resource, db)

@router.post("", response_model=ResourceOut)
def create_resource(
    payload: ResourceCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    res = Resource(
        user_id=current_user.id,
        source_id=payload.source_id,
        type=payload.type,
        title=payload.title,
        organization=payload.organization,
        description=payload.description or "",
        direct_url=payload.direct_url,
        location=payload.location,
        compensation=payload.compensation,
        duration=payload.duration,
        deadline=payload.deadline,
        eligibility=payload.eligibility or {},
        required_skills=payload.required_skills or [],
        taught_skills=payload.taught_skills or [],
        source_evidence=payload.source_evidence or [],
        confidence=payload.confidence or 1.0,
        verification_status=payload.verification_status or "verified",
        notes=payload.notes or ""
    )
    db.add(res)
    db.commit()
    db.refresh(res)

    if payload.collection_ids:
        collections = db.query(Collection).filter(
            Collection.user_id == current_user.id,
            Collection.id.in_(payload.collection_ids)
        ).all()
        res.collections = collections
        db.commit()

    # Recalculate recommendation
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    active_resume = db.query(Resume).filter(Resume.user_id == current_user.id, Resume.is_active == True).first()
    user_skills = db.query(UserSkill).filter(UserSkill.user_id == current_user.id).all()
    
    rec_data = calculate_recommendation(res, profile, user_skills, active_resume)
    rec = Recommendation(
        user_id=current_user.id,
        resource_id=res.id,
        resume_id=active_resume.id if active_resume else None,
        **rec_data
    )
    db.add(rec)
    db.commit()

    # Auto connect
    auto_connect_resources(db, current_user.id, res.id)

    return build_resource_out(res, db)

@router.patch("/{resource_id}", response_model=ResourceOut)
def update_resource(
    resource_id: int,
    payload: ResourceUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    res = db.query(Resource).filter(
        Resource.id == resource_id,
        Resource.user_id == current_user.id
    ).first()
    if not res:
        raise HTTPException(status_code=404, detail="Resource not found.")

    update_dict = payload.dict(exclude_unset=True)
    if "collection_ids" in update_dict:
        col_ids = update_dict.pop("collection_ids")
        if col_ids is not None:
            cols = db.query(Collection).filter(
                Collection.user_id == current_user.id,
                Collection.id.in_(col_ids)
            ).all()
            res.collections = cols

    for k, v in update_dict.items():
        setattr(res, k, v)

    db.commit()
    db.refresh(res)

    # Recalculate recommendation
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    active_resume = db.query(Resume).filter(Resume.user_id == current_user.id, Resume.is_active == True).first()
    user_skills = db.query(UserSkill).filter(UserSkill.user_id == current_user.id).all()
    
    rec_data = calculate_recommendation(res, profile, user_skills, active_resume)
    rec = db.query(Recommendation).filter(
        Recommendation.resource_id == res.id,
        Recommendation.user_id == current_user.id
    ).first()
    if rec:
        for k, v in rec_data.items():
            setattr(rec, k, v)
    else:
        rec = Recommendation(user_id=current_user.id, resource_id=res.id, **rec_data)
        db.add(rec)
    db.commit()

    return build_resource_out(res, db)

@router.delete("/{resource_id}")
def delete_resource(
    resource_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    res = db.query(Resource).filter(
        Resource.id == resource_id,
        Resource.user_id == current_user.id
    ).first()
    if not res:
        raise HTTPException(status_code=404, detail="Resource not found.")

    # Cleanly remove secondary associations & dependent child rows
    db.query(CourseProgress).filter(CourseProgress.resource_id == resource_id).delete(synchronize_session=False)
    db.query(Application).filter(Application.resource_id == resource_id).delete(synchronize_session=False)
    db.query(Recommendation).filter(Recommendation.resource_id == resource_id).delete(synchronize_session=False)
    db.query(ListingFeedback).filter(ListingFeedback.resource_id == resource_id).delete(synchronize_session=False)
    res.collections.clear()

    db.delete(res)
    db.commit()
    return {"status": "success", "message": "Resource deleted."}
