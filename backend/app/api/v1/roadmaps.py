from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.models import User, Roadmap
from app.schemas import RoadmapOut, RoadmapCreate, RoadmapUpdate
from app.services.roadmap_generator import generate_personalized_roadmap, get_roadmap_catalog
from app.api.deps import get_current_user

router = APIRouter(prefix="/roadmaps", tags=["Roadmaps"])

@router.get("/catalog")
def list_roadmap_catalog():
    """Returns curated roadmap.sh presets available for 1-click generation."""
    return get_roadmap_catalog()

@router.get("", response_model=List[RoadmapOut])
def list_roadmaps(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    roadmaps = db.query(Roadmap).filter(
        Roadmap.user_id == current_user.id
    ).order_by(Roadmap.created_at.desc()).all()
    return roadmaps

@router.post("/generate", response_model=RoadmapOut)
async def generate_roadmap(
    goal_title: Optional[str] = Body(None, embed=True),
    goals: Optional[List[str]] = Body(None, embed=True),
    target_role: str = Body("", embed=True),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if goals and len(goals) > 1:
        effective_goal = " + ".join(g.strip() for g in goals if g.strip())
    else:
        effective_goal = goal_title or (goals[0] if goals else "Software Engineer")

    plan = await generate_personalized_roadmap(db, current_user.id, effective_goal, target_role)
    rm = Roadmap(
        user_id=current_user.id,
        goal_title=plan["goal_title"],
        target_role=plan["target_role"],
        description=plan["description"],
        steps=plan["steps"],
        youtube_playlists=plan.get("youtube_playlists", []),
        related_roadmaps=plan.get("related_roadmaps", [])
    )
    db.add(rm)
    db.commit()
    db.refresh(rm)
    return rm

@router.post("", response_model=RoadmapOut)
def create_custom_roadmap(
    payload: RoadmapCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    steps_data = [s.dict() for s in (payload.steps or [])]
    rm = Roadmap(
        user_id=current_user.id,
        goal_title=payload.goal_title,
        description=payload.description or "",
        target_role=payload.target_role or "",
        steps=steps_data
    )
    db.add(rm)
    db.commit()
    db.refresh(rm)
    return rm

@router.patch("/{roadmap_id}", response_model=RoadmapOut)
def update_roadmap(
    roadmap_id: int,
    payload: RoadmapUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    rm = db.query(Roadmap).filter(
        Roadmap.id == roadmap_id,
        Roadmap.user_id == current_user.id
    ).first()
    if not rm:
        raise HTTPException(status_code=404, detail="Roadmap not found.")

    if payload.goal_title is not None:
        rm.goal_title = payload.goal_title
    if payload.description is not None:
        rm.description = payload.description
    if payload.target_role is not None:
        rm.target_role = payload.target_role
    if payload.steps is not None:
        rm.steps = [s.dict() for s in payload.steps]

    db.commit()
    db.refresh(rm)
    return rm

@router.post("/{roadmap_id}/steps/{step_id}/toggle", response_model=RoadmapOut)
def toggle_step(
    roadmap_id: int,
    step_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    rm = db.query(Roadmap).filter(
        Roadmap.id == roadmap_id,
        Roadmap.user_id == current_user.id
    ).first()
    if not rm:
        raise HTTPException(status_code=404, detail="Roadmap not found.")

    updated_steps = []
    for step in rm.steps:
        s = dict(step)
        if s.get("id") == step_id:
            s["completed"] = not s.get("completed", False)
            if "topics" in s and isinstance(s["topics"], list):
                s["topics"] = [{**t, "completed": s["completed"]} for t in s["topics"]]
        updated_steps.append(s)

    rm.steps = updated_steps
    db.commit()
    db.refresh(rm)
    return rm

@router.post("/{roadmap_id}/steps/{step_id}/topics/{topic_idx}/toggle", response_model=RoadmapOut)
def toggle_subtopic(
    roadmap_id: int,
    step_id: str,
    topic_idx: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    rm = db.query(Roadmap).filter(
        Roadmap.id == roadmap_id,
        Roadmap.user_id == current_user.id
    ).first()
    if not rm:
        raise HTTPException(status_code=404, detail="Roadmap not found.")

    updated_steps = []
    for step in rm.steps:
        s = dict(step)
        if s.get("id") == step_id:
            topics = [dict(t) for t in s.get("topics", [])]
            if 0 <= topic_idx < len(topics):
                topics[topic_idx]["completed"] = not topics[topic_idx].get("completed", False)
                s["topics"] = topics
                # If all topics completed, mark parent step completed
                if topics and all(t.get("completed", False) for t in topics):
                    s["completed"] = True
                elif not any(t.get("completed", False) for t in topics):
                    s["completed"] = False
        updated_steps.append(s)

    rm.steps = updated_steps
    db.commit()
    db.refresh(rm)
    return rm

@router.post("/{roadmap_id}/steps/{step_id}/topics/{topic_idx}/references", response_model=RoadmapOut)
def add_subtopic_reference(
    roadmap_id: int,
    step_id: str,
    topic_idx: int,
    payload: Dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    rm = db.query(Roadmap).filter(
        Roadmap.id == roadmap_id,
        Roadmap.user_id == current_user.id
    ).first()
    if not rm:
        raise HTTPException(status_code=404, detail="Roadmap not found.")

    updated_steps = []
    for step in rm.steps:
        s = dict(step)
        if s.get("id") == step_id:
            topics = [dict(t) for t in s.get("topics", [])]
            if 0 <= topic_idx < len(topics):
                t = dict(topics[topic_idx])
                refs = list(t.get("references", []))
                new_ref = {
                    "title": payload.get("title") or "Learning Material",
                    "url": payload.get("url") or "",
                    "type": payload.get("type") or "link",
                    "notes": payload.get("notes") or "",
                    "is_user_added": True
                }
                refs.append(new_ref)
                t["references"] = refs
                topics[topic_idx] = t
                s["topics"] = topics
        updated_steps.append(s)

    rm.steps = updated_steps
    db.commit()
    db.refresh(rm)
    return rm

@router.delete("/{roadmap_id}/steps/{step_id}/topics/{topic_idx}/references/{ref_idx}", response_model=RoadmapOut)
def delete_subtopic_reference(
    roadmap_id: int,
    step_id: str,
    topic_idx: int,
    ref_idx: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    rm = db.query(Roadmap).filter(
        Roadmap.id == roadmap_id,
        Roadmap.user_id == current_user.id
    ).first()
    if not rm:
        raise HTTPException(status_code=404, detail="Roadmap not found.")

    updated_steps = []
    for step in rm.steps:
        s = dict(step)
        if s.get("id") == step_id:
            topics = [dict(t) for t in s.get("topics", [])]
            if 0 <= topic_idx < len(topics):
                t = dict(topics[topic_idx])
                refs = list(t.get("references", []))
                if 0 <= ref_idx < len(refs):
                    refs.pop(ref_idx)
                t["references"] = refs
                topics[topic_idx] = t
                s["topics"] = topics
        updated_steps.append(s)

    rm.steps = updated_steps
    db.commit()
    db.refresh(rm)
    return rm

@router.delete("/{roadmap_id}")
def delete_roadmap(
    roadmap_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    rm = db.query(Roadmap).filter(
        Roadmap.id == roadmap_id,
        Roadmap.user_id == current_user.id
    ).first()
    if not rm:
        raise HTTPException(status_code=404, detail="Roadmap not found.")

    db.delete(rm)
    db.commit()
    return {"status": "success", "message": "Roadmap deleted."}
