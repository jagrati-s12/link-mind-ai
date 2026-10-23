export type ResourceType = 'course' | 'internship' | 'job' | 'project' | 'certification' | 'research' | 'hackathon' | 'resource';

export type VerificationStatus = 'needs_review' | 'verified' | 'expired' | 'closed' | 'unknown';

export type ApplicationStatus = 'Saved' | 'Shortlisted' | 'Preparing' | 'Applied' | 'Assessment' | 'Interview' | 'Offer' | 'Rejected' | 'Withdrawn' | 'Closed';

export interface CollectionMini {
  id: number;
  name: string;
  color: string;
  icon: string;
}

export interface RecommendationMini {
  id: number;
  fit_score: number;
  skill_score: number;
  explanation: string;
  matching_skills: string[];
  missing_skills: string[];
  eligibility_status: string;
}

export interface ApplicationMini {
  id: number;
  status: ApplicationStatus;
  deadline?: string | null;
  application_date?: string | null;
}

export interface Resource {
  id: number;
  user_id: number;
  source_id?: number | null;
  type: ResourceType;
  title: string;
  organization?: string | null;
  description: string;
  direct_url?: string | null;
  location?: string | null;
  compensation?: string | null;
  duration?: string | null;
  deadline?: string | null;
  eligibility: {
    degree?: string;
    graduation_years?: string;
    experience?: string;
    status?: string;
    [key: string]: any;
  };
  required_skills: string[];
  taught_skills: string[];
  source_evidence: string[];
  confidence: number;
  verification_status: VerificationStatus;
  is_archived: boolean;
  notes: string;
  created_at: string;
  updated_at: string;
  source_url?: string | null;
  collections: CollectionMini[];
  recommendation?: RecommendationMini | null;
  application?: ApplicationMini | null;
}

export interface Collection {
  id: number;
  user_id: number;
  name: string;
  description: string;
  color: string;
  icon: string;
  is_smart: boolean;
  rules: Record<string, any>;
  is_system: boolean;
  created_at: string;
  updated_at: string;
  resource_count: number;
}

export interface Source {
  id: number;
  user_id: number;
  original_url?: string | null;
  source_type: string;
  title: string;
  mime_type: string;
  extraction_status: 'pending' | 'processing' | 'completed' | 'failed' | 'partial';
  error_message?: string | null;
  created_at: string;
  updated_at: string;
  resource_count: number;
}

export interface DashboardStats {
  courses_saved: number;
  internships_saved: number;
  jobs_saved: number;
  hackathons_saved: number;
  strong_matches: number;
  upcoming_deadlines: number;
  total_resources: number;
  total_collections: number;
  applications_count: number;
}

export interface UserProfile {
  id: number;
  user_id: number;
  career_goals: string;
  target_roles: string[];
  preferred_locations: string[];
  learning_goals: string[];
  experience_level: string;
  bio: string;
  created_at: string;
  updated_at: string;
}

export interface Resume {
  id: number;
  user_id: number;
  version_name: string;
  file_path?: string | null;
  raw_text: string;
  parsed_data: {
    technical_skills?: string[];
    frameworks?: string[];
    tools?: string[];
    education?: any[];
    graduation_year?: number | null;
    projects?: any[];
    experience?: any[];
    career_interests?: string[];
    preferred_locations?: string[];
  };
  is_active: boolean;
  created_at: string;
}

export interface UserSkill {
  id: number;
  user_id: number;
  skill_id: number;
  skill_name: string;
  proficiency_level: string;
  evidence: string[];
  verified_by_user: boolean;
}

export interface SkillGapData {
  target_role: string;
  required_skills: string[];
  possessed_skills: string[];
  missing_skills: string[];
  recommended_courses: {
    id: number;
    title: string;
    organization?: string;
    teaches: string[];
    direct_url?: string;
  }[];
  recommended_internships: {
    id: number;
    title: string;
    organization?: string;
    deadline?: string;
    direct_url?: string;
  }[];
}

export interface RoadmapStep {
  id: string;
  title: string;
  description: string;
  resource_ids: number[];
  skill_ids: number[];
  order: number;
  completed: boolean;
}

export interface Roadmap {
  id: number;
  user_id: number;
  goal_title: string;
  description: string;
  target_role: string;
  steps: RoadmapStep[];
  created_at: string;
  updated_at: string;
}

export interface Application {
  id: number;
  user_id: number;
  resource_id: number;
  status: ApplicationStatus;
  application_date?: string | null;
  deadline?: string | null;
  notes: string;
  follow_up_date?: string | null;
  created_at: string;
  updated_at: string;
  resource?: Resource | null;
}

export type CourseProgressStatus = 'Not Started' | 'In Progress' | 'Halfway' | 'Reviewing' | 'Completed' | 'Certified';

export interface CourseProgress {
  id: number;
  user_id: number;
  resource_id: number;
  status: CourseProgressStatus;
  progress_percentage: number;
  current_module: string;
  target_completion_date?: string | null;
  notes: string;
  created_at: string;
  updated_at: string;
  resource?: Resource | null;
}

export interface User {
  id: number;
  email: string;
  full_name: string;
  is_active: boolean;
  is_totp_enabled: boolean;
  created_at: string;
  profile?: UserProfile;
}

export interface LoginResponse {
  access_token?: string;
  token_type?: string;
  user_id?: number;
  email?: string;
  full_name?: string;
  requires_2fa: boolean;
  temp_token?: string;
  is_totp_enabled: boolean;
}

export interface TOTPSetupResponse {
  secret: string;
  otpauth_url: string;
  qr_code: string;
}

export interface TOTPStatusResponse {
  is_totp_enabled: boolean;
  email: string;
}

export interface ListingFeedback {
  id: number;
  user_id: number;
  resource_id: number;
  is_correct: boolean;
  original_type: string;
  corrected_type?: string | null;
  original_title: string;
  corrected_title?: string | null;
  domain: string;
  reason: string;
  notes: string;
  created_at: string;
}

export interface ModelLearningStats {
  total_feedback_count: number;
  verified_accurate_count: number;
  user_corrections_count: number;
  accuracy_rate: number;
  active_few_shot_examples: number;
  recent_corrections: ListingFeedback[];
}
