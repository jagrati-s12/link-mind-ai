from typing import Dict, Any, List, Tuple
from app.models import Resource, UserProfile, Resume, UserSkill

def calculate_recommendation(
    resource: Resource,
    profile: UserProfile | None,
    user_skills: List[UserSkill],
    resume: Resume | None
) -> Dict[str, Any]:
    """
    Computes an explainable, transparent recommendation based on the formula:
    S = 0.35*K + 0.25*P + 0.20*G + 0.10*L + 0.10*C
    Separates hard eligibility checks from the relevance fit score.
    """
    # 1. Collect user's known skills (from explicit user_skills and parsed resume)
    user_skill_names = set(us.skill.name.lower() for us in user_skills if us.skill)
    if resume and resume.parsed_data:
        parsed = resume.parsed_data
        for s in parsed.get("technical_skills", []) + parsed.get("frameworks", []) + parsed.get("tools", []):
            user_skill_names.add(s.lower())

    required_skills = [s.lower() for s in (resource.required_skills or [])]
    taught_skills = [s.lower() for s in (resource.taught_skills or [])]

    # K: Required skill alignment (0 - 100)
    matching_skills = []
    missing_skills = []
    if required_skills:
        for req in required_skills:
            if any(req in u or u in req for u in user_skill_names):
                matching_skills.append(req.title())
            else:
                missing_skills.append(req.title())
        skill_score = (len(matching_skills) / len(required_skills)) * 100.0
    else:
        # If no explicit required skills listed, look at title overlap or default neutral
        skill_score = 65.0

    # P: Relevance of projects and experience (0 - 100)
    project_score = 50.0
    if resume and resume.parsed_data:
        projects = resume.parsed_data.get("projects", [])
        if projects:
            proj_text = " ".join([p.get("title", "") + " " + p.get("description", "") for p in projects]).lower()
            overlap_count = sum(1 for req in required_skills if req in proj_text)
            if overlap_count > 0:
                project_score = min(100.0, 60.0 + overlap_count * 15.0)
            else:
                project_score = 60.0
    
    # G: Alignment with career goals & target roles (0 - 100)
    goal_score = 50.0
    target_roles = (profile.target_roles if profile and profile.target_roles else [])
    career_goals = (profile.career_goals if profile and profile.career_goals else "").lower()
    res_title_lower = (resource.title or "").lower()
    res_org_lower = (resource.organization or "").lower()

    if target_roles:
        matched_role = False
        for role in target_roles:
            r_low = role.lower()
            if any(term in res_title_lower for term in r_low.split()):
                matched_role = True
                break
        goal_score = 90.0 if matched_role else 55.0
    elif career_goals:
        goal_score = 75.0 if any(w in career_goals for w in res_title_lower.split()) else 50.0

    # L: Learning value and skill-gap fit (0 - 100)
    learning_score = 60.0
    if resource.type in ("course", "certification", "project"):
        # For courses: gives high score if it teaches skills the user is missing
        if taught_skills:
            useful_gap_skills = [ts for ts in taught_skills if not any(ts in u for u in user_skill_names)]
            learning_score = 90.0 if useful_gap_skills else 50.0
    else:
        # For internships: gives higher score if missing skills is small and manageable (1-3)
        if len(missing_skills) == 0:
            learning_score = 80.0
        elif 1 <= len(missing_skills) <= 3:
            learning_score = 90.0
        else:
            learning_score = 50.0

    # C: Practical fit (location, preferences) (0 - 100)
    practical_score = 70.0
    res_loc = (resource.location or "").lower()
    pref_locs = [l.lower() for l in (profile.preferred_locations if profile and profile.preferred_locations else [])]
    if "remote" in res_loc:
        practical_score = 95.0
    elif any(pref in res_loc for pref in pref_locs if pref):
        practical_score = 90.0
    elif res_loc:
        practical_score = 65.0

    # Compute weighted score: S = 0.35K + 0.25P + 0.20G + 0.10L + 0.10C
    fit_score = (0.35 * skill_score) + (0.25 * project_score) + (0.20 * goal_score) + (0.10 * learning_score) + (0.10 * practical_score)
    fit_score = round(max(0.0, min(100.0, fit_score)), 1)

    # Hard eligibility check (independent of relevance score)
    eligibility_status = "needs_verification"
    elig_data = resource.eligibility or {}
    
    # Check graduation year
    if resume and resume.parsed_data:
        user_grad_year = resume.parsed_data.get("graduation_year")
        req_grad = str(elig_data.get("graduation_years", "") or "")
        if req_grad and user_grad_year:
            if str(user_grad_year) in req_grad:
                eligibility_status = "verified_eligible"
            elif any(y in req_grad for y in ["2023", "2024", "2025", "2026", "2027"]) and str(user_grad_year) not in req_grad:
                eligibility_status = "ineligible"

    # Explanations
    explanation_parts = []
    if matching_skills:
        explanation_parts.append(f"Matching skills ({', '.join(matching_skills[:3])}) align well with your verified experience.")
    if missing_skills:
        explanation_parts.append(f"Opportunity requires skills to strengthen: {', '.join(missing_skills[:3])}.")
    if project_score >= 70:
        explanation_parts.append("Your portfolio projects provide relevant practical evidence.")
    if not explanation_parts:
        explanation_parts.append("General opportunity match based on role title and career focus.")
    
    explanation = " ".join(explanation_parts)

    # Next steps
    next_steps = []
    if missing_skills:
        next_steps.append(f"Review or enroll in courses covering {missing_skills[0]}.")
        if len(missing_skills) > 1:
            next_steps.append(f"Build a focused project applying {missing_skills[1]}.")
    else:
        next_steps.append("Your technical skill requirements are fully satisfied.")

    if resource.deadline:
        next_steps.append(f"Verify application deadline ({resource.deadline}) and submit materials.")
    else:
        next_steps.append("Verify deadline on official portal and prepare resume.")

    return {
        "fit_score": fit_score,
        "skill_score": round(skill_score, 1),
        "project_score": round(project_score, 1),
        "goal_score": round(goal_score, 1),
        "learning_score": round(learning_score, 1),
        "practical_score": round(practical_score, 1),
        "explanation": explanation,
        "matching_skills": matching_skills,
        "missing_skills": missing_skills,
        "eligibility_status": eligibility_status,
        "suggested_next_steps": next_steps
    }
