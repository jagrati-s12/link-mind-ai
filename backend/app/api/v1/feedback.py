from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.models import User, ListingFeedback, Resource
from app.schemas import (
    ListingFeedbackCreate, ListingFeedbackOut, ModelLearningStatsOut
)
from app.api.deps import get_current_user
from app.services.learning_engine import record_feedback, get_model_learning_stats

router = APIRouter(prefix="/feedback", tags=["Model Continuous Learning & Feedback"])

@router.post("", response_model=ListingFeedbackOut)
def submit_listing_feedback(
    payload: ListingFeedbackCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        fb = record_feedback(
            db=db,
            user_id=current_user.id,
            resource_id=payload.resource_id,
            is_correct=payload.is_correct,
            corrected_type=payload.corrected_type,
            corrected_title=payload.corrected_title,
            reason=payload.reason,
            notes=payload.notes
        )
        return ListingFeedbackOut.from_orm(fb)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to record feedback: {str(e)}")

@router.get("/stats", response_model=ModelLearningStatsOut)
def get_learning_metrics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return get_model_learning_stats(db)

@router.get("/resource/{resource_id}", response_model=Optional[ListingFeedbackOut])
def get_resource_feedback(
    resource_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    fb = db.query(ListingFeedback).filter(
        ListingFeedback.resource_id == resource_id,
        ListingFeedback.user_id == current_user.id
    ).order_by(ListingFeedback.created_at.desc()).first()

    if not fb:
        return None
    return ListingFeedbackOut.from_orm(fb)
