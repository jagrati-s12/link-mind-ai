import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import {
  BookOpen,
  Briefcase,
  Trophy,
  Sparkles,
  Calendar,
  FolderKanban,
  ArrowRight,
  TrendingUp,
  Inbox as InboxIcon,
  Compass,
  Link2,
  FileUp,
  ListPlus
} from 'lucide-react';
import { api } from '../services/api';
import { ResourceCard } from '../components/ResourceCard';
import { EmptyState } from '../components/EmptyState';

interface DashboardProps {
  onOpenCapture: () => void;
}

export const Dashboard: React.FC<DashboardProps> = ({ onOpenCapture }) => {
  const [quickUrl, setQuickUrl] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [quickMsg, setQuickMsg] = useState<string | null>(null);

  const { data: stats, refetch: refetchStats } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: api.getStats
  });

  const { data: collections } = useQuery({
    queryKey: ['dashboard-collections'],
    queryFn: api.getCollections
  });

  const { data: resources, refetch: refetchResources } = useQuery({
    queryKey: ['dashboard-resources'],
    queryFn: () => api.getResources()
  });

  const handleQuickCapture = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!quickUrl.trim()) return;
    setIsSubmitting(true);
    setQuickMsg(null);
    try {
      const res = await api.submitUrl(quickUrl.trim());
      setQuickMsg(`Saved! Extracted ${res.resource_count} opportunity records.`);
      setQuickUrl('');
      refetchStats();
      refetchResources();
    } catch (err: any) {
      setQuickMsg(err.message || 'Failed to capture.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const strongMatches = (resources || []).filter(r => (r.recommendation?.fit_score || 0) >= 75);
  const recentResources = (resources || []).slice(0, 6);

  return (
    <div className="space-y-8 animate-fade-in max-w-7xl mx-auto">
      {/* Top Banner / Quick Capture Area */}
      <div className="bg-gradient-to-br from-white to-slate-50 dark:from-slate-900 dark:to-slate-950 p-6 md:p-8 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-sm">
        <div className="max-w-2xl mb-6">
          <span className="text-xs font-bold uppercase tracking-wider text-brand-600 dark:text-brand-400">
            LinkMind AI Workspace
          </span>
          <h1 className="text-2xl md:text-3xl font-extrabold text-slate-900 dark:text-white mt-1 tracking-tight">
            Your Personal Opportunity Workspace
          </h1>
          <p className="text-xs md:text-sm text-slate-500 dark:text-slate-400 mt-2 leading-relaxed">
            Paste courses, internships, LinkedIn posts, or docs. The AI extracts every opportunity,
            evaluates match scores against your resume, and organizes them automatically.
          </p>
        </div>

        {/* Quick Capture Input Box */}
        <div className="bg-white dark:bg-slate-800/90 p-4 rounded-2xl border border-slate-200/80 dark:border-slate-700 shadow-inner max-w-3xl">
          <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 block mb-2">
            Quick Capture
          </span>
          <form onSubmit={handleQuickCapture} className="flex flex-col sm:flex-row gap-2">
            <div className="relative flex-1">
              <Link2 className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="url"
                required
                value={quickUrl}
                onChange={(e) => setQuickUrl(e.target.value)}
                placeholder="Paste a course, LinkedIn post, document, or internship URL..."
                className="w-full pl-9 pr-4 py-2.5 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl text-xs sm:text-sm text-slate-900 dark:text-white focus:outline-none focus:border-brand-500"
              />
            </div>
            <button
              type="submit"
              disabled={isSubmitting || !quickUrl.trim()}
              className="bg-brand-600 hover:bg-brand-700 disabled:opacity-50 text-white font-medium text-xs px-5 py-2.5 rounded-xl shadow-sm transition-all whitespace-nowrap"
            >
              {isSubmitting ? 'Extracting...' : 'Capture Link'}
            </button>
          </form>

          {quickMsg && (
            <p className="text-xs mt-2 text-brand-600 dark:text-brand-400 font-medium">{quickMsg}</p>
          )}

          <div className="flex items-center space-x-4 mt-3 pt-3 border-t border-slate-100 dark:border-slate-700/60 text-xs text-slate-500">
            <button onClick={onOpenCapture} className="hover:text-brand-600 flex items-center space-x-1">
              <ListPlus className="w-3.5 h-3.5" />
              <span>Bulk import</span>
            </button>
            <span className="text-slate-300 dark:text-slate-700">•</span>
            <button onClick={onOpenCapture} className="hover:text-brand-600 flex items-center space-x-1">
              <FileUp className="w-3.5 h-3.5" />
              <span>PDF / document</span>
            </button>
          </div>
        </div>
      </div>

      {/* Real Database Count Cards */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3.5">
        <div className="bg-white dark:bg-slate-900 p-4 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-500 dark:text-slate-400">Courses saved</span>
            <div className="p-1.5 bg-indigo-50 dark:bg-indigo-950/50 rounded-xl text-indigo-600 dark:text-indigo-400">
              <BookOpen className="w-4 h-4" />
            </div>
          </div>
          <div className="text-xl md:text-2xl font-extrabold text-slate-900 dark:text-white mt-2.5">
            {stats?.courses_saved ?? 0}
          </div>
        </div>

        <div className="bg-white dark:bg-slate-900 p-4 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-500 dark:text-slate-400">Internships saved</span>
            <div className="p-1.5 bg-amber-50 dark:bg-amber-950/50 rounded-xl text-amber-600 dark:text-amber-400">
              <Briefcase className="w-4 h-4" />
            </div>
          </div>
          <div className="text-xl md:text-2xl font-extrabold text-slate-900 dark:text-white mt-2.5">
            {stats?.internships_saved ?? 0}
          </div>
        </div>

        <div className="bg-white dark:bg-slate-900 p-4 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-500 dark:text-slate-400">Hackathons</span>
            <div className="p-1.5 bg-orange-50 dark:bg-orange-950/50 rounded-xl text-orange-600 dark:text-orange-400">
              <Trophy className="w-4 h-4" />
            </div>
          </div>
          <div className="text-xl md:text-2xl font-extrabold text-slate-900 dark:text-white mt-2.5">
            {stats?.hackathons_saved ?? 0}
          </div>
        </div>

        <div className="bg-white dark:bg-slate-900 p-4 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-500 dark:text-slate-400">Strong matches</span>
            <div className="p-1.5 bg-emerald-50 dark:bg-emerald-950/50 rounded-xl text-emerald-600 dark:text-emerald-400">
              <Sparkles className="w-4 h-4" />
            </div>
          </div>
          <div className="text-xl md:text-2xl font-extrabold text-slate-900 dark:text-white mt-2.5">
            {stats?.strong_matches ?? 0}
          </div>
        </div>

        <div className="bg-white dark:bg-slate-900 p-4 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm col-span-2 md:col-span-1">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-500 dark:text-slate-400">Upcoming deadlines</span>
            <div className="p-1.5 bg-rose-50 dark:bg-rose-950/50 rounded-xl text-rose-600 dark:text-rose-400">
              <Calendar className="w-4 h-4" />
            </div>
          </div>
          <div className="text-xl md:text-2xl font-extrabold text-slate-900 dark:text-white mt-2.5">
            {stats?.upcoming_deadlines ?? 0}
          </div>
        </div>
      </div>

      {/* Your Collections */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-lg font-bold text-slate-900 dark:text-white">Your Collections</h2>
            <p className="text-xs text-slate-500 dark:text-slate-400">Subject folders with zero record duplication</p>
          </div>
          <Link
            to="/collections"
            className="text-xs font-semibold text-brand-600 dark:text-brand-400 hover:underline flex items-center space-x-1"
          >
            <span>All folders</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
          {(collections || []).slice(0, 4).map((col) => (
            <Link
              key={col.id}
              to={`/collections/${col.id}`}
              className="bg-white dark:bg-slate-900 p-5 rounded-2xl border border-slate-200 dark:border-slate-800 hover:border-brand-500/50 hover:shadow-sm transition-all group"
            >
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 rounded-xl bg-brand-50 dark:bg-brand-950/60 text-brand-600 dark:text-brand-400 flex items-center justify-center font-bold">
                  <FolderKanban className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="font-semibold text-sm text-slate-900 dark:text-white group-hover:text-brand-600 transition-colors">
                    {col.name}
                  </h3>
                  <span className="text-xs text-slate-400">
                    {col.resource_count} items
                  </span>
                </div>
              </div>
            </Link>
          ))}
        </div>
      </div>

      {/* Recent / Recommended Opportunities */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-lg font-bold text-slate-900 dark:text-white">Recent Opportunities</h2>
            <p className="text-xs text-slate-500 dark:text-slate-400">Extracted from your saved sources</p>
          </div>
          <Link
            to="/resources"
            className="text-xs font-semibold text-brand-600 dark:text-brand-400 hover:underline flex items-center space-x-1"
          >
            <span>View all</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        {recentResources.length === 0 ? (
          <EmptyState
            icon={InboxIcon}
            title="Your library is currently empty"
            description="Paste an opportunity link or upload a document containing multiple internship vacancies to start building your personalized workspace."
            actionText="Capture First Link"
            onAction={onOpenCapture}
          />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {recentResources.map((res) => (
              <ResourceCard key={res.id} resource={res} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
