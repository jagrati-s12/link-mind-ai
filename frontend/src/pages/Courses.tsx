import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { BookOpen, Search } from 'lucide-react';
import { api } from '../services/api';
import { ResourceCard } from '../components/ResourceCard';
import { EmptyState } from '../components/EmptyState';

interface CoursesProps {
  onOpenCapture: () => void;
}

export const Courses: React.FC<CoursesProps> = ({ onOpenCapture }) => {
  const [searchTerm, setSearchTerm] = useState('');

  const { data: courses, isLoading } = useQuery({
    queryKey: ['courses-list', searchTerm],
    queryFn: () => api.getResources({
      type: 'courses',
      search: searchTerm.trim() || undefined
    })
  });

  return (
    <div className="space-y-6 max-w-7xl mx-auto animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">All Courses & Learning</h1>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            Searchable course catalog mapped directly to skills and target internships
          </p>
        </div>

        <button
          onClick={onOpenCapture}
          className="self-start sm:self-auto bg-brand-600 hover:bg-brand-700 text-white font-medium text-xs px-4 py-2 rounded-xl shadow-sm transition-colors"
        >
          + Add Course
        </button>
      </div>

      <div className="bg-white dark:bg-slate-900 p-4 rounded-2xl border border-slate-200 dark:border-slate-800 flex items-center shadow-sm max-w-md">
        <Search className="w-4 h-4 text-slate-400 mr-2" />
        <input
          type="text"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          placeholder="Filter courses by topic or skill taught..."
          className="w-full bg-transparent text-xs text-slate-900 dark:text-white focus:outline-none"
        />
      </div>

      {(!courses || courses.length === 0) ? (
        <EmptyState
          icon={BookOpen}
          title="No courses saved yet"
          description="Save tutorials, Coursera, edX, or YouTube course links. LinkMind extracts taught skills and connects them to target internships."
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
