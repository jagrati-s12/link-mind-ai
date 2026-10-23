import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Trophy, Search, Sparkles, ExternalLink, Calendar, MapPin, DollarSign } from 'lucide-react';
import { api } from '../services/api';
import { ResourceCard } from '../components/ResourceCard';
import { EmptyState } from '../components/EmptyState';

interface HackathonsProps {
  onOpenCapture: () => void;
}

export const Hackathons: React.FC<HackathonsProps> = ({ onOpenCapture }) => {
  const [searchTerm, setSearchTerm] = useState('');

  const { data: hackathons, isLoading } = useQuery({
    queryKey: ['hackathons-list', searchTerm],
    queryFn: () => api.getResources({
      type: 'hackathons',
      search: searchTerm.trim() || undefined
    })
  });

  return (
    <div className="space-y-6 max-w-7xl mx-auto animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <Trophy className="w-6 h-6 text-orange-500" />
            <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Hackathons & Competitions</h1>
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            Track Devpost, MLH, and university hackathons with prize pools, themes, deadlines, and skill matching
          </p>
        </div>

        <button
          onClick={onOpenCapture}
          className="self-start sm:self-auto bg-orange-600 hover:bg-orange-700 text-white font-medium text-xs px-4 py-2 rounded-xl shadow-sm transition-colors"
        >
          + Add Hackathon
        </button>
      </div>

      {/* Filter and Search */}
      <div className="bg-white dark:bg-slate-900 p-4 rounded-2xl border border-slate-200 dark:border-slate-800 flex items-center shadow-sm max-w-md">
        <Search className="w-4 h-4 text-slate-400 mr-2" />
        <input
          type="text"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          placeholder="Filter by theme, prize, or tech stack (e.g. AI, Web3, Python)..."
          className="w-full bg-transparent text-xs text-slate-900 dark:text-white focus:outline-none"
        />
      </div>

      {/* Hackathons Grid */}
      {(!hackathons || hackathons.length === 0) ? (
        <EmptyState
          icon={Trophy}
          title="No hackathons saved yet"
          description="Paste a Devpost, Unstop, MLH, or company hackathon link. LinkMind extracts the prize pool, registration deadline, themes, and evaluates how well your skills match!"
          actionText="Capture Hackathon Link"
          onAction={onOpenCapture}
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {hackathons.map((h) => (
            <ResourceCard key={h.id} resource={h} />
          ))}
        </div>
      )}
    </div>
  );
};
