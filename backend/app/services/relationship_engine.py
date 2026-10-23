from typing import List
from sqlalchemy.orm import Session
from app.models import Resource, ResourceRelation, Skill

def auto_connect_resources(db: Session, user_id: int, new_resource_id: int):
    """
    Discovers and persists relationships between the new resource and existing user resources:
    - Course teaches skill required by Internship (prepares_for)
    - Resources sharing core required tech stack (requires_same_skills)
    - Duplicate detection (matching direct URLs or titles)
    """
    new_res = db.query(Resource).filter(Resource.id == new_resource_id, Resource.user_id == user_id).first()
    if not new_res:
        return

    other_resources = db.query(Resource).filter(
        Resource.user_id == user_id,
        Resource.id != new_resource_id,
        Resource.is_archived == False
    ).all()

    new_taught = set(s.lower() for s in (new_res.taught_skills or []))
    new_required = set(s.lower() for s in (new_res.required_skills or []))

    for other in other_resources:
        other_taught = set(s.lower() for s in (other.taught_skills or []))
        other_required = set(s.lower() for s in (other.required_skills or []))

        # 1. Duplicate detection
        if new_res.direct_url and other.direct_url and new_res.direct_url == other.direct_url:
            # Duplicate URL
            _create_relation_if_not_exists(
                db, new_res.id, other.id, "duplicate_of", 1.0,
                "Both resources share the exact direct link."
            )
            continue
        elif (
            new_res.title.lower().strip() == other.title.lower().strip()
            and (new_res.organization or "").lower() == (other.organization or "").lower()
            and new_res.type == other.type
        ):
            _create_relation_if_not_exists(
                db, new_res.id, other.id, "duplicate_of", 0.95,
                "Identical title and provider detected."
            )
            continue

        # 2. Course prepares for Internship or Hackathon
        # Case A: new_res is course, other is internship / hackathon
        if new_res.type in ("course", "certification", "project") and other.type in ("internship", "job", "hackathon"):
            overlap = new_taught.intersection(other_required)
            if overlap:
                skills_str = ", ".join(s.title() for s in overlap)
                _create_relation_if_not_exists(
                    db, new_res.id, other.id, "prepares_for", 0.85,
                    f"Course teaches {skills_str} required by {other.title}."
                )

        # Case B: new_res is internship / hackathon, other is course
        elif new_res.type in ("internship", "job", "hackathon") and other.type in ("course", "certification", "project"):
            overlap = other_taught.intersection(new_required)
            if overlap:
                skills_str = ", ".join(s.title() for s in overlap)
                _create_relation_if_not_exists(
                    db, other.id, new_res.id, "prepares_for", 0.85,
                    f"Course {other.title} teaches {skills_str} required by this role."
                )

        # 3. Same skill stack
        if new_res.type == other.type and new_required and other_required:
            overlap = new_required.intersection(other_required)
            if len(overlap) >= 2:
                _create_relation_if_not_exists(
                    db, new_res.id, other.id, "requires_same_skills", 0.75,
                    f"Both share requirements in {', '.join(s.title() for s in overlap)}."
                )

def _create_relation_if_not_exists(
    db: Session,
    source_id: int,
    target_id: int,
    rel_type: str,
    confidence: float,
    rationale: str
):
    exists = db.query(ResourceRelation).filter(
        ResourceRelation.source_resource_id == source_id,
        ResourceRelation.target_resource_id == target_id,
        ResourceRelation.relation_type == rel_type
    ).first()
    if not exists:
        rel = ResourceRelation(
            source_resource_id=source_id,
            target_resource_id=target_id,
            relation_type=rel_type,
            confidence=confidence,
            rationale=rationale
        )
        db.add(rel)
        db.commit()
