import React, { useState } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  ArrowLeft,
  Building,
  MapPin,
  Calendar,
  ExternalLink,
  Sparkles,
  CheckCircle2,
  AlertCircle,
  HelpCircle,
  Folder,
  Trash2,
  Save,
  CheckSquare,
  Clock,
  DollarSign,
  GraduationCap
} from 'lucide-react';
import { api } from '../services/api';
import { ApplicationStatus } from '../types';

export const ResourceDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const resourceId = Number(id);

  const [notes, setNotes] = useState('');
  const [appStatus, setAppStatus] = useState<ApplicationStatus>('Saved');
  const [isSavedApp, setIsSavedApp] = useState(false);

  const { data: resource, isLoading } = useQuery({
    queryKey: ['resource-detail', resourceId],
    queryFn: async () => {
      const res = await api.getResource(resourceId);
      setNotes(res.notes || '');
      if (res.application) {
        setAppStatus(res.application.status);
        setIsSavedApp(true);
      }
      return res;
    }
  });

  const { data: allCollections } = useQuery({
    queryKey: ['resource-detail-collections'],
    queryFn: api.getCollections
  });

  const updateResourceMutation = useMutation({
    mutationFn: (data: any) => api.updateResource(resourceId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['resource-detail', resourceId] });
      queryClient.invalidateQueries({ queryKey: ['resources-list'] });
    }
  });

  const deleteResourceMutation = useMutation({
    mutationFn: () => api.deleteResource(resourceId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['resources-list'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard-stats'] });
      navigate('/resources');
    }
  });

  const updateAppMutation = useMutation({
    mutationFn: (status: ApplicationStatus) => {
      return api.createApplication({
        resource_id: resourceId,
        status: status,
        deadline: resource?.deadline || undefined,
        notes: notes
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['resource-detail', resourceId] });
      queryClient.invalidateQueries({ queryKey: ['applications-list'] });
      setIsSavedApp(true);
    }
  });

  if (isLoading || !resource) {
    return <div className="p-8 text-center text-xs text-slate-500">Loading opportunity details...</div>;
  }

  const rec = resource.recommendation;
  const isCourse = resource.type === 'course' || resource.type === 'certification';

  const handleStatusChange = (newStatus: ApplicationStatus) => {
    setAppStatus(newStatus);
    updateAppMutation.mutate(newStatus);
  };

  const handleNotesSave = () => {
    updateResourceMutation.mutate({ notes });
  };

  const handleToggleCollection = (colId: number) => {
    const currentIds = resource.collections.map(c => c.id);
    const newIds = currentIds.includes(colId)
      ? currentIds.filter(id => id !== colId)
      : [...currentIds, colId];
    updateResourceMutation.mutate({ collection_ids: newIds });
  };

  const statuses: ApplicationStatus[] = [
    'Saved', 'Shortlisted', 'Preparing', 'Applied',
    'Assessment', 'Interview', 'Offer', 'Rejected', 'Withdrawn', 'Closed'
  ];

  return (
    <div className="space-y-6 max-w-5xl mx-auto animate-fade-in pb-12">
      {/* Navigation breadcrumb */}
      <div className="flex items-center space-x-2 text-xs text-slate-500">
        <Link to="/resources" className="hover:text-brand-600 flex items-center space-x-1">
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>All Resources</span>
        </Link>
        <span>/</span>
        <span className="text-slate-800 dark:text-slate-200 font-medium truncate max-w-xs">{resource.title}</span>
      </div>

      {/* Main Header Card */}
      <div className="bg-white dark:bg-slate-900 p-6 md:p-8 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-sm space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center space-x-2">
            <span className="text-xs font-bold uppercase tracking-wider px-3 py-1 rounded-full bg-brand-50 dark:bg-brand-950/60 text-brand-600 dark:text-brand-400 border border-brand-200 dark:border-brand-900">
              {resource.type}
            </span>
            <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300">
              Status: {resource.verification_status}
            </span>
          </div>

          <div className="flex items-center space-x-2">
            {resource.direct_url && (
              <a
                href={resource.direct_url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center space-x-1.5 bg-brand-600 hover:bg-brand-700 text-white font-medium text-xs px-4 py-2 rounded-xl shadow-sm transition-colors"
              >
                <span>{isCourse ? 'View Course Syllabus' : 'Apply Directly'}</span>
                <ExternalLink className="w-3.5 h-3.5" />
              </a>
            )}

            <button
              onClick={() => {
                if (window.confirm("Delete this opportunity from your library?")) {
                  deleteResourceMutation.mutate();
                }
              }}
              className="p-2 text-slate-400 hover:text-rose-600 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-xl transition-colors"
              title="Delete Opportunity"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          </div>
        </div>

        <div>
          <h1 className="text-2xl md:text-3xl font-extrabold text-slate-900 dark:text-white tracking-tight">
            {resource.title}
          </h1>
          {resource.organization && (
            <div className="flex items-center space-x-2 text-sm text-slate-600 dark:text-slate-400 font-medium mt-1.5">
              <Building className="w-4 h-4" />
              <span>{resource.organization}</span>
            </div>
          )}
        </div>

        {/* Facts Row: Location, Compensation, Deadline */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-3 border-t border-slate-100 dark:border-slate-800 text-xs text-slate-600 dark:text-slate-300">
          <div className="flex items-center space-x-2 bg-slate-50 dark:bg-slate-800/60 p-3 rounded-xl">
            <MapPin className="w-4 h-4 text-slate-400" />
            <div>
              <span className="block text-[10px] text-slate-400 uppercase font-semibold">Location</span>
              <span className="font-medium">{resource.location || 'Not specified'}</span>
            </div>
          </div>

          <div className="flex items-center space-x-2 bg-slate-50 dark:bg-slate-800/60 p-3 rounded-xl">
            <DollarSign className="w-4 h-4 text-slate-400" />
            <div>
              <span className="block text-[10px] text-slate-400 uppercase font-semibold">Compensation / Stipend</span>
              <span className="font-medium">{resource.compensation || 'Needs verification'}</span>
            </div>
          </div>

          <div className="flex items-center space-x-2 bg-slate-50 dark:bg-slate-800/60 p-3 rounded-xl">
            <Calendar className="w-4 h-4 text-slate-400" />
            <div>
              <span className="block text-[10px] text-slate-400 uppercase font-semibold">Application Deadline</span>
              <span className="font-medium text-rose-600 dark:text-rose-400">{resource.deadline || 'Not found'}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Two Column Layout: AI Recommendation & Details */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column (2 Cols): Recommendation Breakdown & Description */}
        <div className="lg:col-span-2 space-y-6">
          {/* AI Fit Recommendation Card */}
          <div className="bg-white dark:bg-slate-900 p-6 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-sm space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Sparkles className="w-5 h-5 text-brand-600 dark:text-brand-400" />
                <h3 className="font-bold text-slate-900 dark:text-white text-base">Resume Fit Intelligence</h3>
              </div>

              {rec && (
                <div className="flex items-center space-x-1.5 px-3 py-1 rounded-full bg-brand-50 dark:bg-brand-950/60 text-brand-600 dark:text-brand-400 font-extrabold text-sm border border-brand-200 dark:border-brand-900">
                  <span>{Math.round(rec.fit_score)} / 100</span>
                </div>
              )}
            </div>

            {/* Transparent Formula Breakdown: S = 0.35K + 0.25P + 0.20G + 0.10L + 0.10C */}
            <div className="p-3 bg-slate-50 dark:bg-slate-800/50 rounded-xl text-[11px] text-slate-500 font-mono">
              Formula: S = 0.35K (Skills) + 0.25P (Projects) + 0.20G (Goals) + 0.10L (Learning) + 0.10C (Practical)
            </div>

            {rec?.explanation && (
              <p className="text-xs text-slate-700 dark:text-slate-300 leading-relaxed font-medium">
                {rec.explanation}
              </p>
            )}

            {/* Matching vs Missing Skills */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
              <div className="p-4 rounded-2xl bg-emerald-50/60 dark:bg-emerald-950/30 border border-emerald-200 dark:border-emerald-900/40">
                <span className="text-[11px] font-bold uppercase tracking-wider text-emerald-700 dark:text-emerald-400 block mb-2">
                  Matching Verified Skills
                </span>
                {rec?.matching_skills && rec.matching_skills.length > 0 ? (
                  <div className="flex flex-wrap gap-1.5">
                    {rec.matching_skills.map((s, idx) => (
                      <span key={idx} className="text-xs px-2 py-0.5 rounded-md bg-emerald-100 dark:bg-emerald-900/60 text-emerald-800 dark:text-emerald-300 font-medium">
                        ✓ {s}
                      </span>
                    ))}
                  </div>
                ) : (
                  <span className="text-xs text-slate-400">None detected on current resume version</span>
                )}
              </div>

              <div className="p-4 rounded-2xl bg-amber-50/60 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-900/40">
                <span className="text-[11px] font-bold uppercase tracking-wider text-amber-700 dark:text-amber-400 block mb-2">
                  Skills To Strengthen
                </span>
                {rec?.missing_skills && rec.missing_skills.length > 0 ? (
                  <div className="flex flex-wrap gap-1.5">
                    {rec.missing_skills.map((s, idx) => (
                      <span key={idx} className="text-xs px-2 py-0.5 rounded-md bg-amber-100 dark:bg-amber-900/60 text-amber-800 dark:text-amber-300 font-medium">
                        + {s}
                      </span>
                    ))}
                  </div>
                ) : (
                  <span className="text-xs text-emerald-600 dark:text-emerald-400 font-medium">All core requirements met!</span>
                )}
              </div>
            </div>
          </div>

          {/* Detailed Description & Provenance */}
          <div className="bg-white dark:bg-slate-900 p-6 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-sm space-y-4">
            <h3 className="font-bold text-slate-900 dark:text-white text-base">Opportunity Description</h3>
            <p className="text-xs sm:text-sm text-slate-600 dark:text-slate-300 whitespace-pre-line leading-relaxed">
              {resource.description || 'No detailed description extracted.'}
            </p>

            {/* Source Provenance */}
            {resource.source_url && (
              <div className="pt-4 border-t border-slate-100 dark:border-slate-800 text-xs text-slate-500">
                <span className="font-semibold block mb-1">Source Provenance:</span>
                <a
                  href={resource.source_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-brand-600 dark:text-brand-400 hover:underline flex items-center space-x-1"
                >
                  <span className="truncate max-w-lg">{resource.source_url}</span>
                  <ExternalLink className="w-3 h-3 shrink-0" />
                </a>
              </div>
            )}
          </div>
        </div>

        {/* Right Column (1 Col): Application Tracker / Learning Tracker, Folders, Notes */}
        <div className="space-y-6">
          {isCourse ? (
            /* Course Progress Tracker Card */
            <div className="bg-white dark:bg-slate-900 p-6 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-sm space-y-3">
              <div className="flex items-center space-x-2">
                <GraduationCap className="w-4 h-4 text-indigo-600" />
                <h3 className="font-bold text-slate-900 dark:text-white text-sm">Course Learning Status</h3>
              </div>
              <p className="text-xs text-slate-600 dark:text-slate-300">
                Track your active modules, completion %, and study updates in your Course Tracker.
              </p>
              <Link
                to="/course-tracker"
                className="inline-flex items-center space-x-1.5 w-full justify-center bg-indigo-50 hover:bg-indigo-100 dark:bg-indigo-950/60 dark:hover:bg-indigo-900/60 text-indigo-600 dark:text-indigo-400 font-semibold text-xs px-3.5 py-2 rounded-xl transition-colors"
              >
                <span>Open Course Tracker</span>
                <ExternalLink className="w-3.5 h-3.5" />
              </Link>
            </div>
          ) : (
            /* Application Stage Tracker for Internships & Jobs */
            <div className="bg-white dark:bg-slate-900 p-6 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-sm space-y-3">
              <div className="flex items-center space-x-2">
                <CheckSquare className="w-4 h-4 text-brand-600" />
                <h3 className="font-bold text-slate-900 dark:text-white text-sm">Application Status</h3>
              </div>

              <select
                value={appStatus}
                onChange={(e) => handleStatusChange(e.target.value as ApplicationStatus)}
                className="w-full text-xs font-semibold bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl px-3 py-2.5 text-slate-900 dark:text-white focus:outline-none focus:border-brand-500"
              >
                {statuses.map((st) => (
                  <option key={st} value={st}>{st}</option>
                ))}
              </select>
              <p className="text-[11px] text-slate-400">
                Track interview rounds and submission status in the Internship Tracker.
              </p>
            </div>
          )}

          {/* Connected Collections / Subject Folders */}
          <div className="bg-white dark:bg-slate-900 p-6 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-sm space-y-3">
            <div className="flex items-center space-x-2">
              <Folder className="w-4 h-4 text-brand-600" />
              <h3 className="font-bold text-slate-900 dark:text-white text-sm">Organized Collections</h3>
            </div>

            <div className="space-y-2">
              {(allCollections || []).map((col) => {
                const isSelected = resource.collections.some(c => c.id === col.id);
                return (
                  <label
                    key={col.id}
                    className="flex items-center space-x-2.5 p-2 rounded-xl hover:bg-slate-50 dark:hover:bg-slate-800/60 cursor-pointer text-xs"
                  >
                    <input
                      type="checkbox"
                      checked={isSelected}
                      onChange={() => handleToggleCollection(col.id)}
                      className="rounded text-brand-600 focus:ring-brand-500"
                    />
                    <span className="font-medium text-slate-700 dark:text-slate-300">{col.name}</span>
                  </label>
                );
              })}
            </div>
          </div>

          {/* Personal Notes */}
          <div className="bg-white dark:bg-slate-900 p-6 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-sm space-y-3">
            <h3 className="font-bold text-slate-900 dark:text-white text-sm">Personal Notes</h3>
            <textarea
              rows={4}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Add interview notes, referral contacts, or deadlines..."
              className="w-full p-3 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-xs text-slate-900 dark:text-white focus:outline-none focus:border-brand-500"
            />
            <button
              onClick={handleNotesSave}
              disabled={updateResourceMutation.isPending}
              className="w-full flex items-center justify-center space-x-1.5 bg-slate-800 dark:bg-slate-700 hover:bg-slate-900 text-white font-medium text-xs py-2 rounded-xl transition-colors"
            >
              <Save className="w-3.5 h-3.5" />
              <span>Save Notes</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
