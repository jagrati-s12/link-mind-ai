import {
  Resource,
  Collection,
  Source,
  DashboardStats,
  UserProfile,
  Resume,
  UserSkill,
  SkillGapData,
  Roadmap,
  Application,
  CourseProgress,
  ListingFeedback,
  ModelLearningStats
} from '../types';

const API_BASE = '/api/v1';

async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  const token = localStorage.getItem('token');
  const headers = new Headers(options?.headers || {});
  
  if (token && !headers.has('Authorization')) {
    headers.set('Authorization', `Bearer ${token}`);
  }
  
  if (!headers.has('Content-Type') && !(options?.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json');
  }

  const response = await fetch(url, { ...options, headers });
  if (!response.ok) {
    let errorDetail = 'API request failed';
    try {
      const errData = await response.json();
      errorDetail = errData.detail || errData.message || errorDetail;
    } catch {
      errorDetail = response.statusText;
    }
    throw new Error(errorDetail);
  }
  return response.json();
}

export const api = {
  // Stats
  getStats: () => fetchJson<DashboardStats>(`${API_BASE}/stats`),

  // Sources & Inbox
  getSources: () => fetchJson<Source[]>(`${API_BASE}/sources`),
  submitUrl: (url: string) => fetchJson<Source>(`${API_BASE}/sources`, {
    method: 'POST',
    body: JSON.stringify({ url })
  }),
  uploadDocument: (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return fetchJson<Source>(`${API_BASE}/sources/upload`, {
      method: 'POST',
      body: formData
    });
  },
  bulkImport: (urls: string[]) => fetchJson<any>(`${API_BASE}/imports`, {
    method: 'POST',
    body: JSON.stringify({ urls })
  }),
  reprocessSource: (id: number) => fetchJson<Source>(`${API_BASE}/sources/${id}/reprocess`, {
    method: 'POST'
  }),
  deleteSource: (id: number) => fetchJson<any>(`${API_BASE}/sources/${id}`, {
    method: 'DELETE'
  }),

  // Resources
  getResources: (params?: { type?: string; collection_id?: number; search?: string }) => {
    const q = new URLSearchParams();
    if (params?.type) q.set('type', params.type);
    if (params?.collection_id) q.set('collection_id', params.collection_id.toString());
    if (params?.search) q.set('search', params.search);
    return fetchJson<Resource[]>(`${API_BASE}/resources?${q.toString()}`);
  },
  getResource: (id: number) => fetchJson<Resource>(`${API_BASE}/resources/${id}`),
  createResource: (data: Partial<Resource>) => fetchJson<Resource>(`${API_BASE}/resources`, {
    method: 'POST',
    body: JSON.stringify(data)
  }),
  updateResource: (id: number, data: Partial<Resource> & { collection_ids?: number[] }) => 
    fetchJson<Resource>(`${API_BASE}/resources/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data)
    }),
  deleteResource: (id: number) => fetchJson<any>(`${API_BASE}/resources/${id}`, {
    method: 'DELETE'
  }),

  // Collections
  getCollections: () => fetchJson<Collection[]>(`${API_BASE}/collections`),
  getCollection: (id: number) => fetchJson<Collection>(`${API_BASE}/collections/${id}`),
  createCollection: (data: { name: string; description?: string; color?: string; icon?: string }) =>
    fetchJson<Collection>(`${API_BASE}/collections`, {
      method: 'POST',
      body: JSON.stringify(data)
    }),
  updateCollection: (id: number, data: Partial<Collection>) =>
    fetchJson<Collection>(`${API_BASE}/collections/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data)
    }),
  deleteCollection: (id: number) => fetchJson<any>(`${API_BASE}/collections/${id}`, {
    method: 'DELETE'
  }),
  addResourceToCollection: (collectionId: number, resourceId: number) =>
    fetchJson<any>(`${API_BASE}/collections/${collectionId}/resources/${resourceId}`, {
      method: 'POST'
    }),
  removeResourceFromCollection: (collectionId: number, resourceId: number) =>
    fetchJson<any>(`${API_BASE}/collections/${collectionId}/resources/${resourceId}`, {
      method: 'DELETE'
    }),

  // Skills
  getUserSkills: () => fetchJson<UserSkill[]>(`${API_BASE}/skills/user`),
  addUserSkill: (data: { skill_name: string; proficiency_level?: string; evidence?: string[] }) =>
    fetchJson<UserSkill>(`${API_BASE}/skills/user`, {
      method: 'POST',
      body: JSON.stringify(data)
    }),
  deleteUserSkill: (id: number) => fetchJson<any>(`${API_BASE}/skills/user/${id}`, {
    method: 'DELETE'
  }),
  getSkillGaps: (role?: string) => {
    const q = role ? `?role=${encodeURIComponent(role)}` : '';
    return fetchJson<SkillGapData>(`${API_BASE}/skills/gaps${q}`);
  },

  // Recommendations
  recalculateRecommendations: () => fetchJson<any>(`${API_BASE}/recommendations/recalculate`, {
    method: 'POST'
  }),

  // Applications (Internships & Jobs)
  getApplications: () => fetchJson<Application[]>(`${API_BASE}/applications`),
  createApplication: (data: { resource_id: number; status?: string; deadline?: string; notes?: string }) =>
    fetchJson<Application>(`${API_BASE}/applications`, {
      method: 'POST',
      body: JSON.stringify(data)
    }),
  updateApplication: (id: number, data: Partial<Application>) =>
    fetchJson<Application>(`${API_BASE}/applications/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data)
    }),
  deleteApplication: (id: number) => fetchJson<any>(`${API_BASE}/applications/${id}`, {
    method: 'DELETE'
  }),

  // Course Progress & Learning Tracker
  getCourseProgress: () => fetchJson<CourseProgress[]>(`${API_BASE}/course-tracker`),
  createCourseProgress: (data: {
    resource_id: number;
    status?: string;
    progress_percentage?: number;
    current_module?: string;
    target_completion_date?: string;
    notes?: string;
  }) =>
    fetchJson<CourseProgress>(`${API_BASE}/course-tracker`, {
      method: 'POST',
      body: JSON.stringify(data)
    }),
  updateCourseProgress: (id: number, data: Partial<CourseProgress>) =>
    fetchJson<CourseProgress>(`${API_BASE}/course-tracker/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data)
    }),
  deleteCourseProgress: (id: number) =>
    fetchJson<any>(`${API_BASE}/course-tracker/${id}`, {
      method: 'DELETE'
    }),

  // Roadmaps
  getRoadmaps: () => fetchJson<Roadmap[]>(`${API_BASE}/roadmaps`),
  getRoadmapCatalog: () => fetchJson<any[]>(`${API_BASE}/roadmaps/catalog`),
  generateRoadmap: (goal_title: string, target_role?: string, goals?: string[]) =>
    fetchJson<Roadmap>(`${API_BASE}/roadmaps/generate`, {
      method: 'POST',
      body: JSON.stringify({ goal_title, target_role, goals })
    }),
  toggleRoadmapStep: (roadmapId: number, stepId: string) =>
    fetchJson<Roadmap>(`${API_BASE}/roadmaps/${roadmapId}/steps/${stepId}/toggle`, {
      method: 'POST'
    }),
  toggleRoadmapSubtopic: (roadmapId: number, stepId: string, topicIdx: number) =>
    fetchJson<Roadmap>(`${API_BASE}/roadmaps/${roadmapId}/steps/${stepId}/topics/${topicIdx}/toggle`, {
      method: 'POST'
    }),
  addRoadmapTopicReference: (
    roadmapId: number,
    stepId: string,
    topicIdx: number,
    payload: { title: string; url: string; type?: string; notes?: string }
  ) =>
    fetchJson<Roadmap>(`${API_BASE}/roadmaps/${roadmapId}/steps/${stepId}/topics/${topicIdx}/references`, {
      method: 'POST',
      body: JSON.stringify(payload)
    }),
  deleteRoadmapTopicReference: (roadmapId: number, stepId: string, topicIdx: number, refIdx: number) =>
    fetchJson<Roadmap>(`${API_BASE}/roadmaps/${roadmapId}/steps/${stepId}/topics/${topicIdx}/references/${refIdx}`, {
      method: 'DELETE'
    }),
  deleteRoadmap: (id: number) => fetchJson<any>(`${API_BASE}/roadmaps/${id}`, {
    method: 'DELETE'
  }),

  // Assistant
  askAssistant: (message: string, history?: { role: string; content: string }[]) =>
    fetchJson<{ response: string; citations: any[]; suggested_actions: string[] }>(`${API_BASE}/assistant/chat`, {
      method: 'POST',
      body: JSON.stringify({ message, history })
    }),

  // Profile & Resume
  getProfile: () => fetchJson<UserProfile>(`${API_BASE}/profile`),
  updateProfile: (data: Partial<UserProfile>) =>
    fetchJson<UserProfile>(`${API_BASE}/profile`, {
      method: 'PATCH',
      body: JSON.stringify(data)
    }),
  uploadResume: (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return fetchJson<Resume>(`${API_BASE}/profile/resume`, {
      method: 'POST',
      body: formData
    });
  },
  getResumes: () => fetchJson<Resume[]>(`${API_BASE}/profile/resumes`),
  activateResume: (id: number) => fetchJson<Resume>(`${API_BASE}/profile/resumes/${id}/activate`, {
    method: 'PATCH'
  }),

  // Settings & Export
  exportData: () => fetchJson<any>(`${API_BASE}/settings/export`),
  deleteAccount: () => fetchJson<any>(`${API_BASE}/settings/account`, {
    method: 'DELETE'
  }),

  // Auth & Google Authenticator (2FA)
  register: (email: string, password: string, full_name?: string) =>
    fetchJson<import('../types').LoginResponse>(`${API_BASE}/auth/register`, {
      method: 'POST',
      body: JSON.stringify({ email, password, full_name })
    }),

  login: (email: string, password: string, code?: string) =>
    fetchJson<import('../types').LoginResponse>(`${API_BASE}/auth/login`, {
      method: 'POST',
      body: JSON.stringify({ email, password, code })
    }),

  verify2FALogin: (temp_token: string, code: string) =>
    fetchJson<import('../types').LoginResponse>(`${API_BASE}/auth/2fa/verify-login`, {
      method: 'POST',
      body: JSON.stringify({ temp_token, code })
    }),

  get2FASetup: () =>
    fetchJson<import('../types').TOTPSetupResponse>(`${API_BASE}/auth/2fa/setup`),

  enable2FA: (code: string) =>
    fetchJson<{ success: boolean; message: string }>(`${API_BASE}/auth/2fa/enable`, {
      method: 'POST',
      body: JSON.stringify({ code })
    }),

  disable2FA: (code: string) =>
    fetchJson<{ success: boolean; message: string }>(`${API_BASE}/auth/2fa/disable`, {
      method: 'POST',
      body: JSON.stringify({ code })
    }),

  get2FAStatus: () =>
    fetchJson<import('../types').TOTPStatusResponse>(`${API_BASE}/auth/2fa/status`),

  getMe: () =>
    fetchJson<import('../types').User>(`${API_BASE}/auth/me`),

  // AI Continuous Self-Training & Feedback
  submitFeedback: (data: {
    resource_id: number;
    is_correct: boolean;
    corrected_type?: string;
    corrected_title?: string;
    reason?: string;
    notes?: string;
  }) =>
    fetchJson<ListingFeedback>(`${API_BASE}/feedback`, {
      method: 'POST',
      body: JSON.stringify(data)
    }),

  getModelLearningStats: () =>
    fetchJson<ModelLearningStats>(`${API_BASE}/feedback/stats`),

  getResourceFeedback: (resourceId: number) =>
    fetchJson<ListingFeedback | null>(`${API_BASE}/feedback/resource/${resourceId}`)
};
