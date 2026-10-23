import logging
from urllib.parse import urlparse
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models import ListingFeedback, Resource, Application, CourseProgress
from app.schemas import ModelLearningStatsOut, ListingFeedbackOut

logger = logging.getLogger(__name__)

def extract_domain(url: Optional[str]) -> str:
    if not url:
        return ""
    try:
        parsed = urlparse(url)
        netloc = parsed.netloc.lower()
        if netloc.startswith("www."):
            netloc = netloc[4:]
        return netloc
    except Exception:
        return ""

def record_feedback(
    db: Session,
    user_id: int,
    resource_id: int,
    is_correct: bool,
    corrected_type: Optional[str] = None,
    corrected_title: Optional[str] = None,
    reason: Optional[str] = None,
    notes: Optional[str] = None
) -> ListingFeedback:
    res = db.query(Resource).filter(
        Resource.id == resource_id,
        Resource.user_id == user_id
    ).first()
    if not res:
        raise ValueError("Resource not found")

    domain = extract_domain(res.direct_url or res.source_url)

    feedback = ListingFeedback(
        user_id=user_id,
        resource_id=resource_id,
        is_correct=is_correct,
        original_type=res.type,
        corrected_type=corrected_type if not is_correct else None,
        original_title=res.title,
        corrected_title=corrected_title if not is_correct else None,
        domain=domain,
        reason=reason or ("Verified as accurate" if is_correct else "User corrected classification"),
        notes=notes or ""
    )
    db.add(feedback)

    if is_correct:
        # Reinforcement: confirm verification and bump confidence
        res.verification_status = "verified"
        res.confidence = 1.0
    else:
        # Correction applied: update resource in-place to improve library & move to right tab
        res.verification_status = "verified"
        if corrected_title and corrected_title.strip():
            res.title = corrected_title.strip()

        if corrected_type and corrected_type.strip():
            old_type = res.type
            new_type = corrected_type.strip().lower()
            res.type = new_type

            # If reclassified from job/internship to course: move from Application to CourseProgress
            if old_type in ("internship", "job") and new_type in ("course", "certification"):
                db.query(Application).filter(
                    Application.resource_id == res.id,
                    Application.user_id == user_id
                ).delete()

                existing_cp = db.query(CourseProgress).filter(
                    CourseProgress.resource_id == res.id,
                    CourseProgress.user_id == user_id
                ).first()
                if not existing_cp:
                    db.add(CourseProgress(
                        user_id=user_id,
                        resource_id=res.id,
                        status="In Progress",
                        progress_percentage=0,
                        current_module="Getting Started",
                        notes=notes or ""
                    ))

            # If reclassified from course to internship/job: move to Application
            elif old_type in ("course", "certification") and new_type in ("internship", "job"):
                db.query(CourseProgress).filter(
                    CourseProgress.resource_id == res.id,
                    CourseProgress.user_id == user_id
                ).delete()

                existing_app = db.query(Application).filter(
                    Application.resource_id == res.id,
                    Application.user_id == user_id
                ).first()
                if not existing_app:
                    db.add(Application(
                        user_id=user_id,
                        resource_id=res.id,
                        status="Saved",
                        deadline=res.deadline,
                        notes=notes or ""
                    ))

    db.commit()
    db.refresh(feedback)
    return feedback

def get_few_shot_prompt_examples(db: Session, limit: int = 6) -> str:
    """
    Retrieves verified user corrections to inject directly into LLM prompts as
    dynamic few-shot in-context learning examples. This causes LLMs to continuously adapt.
    """
    try:
        corrections = db.query(ListingFeedback).filter(
            ListingFeedback.is_correct == False,
            ListingFeedback.corrected_type != None
        ).order_by(desc(ListingFeedback.created_at)).limit(limit).all()

        if not corrections:
            return ""

        lines = [
            "\n--- HUMAN-IN-THE-LOOP CONTINUOUS TRAINING (RECENT USER CORRECTIONS) ---",
            "Follow these real learned corrections when classifying similar opportunities:"
        ]
        for c in corrections:
            domain_info = f" from [{c.domain}]" if c.domain else ""
            lines.append(
                f"- Listing '{c.original_title}'{domain_info}: Correct type is '{c.corrected_type}' (was incorrectly classified as '{c.original_type}'). Reason: {c.reason}"
            )
        return "\n".join(lines) + "\n"
    except Exception as e:
        logger.warning("Error fetching few-shot corrections: %s", str(e))
        return ""

def get_learned_domain_rules(db: Session) -> Dict[str, str]:
    """
    Generates deterministic domain rules from verified user feedback.
    e.g. {'coursera.org': 'course', 'hackerrank.com': 'job'}
    """
    try:
        corrections = db.query(ListingFeedback).filter(
            ListingFeedback.is_correct == False,
            ListingFeedback.corrected_type != None,
            ListingFeedback.domain != ""
        ).all()

        domain_votes: Dict[str, Dict[str, int]] = {}
        for c in corrections:
            d = c.domain.lower()
            t = c.corrected_type.lower()
            if d not in domain_votes:
                domain_votes[d] = {}
            domain_votes[d][t] = domain_votes[d].get(t, 0) + 1

        learned_rules = {}
        for d, votes in domain_votes.items():
            top_type = max(votes.items(), key=lambda x: x[1])[0]
            learned_rules[d] = top_type
        return learned_rules
    except Exception as e:
        logger.warning("Error computing learned domain rules: %s", str(e))
        return {}

def get_model_learning_stats(db: Session) -> ModelLearningStatsOut:
    total = db.query(ListingFeedback).count()
    accurate = db.query(ListingFeedback).filter(ListingFeedback.is_correct == True).count()
    corrections = db.query(ListingFeedback).filter(ListingFeedback.is_correct == False).count()

    accuracy_rate = round((accurate / total * 100.0), 1) if total > 0 else 100.0

    recent_corrections = db.query(ListingFeedback).filter(
        ListingFeedback.is_correct == False
    ).order_by(desc(ListingFeedback.created_at)).limit(10).all()

    recent_out = [ListingFeedbackOut.from_orm(c) for c in recent_corrections]

    return ModelLearningStatsOut(
        total_feedback_count=total,
        verified_accurate_count=accurate,
        user_corrections_count=corrections,
        accuracy_rate=accuracy_rate,
        active_few_shot_examples=len(recent_corrections),
        recent_corrections=recent_out
    )
