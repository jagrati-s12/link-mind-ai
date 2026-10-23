import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { UserCheck, FileUp, CheckCircle2, Sparkles, Building, GraduationCap, Briefcase, Save, Loader2 } from 'lucide-react';
import { api } from '../services/api';

export const Profile: React.FC = () => {
  const queryClient = useQueryClient();
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadMsg, setUploadMsg] = useState<string | null>(null);

  // Profile fields state
  const [careerGoals, setCareerGoals] = useState('');
  const [targetRoles, setTargetRoles] = useState('');
  const [preferredLocs, setPreferredLocs] = useState('');
  const [saveMsg, setSaveMsg] = useState<string | null>(null);

  const { data: profile, isLoading: isProfLoading } = useQuery({
    queryKey: ['user-profile'],
    queryFn: async () => {
      const p = await api.getProfile();
      setCareerGoals(p.career_goals || '');
      setTargetRoles((p.target_roles || []).join(', '));
      setPreferredLocs((p.preferred_locations || []).join(', '));
      return p;
    }
  });

  const { data: resumes } = useQuery({
    queryKey: ['user-resumes'],
    queryFn: api.getResumes
  });

  const activeResume = (resumes || []).find(r => r.is_active);

  const uploadResumeMutation = useMutation({
    mutationFn: (file: File) => api.uploadResume(file),
    onSuccess: (data) => {
      setUploadMsg(`Resume parsed successfully! Extracted ${data.parsed_data.technical_skills?.length || 0} skills.`);
      setSelectedFile(null);
      queryClient.invalidateQueries({ queryKey: ['user-resumes'] });
      queryClient.invalidateQueries({ queryKey: ['skills-user'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard-stats'] });
      queryClient.invalidateQueries({ queryKey: ['resources-list'] });
    },
    onError: (err: any) => {
      setUploadMsg(`Upload failed: ${err.message}`);
    }
  });

  const updateProfileMutation = useMutation({
    mutationFn: (data: any) => api.updateProfile(data),
    onSuccess: () => {
      setSaveMsg('Profile preferences updated! Fit scores recalculated.');
      setTimeout(() => setSaveMsg(null), 3000);
      queryClient.invalidateQueries({ queryKey: ['user-profile'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard-stats'] });
      queryClient.invalidateQueries({ queryKey: ['resources-list'] });
    }
  });

  const activateResumeMutation = useMutation({
    mutationFn: (id: number) => api.activateResume(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['user-resumes'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard-stats'] });
      queryClient.invalidateQueries({ queryKey: ['resources-list'] });
    }
  });

  const handleFileUpload = (e: React.FormEvent) => {
    e.preventDefault();
    if (selectedFile) {
      setUploadMsg(null);
      uploadResumeMutation.mutate(selectedFile);
    }
  };

  const handleProfileSave = (e: React.FormEvent) => {
    e.preventDefault();
    updateProfileMutation.mutate({
      career_goals: careerGoals,
      target_roles: targetRoles.split(',').map(r => r.trim()).filter(Boolean),
      preferred_locations: preferredLocs.split(',').map(l => l.trim()).filter(Boolean)
    });
  };

  return (
    <div className="space-y-8 max-w-5xl mx-auto animate-fade-in pb-12">
      <div>
        <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Profile & Resume Intelligence</h1>
        <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
          Manage your resume versions and career goals. Recommendations adapt dynamically to your active profile.
        </p>
      </div>

      {/* Resume Upload Card */}
      <div className="bg-white dark:bg-slate-900 p-6 md:p-8 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-sm space-y-4">
        <div className="flex items-center space-x-2">
          <FileUp className="w-5 h-5 text-brand-600" />
          <h2 className="text-base font-bold text-slate-900 dark:text-white">Upload Resume (PDF / DOCX)</h2>
        </div>

        <form onSubmit={handleFileUpload} className="space-y-4">
          <div className="border-2 border-dashed border-slate-300 dark:border-slate-700 rounded-2xl p-6 text-center hover:bg-slate-50 dark:hover:bg-slate-800/40 transition-colors">
            <input
              type="file"
              id="resumeInput"
              accept=".pdf,.docx,.txt"
              className="hidden"
              onChange={(e) => {
                if (e.target.files && e.target.files[0]) {
                  setSelectedFile(e.target.files[0]);
                }
              }}
            />
            <label
              htmlFor="resumeInput"
              className="cursor-pointer text-xs sm:text-sm font-semibold text-brand-600 dark:text-brand-400 hover:underline block"
            >
              {selectedFile ? selectedFile.name : 'Click to choose resume file (.pdf, .docx)'}
            </label>
            <p className="text-[11px] text-slate-400 mt-1">
              Extracts programming languages, frameworks, graduation year, education, and portfolio projects
            </p>
          </div>

          <div className="flex justify-end">
            <button
              type="submit"
              disabled={uploadResumeMutation.isPending || !selectedFile}
              className="flex items-center space-x-1.5 bg-brand-600 hover:bg-brand-700 disabled:opacity-50 text-white font-medium text-xs px-5 py-2.5 rounded-xl shadow-sm transition-colors"
            >
              {uploadResumeMutation.isPending && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
              <span>{uploadResumeMutation.isPending ? 'Parsing Resume...' : 'Parse & Activate Resume'}</span>
            </button>
          </div>
        </form>

        {uploadMsg && (
          <p className="text-xs text-brand-600 font-medium">{uploadMsg}</p>
        )}
      </div>

      {/* Active Resume Parsed Data Inspection */}
      {activeResume && (
        <div className="bg-white dark:bg-slate-900 p-6 md:p-8 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-sm space-y-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Sparkles className="w-5 h-5 text-indigo-600" />
              <h2 className="text-base font-bold text-slate-900 dark:text-white">Active Resume: {activeResume.version_name}</h2>
            </div>
            <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-emerald-50 dark:bg-emerald-950/40 text-emerald-600 border border-emerald-200">
              Active For Scoring
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {/* Technical Skills */}
            <div className="p-4 rounded-2xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700">
              <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 block mb-2">
                Languages & Core Tech
              </span>
              <div className="flex flex-wrap gap-1.5">
                {(activeResume.parsed_data.technical_skills || []).map((s, i) => (
                  <span key={i} className="text-xs px-2.5 py-1 rounded-lg bg-white dark:bg-slate-900 text-slate-800 dark:text-slate-200 font-semibold border border-slate-200 dark:border-slate-700">
                    {s}
                  </span>
                ))}
              </div>
            </div>

            {/* Frameworks & Tools */}
            <div className="p-4 rounded-2xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700">
              <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 block mb-2">
                Frameworks & Infrastructure
              </span>
              <div className="flex flex-wrap gap-1.5">
                {(activeResume.parsed_data.frameworks || []).concat(activeResume.parsed_data.tools || []).map((s, i) => (
                  <span key={i} className="text-xs px-2.5 py-1 rounded-lg bg-white dark:bg-slate-900 text-slate-800 dark:text-slate-200 font-semibold border border-slate-200 dark:border-slate-700">
                    {s}
                  </span>
                ))}
              </div>
            </div>
          </div>

          {/* Education & Graduation Year */}
          {activeResume.parsed_data.graduation_year && (
            <div className="flex items-center space-x-2 text-xs text-slate-600 dark:text-slate-300">
              <GraduationCap className="w-4 h-4 text-brand-600" />
              <span>Graduation Year on Record: <strong>{activeResume.parsed_data.graduation_year}</strong></span>
            </div>
          )}
        </div>
      )}

      {/* Target Roles & Career Goals Editor */}
      <div className="bg-white dark:bg-slate-900 p-6 md:p-8 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-sm space-y-4">
        <h2 className="text-base font-bold text-slate-900 dark:text-white">Career Goals & Preferences</h2>
        
        <form onSubmit={handleProfileSave} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
              Target Roles (comma-separated)
            </label>
            <input
              type="text"
              value={targetRoles}
              onChange={(e) => setTargetRoles(e.target.value)}
              placeholder="AI Engineer, Machine Learning Engineer, Backend Developer"
              className="w-full px-3.5 py-2.5 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-xs sm:text-sm text-slate-900 dark:text-white focus:outline-none focus:border-brand-500"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
              Preferred Work Locations (comma-separated)
            </label>
            <input
              type="text"
              value={preferredLocs}
              onChange={(e) => setPreferredLocs(e.target.value)}
              placeholder="Remote, Bengaluru, San Francisco"
              className="w-full px-3.5 py-2.5 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-xs sm:text-sm text-slate-900 dark:text-white focus:outline-none focus:border-brand-500"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
              Career Objective / Long-term Goals
            </label>
            <textarea
              rows={3}
              value={careerGoals}
              onChange={(e) => setCareerGoals(e.target.value)}
              placeholder="e.g. Master PyTorch and model evaluation pipelines, land an internship at top AI lab..."
              className="w-full p-3 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-xs sm:text-sm text-slate-900 dark:text-white focus:outline-none focus:border-brand-500"
            />
          </div>

          <div className="flex items-center justify-between pt-2">
            {saveMsg ? (
              <span className="text-xs text-emerald-600 font-semibold">{saveMsg}</span>
            ) : <span />}

            <button
              type="submit"
              disabled={updateProfileMutation.isPending}
              className="flex items-center space-x-1.5 bg-brand-600 hover:bg-brand-700 text-white font-medium text-xs px-5 py-2.5 rounded-xl shadow-sm transition-colors"
            >
              <Save className="w-3.5 h-3.5" />
              <span>Save & Recalculate Matches</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
