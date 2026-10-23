from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, EmailStr, Field

# ----------------- Auth & User -----------------
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    full_name: Optional[str] = "Student"

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    email: str
    full_name: str

class UserProfileUpdate(BaseModel):
    career_goals: Optional[str] = None
    target_roles: Optional[List[str]] = None
    preferred_locations: Optional[List[str]] = None
    learning_goals: Optional[List[str]] = None
    experience_level: Optional[str] = None
    bio: Optional[str] = None

class UserProfileOut(BaseModel):
    id: int
    user_id: int
    career_goals: str = ""
    target_roles: List[str] = []
    preferred_locations: List[str] = []
    learning_goals: List[str] = []
    experience_level: str = "Entry-level"
    bio: str = ""
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class UserOut(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    is_active: bool
    created_at: datetime
    profile: Optional[UserProfileOut] = None

    class Config:
        from_attributes = True

# ----------------- Resume -----------------
class ResumeParsedData(BaseModel):
    technical_skills: List[str] = []
    frameworks: List[str] = []
    tools: List[str] = []
    education: List[Dict[str, Any]] = []
    graduation_year: Optional[int] = None
    projects: List[Dict[str, Any]] = []
    experience: List[Dict[str, Any]] = []
    career_interests: List[str] = []
    preferred_locations: List[str] = []

class ResumeOut(BaseModel):
    id: int
    user_id: int
    version_name: str
    file_path: Optional[str]
    raw_text: str
    parsed_data: Dict[str, Any]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

# ----------------- Source -----------------
class SourceCreateUrl(BaseModel):
    url: str

class SourceBulkCreate(BaseModel):
    urls: List[str]

class SourceOut(BaseModel):
    id: int
    user_id: int
    original_url: Optional[str] = None
    source_type: str
    title: str
    mime_type: str
    extraction_status: str
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    resource_count: Optional[int] = 0

    class Config:
        from_attributes = True

# ----------------- Resource -----------------
class ResourceBase(BaseModel):
    type: str = "internship" # course, internship, job, project, certification, research, resource
    title: str
    organization: Optional[str] = None
    description: Optional[str] = ""
    direct_url: Optional[str] = None
    location: Optional[str] = None
    compensation: Optional[str] = None
    duration: Optional[str] = None
    deadline: Optional[str] = None
    eligibility: Optional[Dict[str, Any]] = {}
    required_skills: Optional[List[str]] = []
    taught_skills: Optional[List[str]] = []
    source_evidence: Optional[List[str]] = []
    confidence: Optional[float] = 1.0
    verification_status: Optional[str] = "needs_review"
    notes: Optional[str] = ""

class ResourceCreate(ResourceBase):
    source_id: Optional[int] = None
    collection_ids: Optional[List[int]] = []

class ResourceUpdate(BaseModel):
    title: Optional[str] = None
    type: Optional[str] = None
    organization: Optional[str] = None
    description: Optional[str] = None
    direct_url: Optional[str] = None
    location: Optional[str] = None
    compensation: Optional[str] = None
    duration: Optional[str] = None
    deadline: Optional[str] = None
    eligibility: Optional[Dict[str, Any]] = None
    required_skills: Optional[List[str]] = None
    taught_skills: Optional[List[str]] = None
    verification_status: Optional[str] = None
    notes: Optional[str] = None
    is_archived: Optional[bool] = None
    collection_ids: Optional[List[int]] = None

class CollectionMiniOut(BaseModel):
    id: int
    name: str
    color: str
    icon: str

    class Config:
        from_attributes = True

class RecommendationMiniOut(BaseModel):
    id: int
    fit_score: float
    skill_score: float
    explanation: str
    matching_skills: List[str]
    missing_skills: List[str]
    eligibility_status: str

    class Config:
        from_attributes = True

class ApplicationMiniOut(BaseModel):
    id: int
    status: str
    deadline: Optional[str] = None
    application_date: Optional[str] = None

    class Config:
        from_attributes = True

class ResourceOut(BaseModel):
    id: int
    user_id: int
    source_id: Optional[int] = None
    type: str
    title: str
    organization: Optional[str] = None
    description: str = ""
    direct_url: Optional[str] = None
    location: Optional[str] = None
    compensation: Optional[str] = None
    duration: Optional[str] = None
    deadline: Optional[str] = None
    eligibility: Dict[str, Any] = {}
    required_skills: List[str] = []
    taught_skills: List[str] = []
    source_evidence: List[str] = []
    confidence: float = 1.0
    verification_status: str = "needs_review"
    is_archived: bool = False
    notes: str = ""
    created_at: datetime
    updated_at: datetime
    source_url: Optional[str] = None
    collections: List[CollectionMiniOut] = []
    recommendation: Optional[RecommendationMiniOut] = None
    application: Optional[ApplicationMiniOut] = None

    class Config:
        from_attributes = True

# ----------------- Collection -----------------
class CollectionCreate(BaseModel):
    name: str
    description: Optional[str] = ""
    color: Optional[str] = "blue"
    icon: Optional[str] = "folder"
    is_smart: Optional[bool] = False
    rules: Optional[Dict[str, Any]] = {}

class CollectionUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    color: Optional[str] = None
    icon: Optional[str] = None
    is_smart: Optional[bool] = None
    rules: Optional[Dict[str, Any]] = None

class CollectionOut(BaseModel):
    id: int
    user_id: int
    name: str
    description: str = ""
    color: str = "blue"
    icon: str = "folder"
    is_smart: bool = False
    rules: Dict[str, Any] = {}
    is_system: bool = False
    created_at: datetime
    updated_at: datetime
    resource_count: Optional[int] = 0

    class Config:
        from_attributes = True

# ----------------- Skills -----------------
class SkillOut(BaseModel):
    id: int
    name: str
    category: str
    aliases: List[str]

    class Config:
        from_attributes = True

class UserSkillCreate(BaseModel):
    skill_name: str
    proficiency_level: Optional[str] = "intermediate"
    evidence: Optional[List[str]] = []
    verified_by_user: Optional[bool] = True

class UserSkillOut(BaseModel):
    id: int
    user_id: int
    skill_id: int
    skill_name: str
    proficiency_level: str
    evidence: List[str]
    verified_by_user: bool

    class Config:
        from_attributes = True

class SkillGapOut(BaseModel):
    target_role: str
    required_skills: List[str]
    possessed_skills: List[str]
    missing_skills: List[str]
    recommended_courses: List[Dict[str, Any]]
    recommended_internships: List[Dict[str, Any]]

# ----------------- Recommendation -----------------
class RecommendationOut(BaseModel):
    id: int
    user_id: int
    resource_id: int
    resume_id: Optional[int] = None
    fit_score: float
    skill_score: float
    project_score: float
    goal_score: float
    learning_score: float
    practical_score: float
    explanation: str
    matching_skills: List[str]
    missing_skills: List[str]
    eligibility_status: str
    suggested_next_steps: List[str]
    created_at: datetime
    resource: Optional[ResourceOut] = None

    class Config:
        from_attributes = True

# ----------------- Application -----------------
class ApplicationCreate(BaseModel):
    resource_id: int
    status: Optional[str] = "Saved"
    application_date: Optional[str] = None
    deadline: Optional[str] = None
    notes: Optional[str] = ""
    follow_up_date: Optional[str] = None

class ApplicationUpdate(BaseModel):
    status: Optional[str] = None
    application_date: Optional[str] = None
    deadline: Optional[str] = None
    notes: Optional[str] = None
    follow_up_date: Optional[str] = None

class ApplicationOut(BaseModel):
    id: int
    user_id: int
    resource_id: int
    status: str
    application_date: Optional[str] = None
    deadline: Optional[str] = None
    notes: str = ""
    follow_up_date: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    resource: Optional[ResourceOut] = None

    class Config:
        from_attributes = True

# ----------------- Roadmap -----------------
class RoadmapStep(BaseModel):
    id: str
    title: str
    description: str
    resource_ids: List[int] = []
    skill_ids: List[int] = []
    order: int
    completed: bool = False

class RoadmapCreate(BaseModel):
    goal_title: str
    description: Optional[str] = ""
    target_role: Optional[str] = ""
    steps: Optional[List[RoadmapStep]] = []

class RoadmapUpdate(BaseModel):
    goal_title: Optional[str] = None
    description: Optional[str] = None
    target_role: Optional[str] = None
    steps: Optional[List[RoadmapStep]] = None

class RoadmapOut(BaseModel):
    id: int
    user_id: int
    goal_title: str
    description: str = ""
    target_role: str = ""
    steps: List[Dict[str, Any]] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# ----------------- Assistant -----------------
class AssistantMessage(BaseModel):
    role: str # user, assistant
    content: str
    created_at: Optional[datetime] = None

class AssistantChatRequest(BaseModel):
    message: str
    history: Optional[List[AssistantMessage]] = []

class AssistantCitation(BaseModel):
    resource_id: int
    title: str
    type: str
    direct_url: Optional[str] = None

class AssistantChatResponse(BaseModel):
    response: str
    citations: List[AssistantCitation] = []
    suggested_actions: List[str] = []

# ----------------- Import Job -----------------
class ImportJobOut(BaseModel):
    id: int
    user_id: int
    source_id: Optional[int] = None
    status: str
    total_items: int
    processed_items: int
    error_message: Optional[str] = None
    result_summary: Dict[str, Any] = {}
    created_at: datetime

    class Config:
        from_attributes = True

# ----------------- Dashboard Stats -----------------
class DashboardStatsOut(BaseModel):
    courses_saved: int
    internships_saved: int
    hackathons_saved: int = 0
    strong_matches: int
    upcoming_deadlines: int
    total_resources: int
    total_collections: int
    applications_count: int
