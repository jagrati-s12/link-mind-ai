import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  GraduationCap,
  BookOpen,
  Calendar,
  ExternalLink,
  Trash2,
  CheckCircle2,
  Clock,
  Plus,
  PlayCircle,
  Award,
  Search,
  BookmarkCheck,
  ChevronRight
} from 'lucide-react';
import { Link } from 'react-router-dom';
import { api } from '../services/api';
import { EmptyState } from '../components/EmptyState';
import { CourseProgress, CourseProgressStatus, Resource } from '../types';

interface CourseTrackerProps {
  onOpenCapture: () => void;
}

export const CourseTracker: React.FC<CourseTrackerProps> = ({ onOpenCapture }) => {
  const queryClient = useQueryClient();
  const [selectedFilter, setSelectedFilter] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [editingNotesId, setEditingNotesId] = useState<number | null>(null);
  const [tempNotes, setTempNotes] = useState('');

  // Fetch tracked courses
  const { data: trackerItems, isLoading } = useQuery({
    queryKey: ['course-tracker-list'],
    queryFn: api.getCourseProgress
  });

  // Fetch all saved courses for the "Add to Tracker" modal
  const { data: allCourses } = useQuery({
    queryKey: ['all-courses-catalog'],
    queryFn: () => api.getResources({ type: 'courses' }),
    enabled: isAddModalOpen
  });

  const updateProgressMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<CourseProgress> }) =>
      api.updateCourseProgress(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['course-tracker-list'] });
    }
  });

  const deleteProgressMutation = useMutation({
    mutationFn: (id: number) => api.deleteCourseProgress(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['course-tracker-list'] });
    }
  });

  const addProgressMutation = useMutation({
    mutationFn: (resourceId: number) =>
      api.createCourseProgress({
        resource_id: resourceId,
        status: 'In Progress',
        progress_percentage: 10,
        current_module: 'Module 1: Introduction'
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['course-tracker-list'] });
      setIsAddModalOpen(false);
    }
  });

  const statuses: CourseProgressStatus[] = [
    'Not Started',
    'In Progress',
    'Halfway',
    'Reviewing',
    'Completed',
    'Certified'
  ];

  const filteredItems = (trackerItems || []).filter((item) => {
    const matchesFilter =
      selectedFilter === 'all'
        ? true
        : item.status.toLowerCase() === selectedFilter.toLowerCase();

    const matchesSearch =
      searchQuery.trim() === ''
        ? true
        : (item.resource?.title || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
          (item.resource?.organization || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
          (item.current_module || '').toLowerCase().includes(searchQuery.toLowerCase());

    return matchesFilter && matchesSearch;
  });

  // Already tracked resource IDs
  const trackedResourceIds = new Set((trackerItems || []).map((t) => t.resource_id));
  const untrackedSavedCourses = (allCourses || []).filter((c) => !trackedResourceIds.has(c.id));

  return (
    <div className="space-y-6 max-w-7xl mx-auto animate-fade-in pb-16">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <div className="p-2 bg-indigo-50 dark:bg-indigo-950/60 rounded-xl text-indigo-600 dark:text-indigo-400">
              <GraduationCap className="w-5 h-5" />
            </div>
            <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
              Course Progress & Learning Updates
            </h1>
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1.5 ml-9">
            Monitor active syllabus milestones, weekly progress, and completion updates for your courses
          </p>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={() => setIsAddModalOpen(true)}
            className="bg-indigo-600 hover:bg-indigo-700 text-white font-medium text-xs px-4 py-2.5 rounded-xl shadow-sm transition-all flex items-center space-x-1.5"
          >
            <BookmarkCheck className="w-4 h-4" />
            <span>Track Saved Course</span>
          </button>
          <button
            onClick={onOpenCapture}
            className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 hover:border-indigo-400 text-slate-700 dark:text-slate-200 font-medium text-xs px-3.5 py-2.5 rounded-xl transition-all flex items-center space-x-1.5"
          >
            <Plus className="w-4 h-4" />
            <span>Capture New Link</span>
          </button>
        </div>
      </div>

      {/* Controls: Search & Stage Filter Tabs */}
      <div className="flex flex-col md:flex-row items-stretch md:items-center justify-between gap-3">
        {/* Filter Tabs */}
        <div className="flex flex-wrap gap-1.5 p-1.5 bg-slate-100 dark:bg-slate-800/80 rounded-2xl w-fit">
          <button
            onClick={() => setSelectedFilter('all')}
            className={`text-xs font-semibold px-3 py-1.5 rounded-xl transition-all ${
              selectedFilter === 'all'
                ? 'bg-white dark:bg-slate-900 text-slate-900 dark:text-white shadow-sm'
                : 'text-slate-500 hover:text-slate-800 dark:hover:text-slate-200'
            }`}
          >
            All Courses ({(trackerItems || []).length})
          </button>
          {statuses.map((st) => {
            const count = (trackerItems || []).filter((i) => i.status === st).length;
            return (
              <button
                key={st}
                onClick={() => setSelectedFilter(st)}
                className={`text-xs font-semibold px-3 py-1.5 rounded-xl transition-all ${
                  selectedFilter === st
                    ? 'bg-white dark:bg-slate-900 text-slate-900 dark:text-white shadow-sm'
                    : 'text-slate-500 hover:text-slate-800 dark:hover:text-slate-200'
                }`}
              >
                {st} {count > 0 && `(${count})`}
              </button>
            );
          })}
        </div>

        {/* Search */}
        <div className="relative w-full md:w-64">
          <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search tracked courses..."
            className="w-full pl-8 pr-3 py-2 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl text-xs text-slate-900 dark:text-white focus:outline-none focus:border-indigo-500"
          />
        </div>
      </div>

      {/* Tracked Courses List */}
      {filteredItems.length === 0 ? (
        <EmptyState
          icon={BookOpen}
          title="No courses currently being tracked here"
          description="Track your enrolled courses, tutorials, or Coursera certificates to log your module milestones and completion progress."
          actionText="Track A Saved Course"
          onAction={() => setIsAddModalOpen(true)}
        />
      ) : (
        <div className="space-y-4">
          {filteredItems.map((item) => {
            const progress = item.progress_percentage || 0;
            const isCompleted = item.status === 'Completed' || item.status === 'Certified';

            return (
              <div
                key={item.id}
                className="bg-white dark:bg-slate-900 rounded-3xl border border-slate-200/90 dark:border-slate-800 p-5 md:p-6 shadow-sm hover:border-indigo-200 dark:hover:border-indigo-900/60 transition-all space-y-4"
              >
                {/* Header row: Course Title, Org, Direct Link, Status */}
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                  <div className="space-y-1">
                    <div className="flex items-center space-x-2">
                      <Link
                        to={`/resources/${item.resource_id}`}
                        className="font-bold text-slate-900 dark:text-white text-base hover:text-indigo-600 transition-colors"
                      >
                        {item.resource?.title || 'Tracked Course'}
                      </Link>
                      {isCompleted && (
                        <span className="inline-flex items-center space-x-1 text-[11px] font-semibold bg-emerald-50 dark:bg-emerald-950/60 text-emerald-600 dark:text-emerald-400 px-2 py-0.5 rounded-full border border-emerald-200 dark:border-emerald-800">
                          <CheckCircle2 className="w-3 h-3" />
                          <span>Done</span>
                        </span>
                      )}
                    </div>

                    <div className="flex flex-wrap items-center gap-3 text-xs text-slate-500">
                      {item.resource?.organization && (
                        <span className="font-medium text-slate-700 dark:text-slate-300">
                          {item.resource.organization}
                        </span>
                      )}
                      {item.target_completion_date && (
                        <div className="flex items-center space-x-1 text-slate-400">
                          <Calendar className="w-3.5 h-3.5" />
                          <span>Target: {item.target_completion_date}</span>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Actions & Status Dropdown */}
                  <div className="flex items-center space-x-3">
                    {item.resource?.direct_url && (
                      <a
                        href={item.resource.direct_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center space-x-1.5 text-xs font-semibold px-3 py-1.5 rounded-xl bg-indigo-50 dark:bg-indigo-950/50 text-indigo-600 dark:text-indigo-400 hover:bg-indigo-100 transition-colors"
                      >
                        <span>Open Course</span>
                        <ExternalLink className="w-3.5 h-3.5" />
                      </a>
                    )}

                    {/* Status selector */}
                    <select
                      value={item.status}
                      onChange={(e) =>
                        updateProgressMutation.mutate({
                          id: item.id,
                          data: { status: e.target.value as CourseProgressStatus }
                        })
                      }
                      className="text-xs font-semibold bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl px-3 py-1.5 text-slate-900 dark:text-white focus:outline-none focus:border-indigo-500"
                    >
                      {statuses.map((st) => (
                        <option key={st} value={st}>
                          {st}
                        </option>
                      ))}
                    </select>

                    {/* Remove button */}
                    <button
                      onClick={() => {
                        if (window.confirm("Remove this course from your active progress tracker?")) {
                          deleteProgressMutation.mutate(item.id);
                        }
                      }}
                      className="p-1.5 text-slate-400 hover:text-rose-600 transition-colors rounded-lg"
                      title="Remove from Course Tracker"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>

                {/* Progress bar and Module Update */}
                <div className="bg-slate-50 dark:bg-slate-800/50 p-4 rounded-2xl border border-slate-100 dark:border-slate-800/80 space-y-3">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs">
                    <div className="flex items-center space-x-2">
                      <PlayCircle className="w-4 h-4 text-indigo-500 shrink-0" />
                      <span className="text-slate-500 font-medium">Current Milestone:</span>
                      <input
                        type="text"
                        defaultValue={item.current_module || 'Getting Started'}
                        onBlur={(e) => {
                          if (e.target.value !== item.current_module) {
                            updateProgressMutation.mutate({
                              id: item.id,
                              data: { current_module: e.target.value }
                            });
                          }
                        }}
                        placeholder="e.g. Module 3: Prepare Data for Exploration"
                        className="bg-transparent border-b border-dashed border-slate-300 dark:border-slate-600 px-1 py-0.5 text-slate-800 dark:text-slate-100 font-semibold focus:outline-none focus:border-indigo-500 min-w-[240px]"
                      />
                    </div>

                    <div className="flex items-center space-x-3">
                      <span className="font-mono font-bold text-indigo-600 dark:text-indigo-400">
                        {progress}%
                      </span>
                      {/* Quick percentage pills */}
                      <div className="flex items-center space-x-1">
                        {[0, 25, 50, 75, 100].map((pct) => (
                          <button
                            key={pct}
                            onClick={() =>
                              updateProgressMutation.mutate({
                                id: item.id,
                                data: {
                                  progress_percentage: pct,
                                  status: pct === 100 ? 'Completed' : item.status
                                }
                              })
                            }
                            className={`text-[10px] font-bold px-2 py-0.5 rounded-lg transition-colors ${
                              progress === pct
                                ? 'bg-indigo-600 text-white'
                                : 'bg-slate-200/80 dark:bg-slate-700 text-slate-600 dark:text-slate-300 hover:bg-slate-300'
                            }`}
                          >
                            {pct}%
                          </button>
                        ))}
                      </div>
                    </div>
                  </div>

                  {/* Visual Progress Bar */}
                  <div className="w-full h-2.5 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
                    <div
                      className={`h-full transition-all duration-300 rounded-full ${
                        isCompleted
                          ? 'bg-emerald-500'
                          : 'bg-gradient-to-r from-indigo-500 to-brand-500'
                      }`}
                      style={{ width: `${progress}%` }}
                    />
                  </div>
                </div>

                {/* Notes & Learning Updates */}
                <div className="pt-1 flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs">
                  <div className="flex-1">
                    {editingNotesId === item.id ? (
                      <div className="flex items-center space-x-2">
                        <input
                          type="text"
                          value={tempNotes}
                          onChange={(e) => setTempNotes(e.target.value)}
                          placeholder="Log notes, key learnings, or quiz score..."
                          className="flex-1 px-3 py-1.5 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-xs text-slate-900 dark:text-white focus:outline-none focus:border-indigo-500"
                        />
                        <button
                          onClick={() => {
                            updateProgressMutation.mutate({
                              id: item.id,
                              data: { notes: tempNotes }
                            });
                            setEditingNotesId(null);
                          }}
                          className="bg-indigo-600 text-white px-3 py-1.5 rounded-xl font-medium text-xs hover:bg-indigo-700"
                        >
                          Save
                        </button>
                        <button
                          onClick={() => setEditingNotesId(null)}
                          className="text-slate-400 hover:text-slate-600 px-2 text-xs"
                        >
                          Cancel
                        </button>
                      </div>
                    ) : (
                      <div
                        onClick={() => {
                          setEditingNotesId(item.id);
                          setTempNotes(item.notes || '');
                        }}
                        className="cursor-pointer group flex items-center space-x-2 text-slate-500 hover:text-slate-800 dark:hover:text-slate-200"
                      >
                        <span className="font-medium text-slate-400">Weekly Update:</span>
                        <span className="italic">
                          {item.notes ? `"${item.notes}"` : 'Click to add notes or updates...'}
                        </span>
                      </div>
                    )}
                  </div>

                  {/* Skills tags */}
                  {item.resource?.taught_skills && item.resource.taught_skills.length > 0 && (
                    <div className="flex flex-wrap items-center gap-1.5">
                      {item.resource.taught_skills.slice(0, 3).map((sk, idx) => (
                        <span
                          key={idx}
                          className="text-[10px] font-medium bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 px-2 py-0.5 rounded-md"
                        >
                          {sk}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Add Course from Library Modal */}
      {isAddModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-sm animate-fade-in">
          <div className="bg-white dark:bg-slate-900 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-xl max-w-lg w-full p-6 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800">
              <h3 className="font-bold text-base text-slate-900 dark:text-white flex items-center space-x-2">
                <BookmarkCheck className="w-5 h-5 text-indigo-600" />
                <span>Track Saved Course</span>
              </h3>
              <button
                onClick={() => setIsAddModalOpen(false)}
                className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 text-sm font-semibold"
              >
                ✕
              </button>
            </div>

            <p className="text-xs text-slate-500">
              Select any course from your library to start tracking modules and progress:
            </p>

            <div className="max-h-72 overflow-y-auto space-y-2 custom-scrollbar">
              {untrackedSavedCourses.length === 0 ? (
                <div className="text-center py-6 text-xs text-slate-400">
                  All your saved courses are already tracked! You can capture new course links anytime.
                </div>
              ) : (
                untrackedSavedCourses.map((c) => (
                  <div
                    key={c.id}
                    className="p-3 rounded-2xl border border-slate-200 dark:border-slate-800 hover:border-indigo-400 dark:hover:border-indigo-600 flex items-center justify-between gap-3 transition-colors"
                  >
                    <div className="space-y-0.5 max-w-xs">
                      <h4 className="text-xs font-bold text-slate-900 dark:text-white truncate">
                        {c.title}
                      </h4>
                      <p className="text-[11px] text-slate-500 truncate">{c.organization || 'Course'}</p>
                    </div>

                    <button
                      onClick={() => addProgressMutation.mutate(c.id)}
                      className="bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-xs px-3 py-1.5 rounded-xl shadow-sm transition-colors whitespace-nowrap"
                    >
                      + Track
                    </button>
                  </div>
                ))
              )}
            </div>

            <div className="pt-2 border-t border-slate-100 dark:border-slate-800 flex justify-end">
              <button
                onClick={() => setIsAddModalOpen(false)}
                className="text-xs font-medium px-4 py-2 rounded-xl text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
              >
                Done
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
