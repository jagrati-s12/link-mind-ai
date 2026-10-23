import os
import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.core.config import settings
from app.models import User, UserProfile, Resume, UserSkill, Skill
from app.schemas import UserProfileOut, UserProfileUpdate, ResumeOut
from app.services.fetcher import extract_document_file
from app.services.ai_adapter import parse_resume_content
from app.api.deps import get_current_user
from app.api.v1.recommendations import recalculate_recommendations

router = APIRouter(prefix="/profile", tags=["Profile"])

@router.get("", response_model=UserProfileOut)
def get_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    if not profile:
        profile = UserProfile(user_id=current_user.id)
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile

@router.patch("", response_model=UserProfileOut)
def update_profile(
    payload: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    if not profile:
        profile = UserProfile(user_id=current_user.id)
        db.add(profile)

    for k, v in payload.dict(exclude_unset=True).items():
        setattr(profile, k, v)

    db.commit()
    db.refresh(profile)

    # Recalculate recommendations
    try:
        recalculate_recommendations(current_user, db)
    except Exception:
        pass

    return profile

@router.post("/resume", response_model=ResumeOut)
async def upload_resume(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    filename = file.filename or "resume.pdf"
    ext = os.path.splitext(filename)[1].lower()
    if ext not in (".pdf", ".docx", ".txt"):
        raise HTTPException(status_code=400, detail="Allowed resume formats: PDF, DOCX, TXT.")

    saved_name = f"resume_{uuid.uuid4()}_{filename}"
    file_path = os.path.join(settings.UPLOAD_DIR, saved_name)
    content_bytes = await file.read()
    if len(content_bytes) > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=400, detail="Resume file exceeds 15MB size limit.")

    with open(file_path, "wb") as f:
        f.write(content_bytes)

    doc_res = extract_document_file(file_path, filename)
    if doc_res.error:
        raise HTTPException(status_code=400, detail=f"Failed to read resume: {doc_res.error}")

    parsed_info = parse_resume_content(doc_res.content)

    # Mark other resumes inactive
    db.query(Resume).filter(Resume.user_id == current_user.id).update({"is_active": False})

    # Create new resume version
    resume = Resume(
        user_id=current_user.id,
        version_name=filename,
        file_path=file_path,
        raw_text=doc_res.content,
        parsed_data=parsed_info,
        is_active=True
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)

    # Sync extracted skills into user_skills table
    for s_name in (parsed_info.get("technical_skills", []) + parsed_info.get("frameworks", []) + parsed_info.get("tools", [])):
        skill = db.query(Skill).filter(Skill.name.ilike(s_name)).first()
        if not skill:
            skill = Skill(name=s_name, category="Resume Extracted")
            db.add(skill)
            db.commit()
            db.refresh(skill)

        us = db.query(UserSkill).filter(
            UserSkill.user_id == current_user.id,
            UserSkill.skill_id == skill.id
        ).first()
        if not us:
            us = UserSkill(
                user_id=current_user.id,
                skill_id=skill.id,
                proficiency_level="intermediate",
                evidence=[f"Extracted from {filename}"],
                verified_by_user=False
            )
            db.add(us)

    db.commit()

    # Recalculate recommendations
    try:
        recalculate_recommendations(current_user, db)
    except Exception:
        pass

    return resume

@router.get("/resumes", response_model=List[ResumeOut])
def list_resumes(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return db.query(Resume).filter(
        Resume.user_id == current_user.id
    ).order_by(Resume.created_at.desc()).all()

@router.patch("/resumes/{resume_id}/activate", response_model=ResumeOut)
def activate_resume(
    resume_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    target = db.query(Resume).filter(
        Resume.id == resume_id,
        Resume.user_id == current_user.id
    ).first()
    if not target:
        raise HTTPException(status_code=404, detail="Resume version not found.")

    db.query(Resume).filter(Resume.user_id == current_user.id).update({"is_active": False})
    target.is_active = True
    db.commit()
    db.refresh(target)

    # Recalculate recommendations
    try:
        recalculate_recommendations(current_user, db)
    except Exception:
        pass

    return target
