from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Text, Float, ForeignKey, Table, JSON, UniqueConstraint
)
from sqlalchemy.orm import relationship
from app.core.db import Base

def utc_now():
    return datetime.now(timezone.utc)

# Association table for Resource <-> Collection
resource_collections = Table(
    "resource_collections",
    Base.metadata,
    Column("resource_id", Integer, ForeignKey("resources.id", ondelete="CASCADE"), primary_key=True),
    Column("collection_id", Integer, ForeignKey("collections.id", ondelete="CASCADE"), primary_key=True),
    Column("added_at", DateTime, default=utc_now)
)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), default="")
    is_active = Column(Boolean, default=True)
    totp_secret = Column(String(64), nullable=True)
    is_totp_enabled = Column(Boolean, default=False)
    totp_temp_secret = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    profile = relationship("UserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    resumes = relationship("Resume", back_populates="user", cascade="all, delete-orphan")
    sources = relationship("Source", back_populates="user", cascade="all, delete-orphan")
    resources = relationship("Resource", back_populates="user", cascade="all, delete-orphan")
    collections = relationship("Collection", back_populates="user", cascade="all, delete-orphan")
    user_skills = relationship("UserSkill", back_populates="user", cascade="all, delete-orphan")
    recommendations = relationship("Recommendation", back_populates="user", cascade="all, delete-orphan")
    applications = relationship("Application", back_populates="user", cascade="all, delete-orphan")
    course_progress = relationship("CourseProgress", back_populates="user", cascade="all, delete-orphan")
    roadmaps = relationship("Roadmap", back_populates="user", cascade="all, delete-orphan")
    import_jobs = relationship("ImportJob", back_populates="user", cascade="all, delete-orphan")

class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    career_goals = Column(Text, default="")
    target_roles = Column(JSON, default=list)            # e.g. ["AI Engineer", "Backend Developer"]
    preferred_locations = Column(JSON, default=list)     # e.g. ["Remote", "Bengaluru", "San Francisco"]
    learning_goals = Column(JSON, default=list)          # e.g. ["Master PyTorch", "System Design"]
    experience_level = Column(String(100), default="Entry-level")
    bio = Column(Text, default="")
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    user = relationship("User", back_populates="profile")

class Resume(Base):
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    version_name = Column(String(255), default="Primary Resume")
    file_path = Column(String(500), nullable=True)
    raw_text = Column(Text, default="")
    parsed_data = Column(JSON, default=dict) # skills, education, graduation_year, experience, projects, etc.
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utc_now)

    user = relationship("User", back_populates="resumes")

class Source(Base):
    __tablename__ = "sources"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    original_url = Column(String(2048), nullable=True, index=True)
    source_type = Column(String(50), default="url") # url, pdf, docx, text
    title = Column(String(500), default="Untitled Source")
    raw_content = Column(Text, default="")
    mime_type = Column(String(100), default="text/html")
    content_hash = Column(String(64), index=True, nullable=True)
    extraction_status = Column(String(50), default="pending") # pending, completed, failed, partial
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    user = relationship("User", back_populates="sources")
    resources = relationship("Resource", back_populates="source", cascade="all, delete-orphan")
    import_jobs = relationship("ImportJob", back_populates="source")

class Resource(Base):
    __tablename__ = "resources"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    source_id = Column(Integer, ForeignKey("sources.id", ondelete="SET NULL"), nullable=True, index=True)
    type = Column(String(50), default="resource", index=True) # course, internship, job, project, certification, research, resource
    title = Column(String(500), nullable=False, index=True)
    organization = Column(String(255), nullable=True, index=True)
    description = Column(Text, default="")
    direct_url = Column(String(2048), nullable=True)
    location = Column(String(255), nullable=True)
    compensation = Column(String(255), nullable=True)
    duration = Column(String(255), nullable=True)
    deadline = Column(String(100), nullable=True)
    eligibility = Column(JSON, default=dict)        # {degree, graduation_years, experience, status}
    required_skills = Column(JSON, default=list)    # ["Python", "PyTorch"]
    taught_skills = Column(JSON, default=list)      # ["FastAPI", "Docker"]
    source_evidence = Column(JSON, default=list)    # ["extracted quote 1", ...]
    confidence = Column(Float, default=1.0)
    verification_status = Column(String(50), default="needs_review") # needs_review, verified, expired, closed, unknown
    is_archived = Column(Boolean, default=False)
    notes = Column(Text, default="")
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    user = relationship("User", back_populates="resources")
    source = relationship("Source", back_populates="resources")
    collections = relationship("Collection", secondary=resource_collections, back_populates="resources")
    skills = relationship("ResourceSkill", back_populates="resource", cascade="all, delete-orphan")
    recommendations = relationship("Recommendation", back_populates="resource", cascade="all, delete-orphan")
    applications = relationship("Application", back_populates="resource", cascade="all, delete-orphan")
    course_progress = relationship("CourseProgress", back_populates="resource", cascade="all, delete-orphan")
    outward_relations = relationship("ResourceRelation", foreign_keys="ResourceRelation.source_resource_id", cascade="all, delete-orphan")
    inward_relations = relationship("ResourceRelation", foreign_keys="ResourceRelation.target_resource_id", cascade="all, delete-orphan")

class Collection(Base):
    __tablename__ = "collections"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, default="")
    color = Column(String(50), default="blue")
    icon = Column(String(50), default="folder")
    is_smart = Column(Boolean, default=False)
    rules = Column(JSON, default=dict) # e.g. {"category": "AI & Machine Learning", "types": ["course", "internship"]}
    is_system = Column(Boolean, default=False)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    user = relationship("User", back_populates="collections")
    resources = relationship("Resource", secondary=resource_collections, back_populates="collections")

class Skill(Base):
    __tablename__ = "skills"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False)
    category = Column(String(100), default="General")
    aliases = Column(JSON, default=list)

    resource_skills = relationship("ResourceSkill", back_populates="skill")
    user_skills = relationship("UserSkill", back_populates="skill")

class ResourceSkill(Base):
    __tablename__ = "resource_skills"

    id = Column(Integer, primary_key=True, index=True)
    resource_id = Column(Integer, ForeignKey("resources.id", ondelete="CASCADE"), nullable=False, index=True)
    skill_id = Column(Integer, ForeignKey("skills.id", ondelete="CASCADE"), nullable=False, index=True)
    relationship_type = Column(String(50), default="required") # required, taught, recommended

    resource = relationship("Resource", back_populates="skills")
    skill = relationship("Skill", back_populates="resource_skills")

class UserSkill(Base):
    __tablename__ = "user_skills"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    skill_id = Column(Integer, ForeignKey("skills.id", ondelete="CASCADE"), nullable=False, index=True)
    proficiency_level = Column(String(50), default="intermediate") # beginner, intermediate, advanced, expert
    evidence = Column(JSON, default=list) # project names, bullet points
    verified_by_user = Column(Boolean, default=False)

    user = relationship("User", back_populates="user_skills")
    skill = relationship("Skill", back_populates="user_skills")

class ResourceRelation(Base):
    __tablename__ = "resource_relations"

    id = Column(Integer, primary_key=True, index=True)
    source_resource_id = Column(Integer, ForeignKey("resources.id", ondelete="CASCADE"), nullable=False, index=True)
    target_resource_id = Column(Integer, ForeignKey("resources.id", ondelete="CASCADE"), nullable=False, index=True)
    relation_type = Column(String(50), default="prepares_for") # prepares_for, requires_same_skills, duplicate_of, supersedes
    confidence = Column(Float, default=1.0)
    rationale = Column(Text, default="")
    created_at = Column(DateTime, default=utc_now)

class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    resource_id = Column(Integer, ForeignKey("resources.id", ondelete="CASCADE"), nullable=False, index=True)
    resume_id = Column(Integer, ForeignKey("resumes.id", ondelete="SET NULL"), nullable=True)
    fit_score = Column(Float, default=0.0) # S = 0.35K + 0.25P + 0.20G + 0.10L + 0.10C
    skill_score = Column(Float, default=0.0)
    project_score = Column(Float, default=0.0)
    goal_score = Column(Float, default=0.0)
    learning_score = Column(Float, default=0.0)
    practical_score = Column(Float, default=0.0)
    explanation = Column(Text, default="")
    matching_skills = Column(JSON, default=list)
    missing_skills = Column(JSON, default=list)
    eligibility_status = Column(String(50), default="needs_verification") # verified_eligible, needs_verification, ineligible
    suggested_next_steps = Column(JSON, default=list)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    user = relationship("User", back_populates="recommendations")
    resource = relationship("Resource", back_populates="recommendations")

class Application(Base):
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    resource_id = Column(Integer, ForeignKey("resources.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(50), default="Saved") # Saved, Shortlisted, Preparing, Applied, Assessment, Interview, Offer, Rejected, Withdrawn, Closed
    application_date = Column(String(50), nullable=True)
    deadline = Column(String(50), nullable=True)
    notes = Column(Text, default="")
    follow_up_date = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    user = relationship("User", back_populates="applications")
    resource = relationship("Resource", back_populates="applications")

class CourseProgress(Base):
    __tablename__ = "course_progress"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    resource_id = Column(Integer, ForeignKey("resources.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(50), default="In Progress") # Not Started, In Progress, Halfway, Reviewing, Completed, Certified
    progress_percentage = Column(Integer, default=0)    # 0 - 100
    current_module = Column(String(255), default="")    # e.g. "Course 3: Prepare Data for Exploration"
    target_completion_date = Column(String(50), nullable=True)
    notes = Column(Text, default="")
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    user = relationship("User", back_populates="course_progress")
    resource = relationship("Resource", back_populates="course_progress")

class Roadmap(Base):
    __tablename__ = "roadmaps"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    goal_title = Column(String(255), nullable=False)
    description = Column(Text, default="")
    target_role = Column(String(255), default="")
    steps = Column(JSON, default=list) # [{id, title, description, resource_ids, skill_ids, order, completed}]
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    user = relationship("User", back_populates="roadmaps")

class ImportJob(Base):
    __tablename__ = "import_jobs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    source_id = Column(Integer, ForeignKey("sources.id", ondelete="SET NULL"), nullable=True)
    status = Column(String(50), default="pending") # pending, processing, completed, failed
    total_items = Column(Integer, default=0)
    processed_items = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    result_summary = Column(JSON, default=dict)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    user = relationship("User", back_populates="import_jobs")
    source = relationship("Source", back_populates="import_jobs")
