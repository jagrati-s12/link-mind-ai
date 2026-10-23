import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models import Source, Resource, Collection, UserProfile, Resume, UserSkill, Recommendation, Application, CourseProgress
from app.services.fetcher import fetch_url_content, extract_document_file
from app.services.ai_adapter import extract_structured_opportunities
from app.services.matcher import calculate_recommendation
from app.services.relationship_engine import auto_connect_resources
from app.services.learning_engine import get_few_shot_prompt_examples

logger = logging.getLogger(__name__)

DEFAULT_COLLECTIONS = [
    {"name": "AI & Machine Learning", "description": "Courses, internships & projects in AI/ML, PyTorch, LLMs", "icon": "sparkles", "color": "purple"},
    {"name": "Core Software Engineering", "description": "Backend, DSA, System Design, Core CS", "icon": "code", "color": "blue"},
    {"name": "Data Science", "description": "Data analysis, SQL, Analytics, Machine Learning", "icon": "database", "color": "emerald"},
    {"name": "Web Development", "description": "Frontend, Full-stack, React, Node, Web APIs", "icon": "globe", "color": "cyan"},
    {"name": "Cloud & DevOps", "description": "AWS, Docker, Kubernetes, CI/CD, Infrastructure", "icon": "cloud", "color": "sky"},
    {"name": "Internships", "description": "All extracted internship listings and portals", "icon": "briefcase", "color": "amber"},
    {"name": "Jobs", "description": "Full-time and engineering job positions", "icon": "building", "color": "emerald"},
    {"name": "Hackathons", "description": "Devpost, MLH, and open hackathon competitions", "icon": "trophy", "color": "orange"},
    {"name": "Courses", "description": "All saved learning courses and tutorials", "icon": "book-open", "color": "indigo"},
]

def ensure_default_collections(db: Session, user_id: int) -> List[Collection]:
    existing = db.query(Collection).filter(Collection.user_id == user_id).all()
    existing_names = {c.name for c in existing}
    created = list(existing)
    
    for item in DEFAULT_COLLECTIONS:
        if item["name"] not in existing_names:
            c = Collection(
                user_id=user_id,
                name=item["name"],
                description=item["description"],
                icon=item["icon"],
                color=item["color"],
                is_system=True
            )
            db.add(c)
            created.append(c)
    db.commit()
    return created

def match_collections_for_resource(resource_dict: Dict[str, Any], collections: List[Collection]) -> List[Collection]:
    """
    Categorizes resource into relevant folders based on type and technical keywords.
    One resource can belong to multiple folders!
    """
    matched = []
    text_corpus = (
        (resource_dict.get("title") or "") + " " +
        (resource_dict.get("description") or "") + " " +
        " ".join(resource_dict.get("required_skills") or []) + " " +
        " ".join(resource_dict.get("taught_skills") or [])
    ).lower()

    res_type = resource_dict.get("type", "").lower()

    for col in collections:
        c_name = col.name.lower()
        if "internship" in c_name and res_type == "internship":
            matched.append(col)
        elif "jobs" in c_name and res_type == "job":
            matched.append(col)
        elif "hackathon" in c_name and res_type == "hackathon":
            matched.append(col)
        elif "course" in c_name and res_type in ("course", "certification"):
            matched.append(col)
        elif "ai & machine learning" in c_name and any(k in text_corpus for k in ["ai", "machine learning", "deep learning", "pytorch", "tensorflow", "nlp", "llm", "scikit-learn"]):
            matched.append(col)
        elif "core software engineering" in c_name and any(k in text_corpus for k in ["software engineer", "backend", "system design", "data structures", "algorithms", "dsa", "c++", "java", "go", "rust"]):
            matched.append(col)
        elif "data science" in c_name and any(k in text_corpus for k in ["data science", "data analyst", "pandas", "numpy", "sql", "analytics", "statistics"]):
            matched.append(col)
        elif "web development" in c_name and any(k in text_corpus for k in ["web", "frontend", "full stack", "react", "vue", "javascript", "typescript", "html", "css", "next.js"]):
            matched.append(col)
        elif "cloud & devops" in c_name and any(k in text_corpus for k in ["cloud", "devops", "aws", "gcp", "azure", "docker", "kubernetes", "ci/cd"]):
            matched.append(col)

    return matched

async def process_source(db: Session, source_id: int) -> Source:
    """
    Runs end-to-end ingestion pipeline:
    1. Fetches/reads content
    2. Runs AI extraction to discover opportunities
    3. Persists individual Resource rows linked to this Source
    4. Automatically organizes into collections
    5. Calculates personalized recommendations
    6. Connects related resources
    """
    source = db.query(Source).filter(Source.id == source_id).first()
    if not source:
        raise ValueError(f"Source {source_id} not found.")

    source.extraction_status = "processing"
    db.commit()

    # Step 1: Fetch
    if source.original_url:
        fetch_res = await fetch_url_content(source.original_url)
    elif source.source_type in ("pdf", "docx", "text") and source.raw_content:
        # Uploaded file content already in raw_content or file path
        fetch_res = type("FetchResult", (), {
            "content": source.raw_content,
            "title": source.title,
            "mime_type": source.mime_type,
            "content_hash": source.content_hash,
            "error": None
        })()
    else:
        fetch_res = type("FetchResult", (), {
            "content": "",
            "title": source.title,
            "mime_type": "text/plain",
            "content_hash": None,
            "error": "No URL or content provided for source."
        })()

    if fetch_res.error:
        source.extraction_status = "failed"
        source.error_message = fetch_res.error
        db.commit()
        return source

    source.raw_content = fetch_res.content
    source.title = fetch_res.title or source.title
    source.mime_type = fetch_res.mime_type or source.mime_type
    source.content_hash = fetch_res.content_hash

    # Step 2: AI Structured Extraction (with Continuous Model Learning from Human Feedback)
    few_shot = get_few_shot_prompt_examples(db)

    try:
        raw_opps = await extract_structured_opportunities(
            source.raw_content,
            source_title=source.title,
            source_url=source.original_url or "",
            few_shot_guidance=few_shot
        )
    except Exception as e:
        logger.exception("AI Extraction failed")
        source.extraction_status = "failed"
        source.error_message = f"AI extraction error: {str(e)}"
        db.commit()
        return source

    if not raw_opps:
        source.extraction_status = "partial"
        source.error_message = "No specific courses or opportunities identified in the content."
        db.commit()
        return source

    # Step 3: Ensure User Collections exist
    user_collections = ensure_default_collections(db, source.user_id)

    # Step 4: Fetch User Profile, Skills, and Active Resume for instant matching
    profile = db.query(UserProfile).filter(UserProfile.user_id == source.user_id).first()
    active_resume = db.query(Resume).filter(Resume.user_id == source.user_id, Resume.is_active == True).first()
    user_skills = db.query(UserSkill).filter(UserSkill.user_id == source.user_id).all()

    # Step 5: Persist each extracted opportunity as an individual canonical Resource
    for opp_data in raw_opps:
        # Check if already saved under same direct URL for this user
        existing_res = None
        if opp_data.get("direct_url"):
            existing_res = db.query(Resource).filter(
                Resource.user_id == source.user_id,
                Resource.direct_url == opp_data["direct_url"]
            ).first()

        if existing_res:
            # Update non-destructive fields
            if not existing_res.deadline and opp_data.get("deadline"):
                existing_res.deadline = opp_data["deadline"]
            if not existing_res.compensation and opp_data.get("compensation"):
                existing_res.compensation = opp_data["compensation"]
            res = existing_res
        else:
            res = Resource(
                user_id=source.user_id,
                source_id=source.id,
                type=opp_data.get("type", "internship"),
                title=opp_data.get("title", "Untitled Opportunity"),
                organization=opp_data.get("organization"),
                description=opp_data.get("description", ""),
                direct_url=opp_data.get("direct_url"),
                location=opp_data.get("location"),
                compensation=opp_data.get("compensation"),
                duration=opp_data.get("duration"),
                deadline=opp_data.get("deadline"),
                eligibility=opp_data.get("eligibility", {}),
                required_skills=opp_data.get("required_skills", []),
                taught_skills=opp_data.get("taught_skills", []),
                source_evidence=opp_data.get("source_evidence", []),
                confidence=opp_data.get("confidence", 0.9),
                verification_status=opp_data.get("verification_status", "needs_review"),
                notes=opp_data.get("notes", "")
            )
            db.add(res)
            db.flush()

        # Connect to collections
        matched_cols = match_collections_for_resource(opp_data, user_collections)
        for col in matched_cols:
            if col not in res.collections:
                res.collections.append(col)

        # Generate recommendation
        rec_data = calculate_recommendation(res, profile, user_skills, active_resume)
        existing_rec = db.query(Recommendation).filter(
            Recommendation.user_id == source.user_id,
            Recommendation.resource_id == res.id
        ).first()

        if existing_rec:
            for k, v in rec_data.items():
                setattr(existing_rec, k, v)
            if active_resume:
                existing_rec.resume_id = active_resume.id
        else:
            new_rec = Recommendation(
                user_id=source.user_id,
                resource_id=res.id,
                resume_id=active_resume.id if active_resume else None,
                **rec_data
            )
            db.add(new_rec)

        # Auto-create Application record for internships & jobs in "Saved" status
        if res.type in ("internship", "job"):
            existing_app = db.query(Application).filter(
                Application.user_id == source.user_id,
                Application.resource_id == res.id
            ).first()
            if not existing_app:
                new_app = Application(
                    user_id=source.user_id,
                    resource_id=res.id,
                    status="Saved",
                    deadline=res.deadline,
                    notes=""
                )
                db.add(new_app)

        # Auto-create CourseProgress record for courses & certifications in "In Progress" status
        if res.type in ("course", "certification"):
            existing_cp = db.query(CourseProgress).filter(
                CourseProgress.user_id == source.user_id,
                CourseProgress.resource_id == res.id
            ).first()
            if not existing_cp:
                new_cp = CourseProgress(
                    user_id=source.user_id,
                    resource_id=res.id,
                    status="In Progress",
                    progress_percentage=0,
                    current_module="Introduction",
                    target_completion_date=res.deadline,
                    notes=""
                )
                db.add(new_cp)

        db.commit()

        # Discover relationships
        try:
            auto_connect_resources(db, source.user_id, res.id)
        except Exception:
            logger.warning("Auto connect resources failed for %d", res.id)

    source.extraction_status = "completed"
    db.commit()
    return source
