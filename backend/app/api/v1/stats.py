from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.models import User, Resource, Recommendation, Collection, Application
from app.schemas import DashboardStatsOut
from app.api.deps import get_current_user

router = APIRouter(prefix="/stats", tags=["Stats"])

@router.get("", response_model=DashboardStatsOut)
def get_dashboard_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    courses_count = db.query(Resource).filter(
        Resource.user_id == current_user.id,
        Resource.type.in_(["course", "certification"]),
        Resource.is_archived == False
    ).count()

    internships_count = db.query(Resource).filter(
        Resource.user_id == current_user.id,
        Resource.type.in_(["internship", "job"]),
        Resource.is_archived == False
    ).count()

    hackathons_count = db.query(Resource).filter(
        Resource.user_id == current_user.id,
        Resource.type == "hackathon",
        Resource.is_archived == False
    ).count()

    strong_matches_count = db.query(Recommendation).filter(
        Recommendation.user_id == current_user.id,
        Recommendation.fit_score >= 75.0
    ).count()

    deadlines_count = db.query(Resource).filter(
        Resource.user_id == current_user.id,
        Resource.is_archived == False,
        Resource.deadline != None,
        Resource.deadline != ""
    ).count()

    total_resources = db.query(Resource).filter(
        Resource.user_id == current_user.id,
        Resource.is_archived == False
    ).count()

    total_collections = db.query(Collection).filter(
        Collection.user_id == current_user.id
    ).count()

    applications_count = db.query(Application).filter(
        Application.user_id == current_user.id
    ).count()

    return DashboardStatsOut(
        courses_saved=courses_count,
        internships_saved=internships_count,
        hackathons_saved=hackathons_count,
        strong_matches=strong_matches_count,
        upcoming_deadlines=deadlines_count,
        total_resources=total_resources,
        total_collections=total_collections,
        applications_count=applications_count
    )
