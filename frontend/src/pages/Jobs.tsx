import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Building2, Search } from 'lucide-react';
import { api } from '../services/api';
import { ResourceCard } from '../components/ResourceCard';
import { EmptyState } from '../components/EmptyState';

interface JobsProps {
  onOpenCapture: () => void;
}

export const Jobs: React.FC<JobsProps> = ({ onOpenCapture }) => {
  const [searchTerm, setSearchTerm] = useState('');

  const { data: jobs, isLoading } = useQuery({
    queryKey: ['jobs-list', searchTerm],
    queryFn: () => api.getResources({
      type: 'jobs',
      search: searchTerm.trim() || undefined
    })
  });

  return (
    <div className="space-y-6 max-w-7xl mx-auto animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Full-Time & Engineering Jobs</h1>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            Individually extracted job postings with required tech stacks, compensation, and resume match scores
          </p>
        </div>

        <button
          onClick={onOpenCapture}
          className="self-start sm:self-auto bg-brand-600 hover:bg-brand-700 text-white font-medium text-xs px-4 py-2 rounded-xl shadow-sm transition-colors"
        >
          + Add Job Listing
        </button>
      </div>

      <div className="bg-white dark:bg-slate-900 p-4 rounded-2xl border border-slate-200 dark:border-slate-800 flex items-center shadow-sm max-w-md">
        <Search className="w-4 h-4 text-slate-400 mr-2" />
        <input
          type="text"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          placeholder="Filter by title, company, or required skill..."
          className="w-full bg-transparent text-xs text-slate-900 dark:text-white focus:outline-none"
        />
      </div>

      {(!jobs || jobs.length === 0) ? (
        <EmptyState
          icon={Building2}
          title="No full-time jobs saved yet"
          description="Paste any career URL or job posting from LinkedIn, company portals, or job boards to analyze requirements and fit score."
          actionText="Capture Job Posting"
          onAction={onOpenCapture}
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {jobs.map((job) => (
            <ResourceCard key={job.id} resource={job} />
          ))}
        </div>
      )}
    </div>
  );
};
