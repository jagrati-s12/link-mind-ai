from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.models import User, Resource, Collection, Application, Roadmap, Resume, UserSkill
from app.api.deps import get_current_user

router = APIRouter(prefix="/settings", tags=["Settings"])

@router.get("/export")
def export_user_data(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Exports all personal opportunities, resumes, applications, roadmaps, and skills
    as a structured JSON document.
    """
    resources = db.query(Resource).filter(Resource.user_id == current_user.id).all()
    collections = db.query(Collection).filter(Collection.user_id == current_user.id).all()
    applications = db.query(Application).filter(Application.user_id == current_user.id).all()
    roadmaps = db.query(Roadmap).filter(Roadmap.user_id == current_user.id).all()
    user_skills = db.query(UserSkill).filter(UserSkill.user_id == current_user.id).all()

    return {
        "user": {
            "email": current_user.email,
            "full_name": current_user.full_name,
            "created_at": str(current_user.created_at)
        },
        "resources": [
            {
                "id": r.id,
                "title": r.title,
                "type": r.type,
                "organization": r.organization,
                "description": r.description,
                "direct_url": r.direct_url,
                "deadline": r.deadline,
                "location": r.location,
                "compensation": r.compensation,
                "required_skills": r.required_skills,
                "taught_skills": r.taught_skills,
                "notes": r.notes
            }
            for r in resources
        ],
        "collections": [
            {"id": c.id, "name": c.name, "description": c.description, "is_smart": c.is_smart}
            for c in collections
        ],
        "applications": [
            {"id": a.id, "resource_id": a.resource_id, "status": a.status, "deadline": a.deadline, "notes": a.notes}
            for a in applications
        ],
        "roadmaps": [
            {"id": rm.id, "goal_title": rm.goal_title, "steps": rm.steps}
            for rm in roadmaps
        ],
        "skills": [
            {"name": us.skill.name if us.skill else "", "proficiency": us.proficiency_level, "evidence": us.evidence}
            for us in user_skills
        ]
    }

@router.delete("/account")
def delete_user_account(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Permanently deletes user account and all cascaded personal records.
    """
    db.delete(current_user)
    db.commit()
    return {"status": "success", "message": "User account and all personal library data deleted."}
