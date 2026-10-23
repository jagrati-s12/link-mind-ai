from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.models import User, Recommendation, Resource, UserProfile, Resume, UserSkill
from app.schemas import RecommendationOut
from app.services.matcher import calculate_recommendation
from app.api.deps import get_current_user
from app.api.v1.resources import build_resource_out

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])

@router.get("", response_model=List[RecommendationOut])
def list_recommendations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    recs = db.query(Recommendation).filter(
        Recommendation.user_id == current_user.id
    ).order_by(Recommendation.fit_score.desc()).all()

    results = []
    for r in recs:
        ro = RecommendationOut.from_orm(r)
        if r.resource:
            ro.resource = build_resource_out(r.resource, db)
        results.append(ro)
    return results

@router.post("/recalculate", response_model=List[RecommendationOut])
def recalculate_recommendations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    active_resume = db.query(Resume).filter(Resume.user_id == current_user.id, Resume.is_active == True).first()
    user_skills = db.query(UserSkill).filter(UserSkill.user_id == current_user.id).all()
    
    resources = db.query(Resource).filter(
        Resource.user_id == current_user.id,
        Resource.is_archived == False
    ).all()

    results = []
    for res in resources:
        rec_data = calculate_recommendation(res, profile, user_skills, active_resume)
        rec = db.query(Recommendation).filter(
            Recommendation.resource_id == res.id,
            Recommendation.user_id == current_user.id
        ).first()

        if rec:
            for k, v in rec_data.items():
                setattr(rec, k, v)
            if active_resume:
                rec.resume_id = active_resume.id
        else:
            rec = Recommendation(
                user_id=current_user.id,
                resource_id=res.id,
                resume_id=active_resume.id if active_resume else None,
                **rec_data
            )
            db.add(rec)
        db.flush()
        
        ro = RecommendationOut.from_orm(rec)
        ro.resource = build_resource_out(res, db)
        results.append(ro)

    db.commit()
    results.sort(key=lambda x: x.fit_score, reverse=True)
    return results
