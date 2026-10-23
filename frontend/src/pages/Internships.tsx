import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Briefcase, Search } from 'lucide-react';
import { api } from '../services/api';
import { ResourceCard } from '../components/ResourceCard';
import { EmptyState } from '../components/EmptyState';

interface InternshipsProps {
  onOpenCapture: () => void;
}

export const Internships: React.FC<InternshipsProps> = ({ onOpenCapture }) => {
  const [searchTerm, setSearchTerm] = useState('');

  const { data: internships, isLoading } = useQuery({
    queryKey: ['internships-list', searchTerm],
    queryFn: () => api.getResources({
      type: 'internships',
      search: searchTerm.trim() || undefined
    })
  });

  return (
    <div className="space-y-6 max-w-7xl mx-auto animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Internships & Opportunities</h1>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            Individually extracted vacancy records with transparent fit score breakdown and deadlines
          </p>
        </div>

        <button
          onClick={onOpenCapture}
          className="self-start sm:self-auto bg-brand-600 hover:bg-brand-700 text-white font-medium text-xs px-4 py-2 rounded-xl shadow-sm transition-colors"
        >
          + Add Opportunity
        </button>
      </div>

      <div className="bg-white dark:bg-slate-900 p-4 rounded-2xl border border-slate-200 dark:border-slate-800 flex items-center shadow-sm max-w-md">
        <Search className="w-4 h-4 text-slate-400 mr-2" />
        <input
          type="text"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          placeholder="Filter by role, company, or required skill..."
          className="w-full bg-transparent text-xs text-slate-900 dark:text-white focus:outline-none"
        />
      </div>

      {(!internships || internships.length === 0) ? (
        <EmptyState
          icon={Briefcase}
          title="No internships saved yet"
          description="Paste an internship URL or a LinkedIn post containing a list of vacancies to extract each opportunity separately."
          actionText="Capture Internship"
          onAction={onOpenCapture}
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {internships.map((item) => (
            <ResourceCard key={item.id} resource={item} />
          ))}
        </div>
      )}
    </div>
  );
};
