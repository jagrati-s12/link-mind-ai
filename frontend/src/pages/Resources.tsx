import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useSearchParams } from 'react-router-dom';
import { Layers, Search, Filter, Folder } from 'lucide-react';
import { api } from '../services/api';
import { ResourceCard } from '../components/ResourceCard';
import { EmptyState } from '../components/EmptyState';

interface ResourcesProps {
  onOpenCapture: () => void;
}

export const Resources: React.FC<ResourcesProps> = ({ onOpenCapture }) => {
  const [searchParams, setSearchParams] = useSearchParams();
  const searchInitial = searchParams.get('search') || '';
  const [searchTerm, setSearchTerm] = useState(searchInitial);
  const [selectedType, setSelectedType] = useState<string>('all');
  const [selectedCol, setSelectedCol] = useState<number | undefined>(undefined);

  const { data: collections } = useQuery({
    queryKey: ['resources-collections'],
    queryFn: api.getCollections
  });

  const { data: resources, isLoading } = useQuery({
    queryKey: ['resources-list', selectedType, selectedCol, searchTerm],
    queryFn: () => api.getResources({
      type: selectedType === 'all' ? undefined : selectedType,
      collection_id: selectedCol,
      search: searchTerm.trim() || undefined
    })
  });

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setSearchParams(searchTerm.trim() ? { search: searchTerm.trim() } : {});
  };

  const types = [
    { value: 'all', label: 'All Resources' },
    { value: 'internship', label: 'Internships' },
    { value: 'hackathon', label: 'Hackathons' },
    { value: 'course', label: 'Courses' },
    { value: 'job', label: 'Jobs' },
    { value: 'project', label: 'Projects' },
    { value: 'certification', label: 'Certifications' }
  ];

  return (
    <div className="space-y-6 max-w-7xl mx-auto animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">All Resources</h1>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            Searchable opportunity library with automated classification & resume fit scores
          </p>
        </div>

        <button
          onClick={onOpenCapture}
          className="self-start sm:self-auto bg-brand-600 hover:bg-brand-700 text-white font-medium text-xs px-4 py-2 rounded-xl shadow-sm transition-colors"
        >
          + Add Opportunity
        </button>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-white dark:bg-slate-900 p-4 rounded-2xl border border-slate-200 dark:border-slate-800 flex flex-col md:flex-row gap-3 items-stretch md:items-center justify-between shadow-sm">
        {/* Type selector */}
        <div className="flex flex-wrap gap-1.5">
          {types.map((t) => (
            <button
              key={t.value}
              onClick={() => setSelectedType(t.value)}
              className={`text-xs font-medium px-3 py-1.5 rounded-xl transition-colors ${
                selectedType === t.value
                  ? 'bg-brand-600 text-white shadow-sm'
                  : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700'
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>

        {/* Collection filter & Search form */}
        <div className="flex items-center gap-2">
          {collections && collections.length > 0 && (
            <select
              value={selectedCol || ''}
              onChange={(e) => setSelectedCol(e.target.value ? Number(e.target.value) : undefined)}
              className="text-xs bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl px-3 py-2 text-slate-700 dark:text-slate-200 focus:outline-none focus:border-brand-500"
            >
              <option value="">All Collections</option>
              {collections.map((c) => (
                <option key={c.id} value={c.id}>{c.name}</option>
              ))}
            </select>
          )}

          <form onSubmit={handleSearchSubmit} className="relative min-w-[200px]">
            <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search library..."
              className="w-full pl-8 pr-3 py-1.5 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-xs text-slate-900 dark:text-white focus:outline-none focus:border-brand-500"
            />
          </form>
        </div>
      </div>

      {/* Grid of Resources */}
      {(!resources || resources.length === 0) ? (
        <EmptyState
          icon={Layers}
          title="No resources found"
          description={searchTerm ? `No opportunities matching "${searchTerm}". Try adjusting your filters.` : "Your opportunity library is currently empty. Start by capturing a course or internship link!"}
          actionText="Capture Resource"
          onAction={onOpenCapture}
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {resources.map((res) => (
            <ResourceCard key={res.id} resource={res} />
          ))}
        </div>
      )}
    </div>
  );
};
