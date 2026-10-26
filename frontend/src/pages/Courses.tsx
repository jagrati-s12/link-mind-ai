import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { BookOpen, Search, Folder, FolderKanban, ArrowRight } from 'lucide-react';
import { Link } from 'react-router-dom';
import { api } from '../services/api';
import { ResourceCard } from '../components/ResourceCard';
import { EmptyState } from '../components/EmptyState';

interface CoursesProps {
  onOpenCapture: () => void;
}

export const Courses: React.FC<CoursesProps> = ({ onOpenCapture }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedFolderId, setSelectedFolderId] = useState<number | null>(null);

  // Fetch all collections / subject folders
  const { data: collections } = useQuery({
    queryKey: ['collections-list'],
    queryFn: api.getCollections
  });

  // Filter out pure job/internship/hackathon system folders to display course-relevant folders
  const courseFolders = (collections || []).filter(c => {
    const n = c.name.toLowerCase();
    return !['internships', 'jobs', 'hackathons'].includes(n) && (c.resource_count > 0 || !c.is_system);
  });

  const { data: courses, isLoading } = useQuery({
    queryKey: ['courses-list', searchTerm, selectedFolderId],
    queryFn: () => api.getResources({
      type: 'courses',
      collection_id: selectedFolderId || undefined,
      search: searchTerm.trim() || undefined
    })
  });

  const activeFolderName = selectedFolderId 
    ? collections?.find(c => c.id === selectedFolderId)?.name 
    : 'All Courses';

  return (
    <div className="space-y-6 max-w-7xl mx-auto animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Courses & Learning Catalogs</h1>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            Curated courses automatically organized into subject folders (Systems, Algorithms, Machine Learning, etc.)
          </p>
        </div>

        <div className="flex items-center space-x-2">
          <Link
            to="/collections"
            className="flex items-center space-x-1 text-xs text-brand-600 dark:text-brand-400 hover:text-brand-700 bg-brand-50 dark:bg-brand-950/40 border border-brand-200 dark:border-brand-900/50 px-3 py-2 rounded-xl font-medium transition-colors"
          >
            <FolderKanban className="w-3.5 h-3.5 mr-1" />
            <span>Browse All Folders</span>
            <ArrowRight className="w-3.5 h-3.5 ml-1" />
          </Link>

          <button
            onClick={onOpenCapture}
            className="self-start sm:self-auto bg-brand-600 hover:bg-brand-700 text-white font-medium text-xs px-4 py-2 rounded-xl shadow-sm transition-colors"
          >
            + Add Course Link
          </button>
        </div>
      </div>

      {/* Category Folders Bar */}
      {courseFolders.length > 0 && (
        <div className="bg-white dark:bg-slate-900 p-4 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm space-y-2.5">
          <div className="flex items-center justify-between text-xs font-semibold text-slate-700 dark:text-slate-300">
            <div className="flex items-center space-x-1.5">
              <Folder className="w-4 h-4 text-brand-600" />
              <span>Course Subject Folders</span>
            </div>
            {selectedFolderId && (
              <button
                onClick={() => setSelectedFolderId(null)}
                className="text-xs text-brand-600 dark:text-brand-400 hover:underline"
              >
                Clear folder filter (Show all)
              </button>
            )}
          </div>

          <div className="flex flex-wrap gap-2 pt-1">
            <button
              onClick={() => setSelectedFolderId(null)}
              className={`px-3 py-1.5 rounded-xl text-xs font-medium transition-all flex items-center space-x-1.5 ${
                selectedFolderId === null
                  ? 'bg-brand-600 text-white shadow-sm'
                  : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700'
              }`}
            >
              <span>All Courses</span>
            </button>

            {courseFolders.map(folder => {
              const isSelected = selectedFolderId === folder.id;
              return (
                <button
                  key={folder.id}
                  onClick={() => setSelectedFolderId(isSelected ? null : folder.id)}
                  className={`px-3 py-1.5 rounded-xl text-xs font-medium transition-all flex items-center space-x-1.5 border ${
                    isSelected
                      ? 'bg-brand-600 text-white border-brand-600 shadow-sm'
                      : 'bg-slate-50 dark:bg-slate-800/80 text-slate-700 dark:text-slate-300 border-slate-200 dark:border-slate-700 hover:border-brand-400'
                  }`}
                >
                  <Folder className="w-3.5 h-3.5 opacity-80" />
                  <span>{folder.name}</span>
                  <span className={`text-[10px] px-1.5 py-0.2 rounded-full font-bold ${
                    isSelected ? 'bg-white/20 text-white' : 'bg-slate-200 dark:bg-slate-700 text-slate-600 dark:text-slate-400'
                  }`}>
                    {folder.resource_count}
                  </span>
                </button>
              );
            })}
          </div>
        </div>
      )}

      {/* Search Bar & Active Folder Summary */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="bg-white dark:bg-slate-900 p-3.5 rounded-2xl border border-slate-200 dark:border-slate-800 flex items-center shadow-sm max-w-md w-full">
          <Search className="w-4 h-4 text-slate-400 mr-2 flex-shrink-0" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder={`Search within ${activeFolderName}...`}
            className="w-full bg-transparent text-xs text-slate-900 dark:text-white focus:outline-none"
          />
        </div>

        <div className="text-xs text-slate-500 dark:text-slate-400 font-medium">
          Showing <span className="font-bold text-slate-900 dark:text-white">{courses?.length || 0}</span> courses {selectedFolderId ? `in "${activeFolderName}"` : ''}
        </div>
      </div>

      {/* Course Cards Grid */}
      {(!courses || courses.length === 0) ? (
        <EmptyState
          icon={BookOpen}
          title={selectedFolderId ? `No courses found in "${activeFolderName}"` : "No courses saved yet"}
          description={selectedFolderId ? "Try clearing the search or folder filter." : "Save tutorials, Coursera, edX, or GitHub awesome lists. LinkMind automatically categorizes them into subject folders."}
          actionText="Save Course Link"
          onAction={onOpenCapture}
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {courses.map((c) => (
            <ResourceCard key={c.id} resource={c} />
          ))}
        </div>
      )}
    </div>
  );
};
