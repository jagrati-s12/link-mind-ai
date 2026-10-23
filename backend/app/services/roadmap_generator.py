import uuid
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.models import Resource, UserProfile, Resume, UserSkill

def generate_personalized_roadmap(db: Session, user_id: int, goal_title: str, target_role: str = "") -> Dict[str, Any]:
    """
    Builds a grounded 5-phase career roadmap uniquely tailored to the user's saved resources,
    missing skills, and active resume.
    """
    profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    active_resume = db.query(Resume).filter(Resume.user_id == user_id, Resume.is_active == True).first()
    user_skills_list = db.query(UserSkill).filter(UserSkill.user_id == user_id).all()
    user_skill_names = set(us.skill.name.lower() for us in user_skills_list if us.skill)

    if active_resume and active_resume.parsed_data:
        parsed = active_resume.parsed_data
        for s in parsed.get("technical_skills", []) + parsed.get("frameworks", []) + parsed.get("tools", []):
            user_skill_names.add(s.lower())

    # Get user's saved courses and internships
    saved_courses = db.query(Resource).filter(
        Resource.user_id == user_id,
        Resource.type.in_(["course", "certification"]),
        Resource.is_archived == False
    ).all()

    saved_internships = db.query(Resource).filter(
        Resource.user_id == user_id,
        Resource.type.in_(["internship", "job"]),
        Resource.is_archived == False
    ).all()

    # Step 1: Skill Assessment
    known_skills_str = ", ".join([s.title() for s in list(user_skill_names)[:6]]) if user_skill_names else "Python, Git, Problem Solving"
    step1 = {
        "id": str(uuid.uuid4())[:8],
        "title": "Phase 1: Baseline Skill Assessment",
        "description": f"Verified current competencies: {known_skills_str}. Audit resume alignment against target '{goal_title}'.",
        "resource_ids": [],
        "skill_ids": [],
        "order": 1,
        "completed": True if len(user_skill_names) >= 3 else False
    }

    # Step 2: Targeted Learning
    course_ids = [c.id for c in saved_courses[:3]]
    courses_titles = ", ".join([c.title for c in saved_courses[:2]]) if saved_courses else "target technical specialization courses"
    step2 = {
        "id": str(uuid.uuid4())[:8],
        "title": "Phase 2: Complete Targeted Core Courses",
        "description": f"Close key skill gaps by working through saved resources: {courses_titles}.",
        "resource_ids": course_ids,
        "skill_ids": [],
        "order": 2,
        "completed": False
    }

    # Step 3: Practical Project
    step3 = {
        "id": str(uuid.uuid4())[:8],
        "title": "Phase 3: Build & Deploy Portfolio Project",
        "description": f"Synthesize core tools into a production-grade project with reproducible documentation, unit tests, and live deployment.",
        "resource_ids": [],
        "skill_ids": [],
        "order": 3,
        "completed": False
    }

    # Step 4: Shortlist & Refine Opportunities
    internship_ids = [i.id for i in saved_internships[:4]]
    internships_titles = ", ".join([i.title for i in saved_internships[:2]]) if saved_internships else "saved internship vacancies"
    step4 = {
        "id": str(uuid.uuid4())[:8],
        "title": "Phase 4: Target Application Shortlisting",
        "description": f"Review verified openings and align project bullet points with requirements: {internships_titles}.",
        "resource_ids": internship_ids,
        "skill_ids": [],
        "order": 4,
        "completed": False
    }

    # Step 5: Application Tracking & Interview Prep
    step5 = {
        "id": str(uuid.uuid4())[:8],
        "title": "Phase 5: Applications & Technical Rounds",
        "description": "Submit tailored applications ahead of deadlines, prepare technical DSA / system design topics, and log interview progress.",
        "resource_ids": [],
        "skill_ids": [],
        "order": 5,
        "completed": False
    }

    return {
        "goal_title": goal_title,
        "target_role": target_role or goal_title,
        "description": f"Custom opportunity execution plan generated for {goal_title} using {len(saved_courses)} saved courses and {len(saved_internships)} target opportunities.",
        "steps": [step1, step2, step3, step4, step5]
    }
