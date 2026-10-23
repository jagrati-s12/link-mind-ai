from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.models import User, Skill, UserSkill, Resource, UserProfile, Resume
from app.schemas import SkillOut, UserSkillOut, UserSkillCreate, SkillGapOut
from app.api.deps import get_current_user

router = APIRouter(prefix="/skills", tags=["Skills"])

ROLE_SKILL_BENCHMARKS = {
    "ai engineer": ["python", "pytorch", "scikit-learn", "deep learning", "docker", "sql", "data structures"],
    "machine learning engineer": ["python", "scikit-learn", "pytorch", "pandas", "numpy", "sql", "docker", "algorithms"],
    "backend developer": ["python", "fastapi", "sql", "postgresql", "docker", "redis", "rest api", "git"],
    "frontend developer": ["javascript", "typescript", "react", "html", "css", "tailwind css", "git"],
    "full stack developer": ["javascript", "typescript", "react", "node.js", "sql", "python", "docker", "git"],
    "data scientist": ["python", "sql", "pandas", "numpy", "machine learning", "data analysis", "scikit-learn"],
    "cloud / devops": ["aws", "docker", "kubernetes", "ci/cd", "linux", "python", "git"]
}

@router.get("", response_model=List[SkillOut])
def list_skills(db: Session = Depends(get_db)):
    skills = db.query(Skill).order_by(Skill.name).all()
    return skills

@router.get("/user", response_model=List[UserSkillOut])
def get_user_skills(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    skills = db.query(UserSkill).filter(UserSkill.user_id == current_user.id).all()
    result = []
    for us in skills:
        result.append(UserSkillOut(
            id=us.id,
            user_id=us.user_id,
            skill_id=us.skill_id,
            skill_name=us.skill.name if us.skill else "Skill",
            proficiency_level=us.proficiency_level,
            evidence=us.evidence or [],
            verified_by_user=us.verified_by_user
        ))
    return result

@router.post("/user", response_model=UserSkillOut)
def add_user_skill(
    payload: UserSkillCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    clean_name = payload.skill_name.strip()
    skill = db.query(Skill).filter(Skill.name.ilike(clean_name)).first()
    if not skill:
        skill = Skill(name=clean_name.title(), category="Technical")
        db.add(skill)
        db.commit()
        db.refresh(skill)

    user_skill = db.query(UserSkill).filter(
        UserSkill.user_id == current_user.id,
        UserSkill.skill_id == skill.id
    ).first()

    if user_skill:
        user_skill.proficiency_level = payload.proficiency_level or user_skill.proficiency_level
        user_skill.evidence = payload.evidence or user_skill.evidence
        user_skill.verified_by_user = True
    else:
        user_skill = UserSkill(
            user_id=current_user.id,
            skill_id=skill.id,
            proficiency_level=payload.proficiency_level or "intermediate",
            evidence=payload.evidence or [],
            verified_by_user=True
        )
        db.add(user_skill)

    db.commit()
    db.refresh(user_skill)
    return UserSkillOut(
        id=user_skill.id,
        user_id=user_skill.user_id,
        skill_id=user_skill.skill_id,
        skill_name=skill.name,
        proficiency_level=user_skill.proficiency_level,
        evidence=user_skill.evidence or [],
        verified_by_user=user_skill.verified_by_user
    )

@router.delete("/user/{user_skill_id}")
def delete_user_skill(
    user_skill_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    us = db.query(UserSkill).filter(
        UserSkill.id == user_skill_id,
        UserSkill.user_id == current_user.id
    ).first()
    if not us:
        raise HTTPException(status_code=404, detail="Skill record not found.")
    db.delete(us)
    db.commit()
    return {"status": "success", "message": "User skill removed."}

@router.get("/gaps", response_model=SkillGapOut)
def get_skill_gaps(
    role: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    target_role = role or (profile.target_roles[0] if profile and profile.target_roles else "AI Engineer")
    target_key = target_role.lower()

    # Find required skills from benchmark or default
    required = ROLE_SKILL_BENCHMARKS.get(target_key)
    if not required:
        for k in ROLE_SKILL_BENCHMARKS:
            if k in target_key or target_key in k:
                required = ROLE_SKILL_BENCHMARKS[k]
                break
    if not required:
        required = ["python", "sql", "git", "data structures", "system design"]

    # Gather user's known skills
    user_skills = db.query(UserSkill).filter(UserSkill.user_id == current_user.id).all()
    user_skill_names = set(us.skill.name.lower() for us in user_skills if us.skill)
    
    active_resume = db.query(Resume).filter(Resume.user_id == current_user.id, Resume.is_active == True).first()
    if active_resume and active_resume.parsed_data:
        parsed = active_resume.parsed_data
        for s in parsed.get("technical_skills", []) + parsed.get("frameworks", []) + parsed.get("tools", []):
            user_skill_names.add(s.lower())

    possessed = []
    missing = []
    for r in required:
        if any(r in u or u in r for u in user_skill_names):
            possessed.append(r.title())
        else:
            missing.append(r.title())

    # Find recommended saved courses teaching the missing skills
    courses = db.query(Resource).filter(
        Resource.user_id == current_user.id,
        Resource.type.in_(["course", "certification"]),
        Resource.is_archived == False
    ).all()

    rec_courses = []
    missing_lower = [m.lower() for m in missing]
    for c in courses:
        taught = [t.lower() for t in (c.taught_skills or [])]
        overlap = [t for t in taught if t in missing_lower]
        if overlap or not missing:
            rec_courses.append({
                "id": c.id,
                "title": c.title,
                "organization": c.organization,
                "teaches": [t.title() for t in overlap] if overlap else c.taught_skills[:3],
                "direct_url": c.direct_url
            })

    # Find target internships
    internships = db.query(Resource).filter(
        Resource.user_id == current_user.id,
        Resource.type.in_(["internship", "job"]),
        Resource.is_archived == False
    ).limit(5).all()

    rec_internships = [
        {"id": i.id, "title": i.title, "organization": i.organization, "deadline": i.deadline, "direct_url": i.direct_url}
        for i in internships
    ]

    return SkillGapOut(
        target_role=target_role,
        required_skills=[r.title() for r in required],
        possessed_skills=possessed,
        missing_skills=missing,
        recommended_courses=rec_courses[:5],
        recommended_internships=rec_internships
    )
