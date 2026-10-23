import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { CheckSquare, Calendar, Building, ExternalLink, Trash2, Clock, Plus } from 'lucide-react';
import { Link } from 'react-router-dom';
import { api } from '../services/api';
import { EmptyState } from '../components/EmptyState';
import { ApplicationStatus } from '../types';

export const Applications: React.FC = () => {
  const queryClient = useQueryClient();
  const [selectedFilter, setSelectedFilter] = useState<string>('all');

  const { data: applications, isLoading } = useQuery({
    queryKey: ['applications-list'],
    queryFn: api.getApplications
  });

  const updateAppMutation = useMutation({
    mutationFn: ({ id, status }: { id: number; status: ApplicationStatus }) =>
      api.updateApplication(id, { status }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['applications-list'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard-stats'] });
    }
  });

  const deleteAppMutation = useMutation({
    mutationFn: (id: number) => api.deleteApplication(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['applications-list'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard-stats'] });
    }
  });

  const stages: ApplicationStatus[] = [
    'Saved', 'Shortlisted', 'Preparing', 'Applied',
    'Assessment', 'Interview', 'Offer', 'Rejected'
  ];

  const filtered = (applications || []).filter(app => {
    if (selectedFilter === 'all') return true;
    return app.status.toLowerCase() === selectedFilter.toLowerCase();
  });

  return (
    <div className="space-y-6 max-w-7xl mx-auto animate-fade-in pb-12">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Internship Applications Tracker</h1>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            Track interview rounds, submission deadlines, and status updates for your opportunities
          </p>
        </div>

        <Link
          to="/internships"
          className="self-start sm:self-auto bg-brand-600 hover:bg-brand-700 text-white font-medium text-xs px-4 py-2 rounded-xl shadow-sm transition-colors"
        >
          Track From Saved Internships
        </Link>
      </div>

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
          All Stages ({applications?.length || 0})
        </button>
        {stages.map((st) => {
          const count = (applications || []).filter(a => a.status === st).length;
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

      {/* Applications List / Table */}
      {filtered.length === 0 ? (
        <EmptyState
          icon={CheckSquare}
          title="No applications tracked in this view"
          description="Open any saved internship opportunity and set its application status to 'Shortlisted' or 'Applied' to track deadlines and interview stages."
        />
      ) : (
        <div className="bg-white dark:bg-slate-900 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-sm overflow-hidden">
          <div className="divide-y divide-slate-100 dark:divide-slate-800">
            {filtered.map((app) => (
              <div
                key={app.id}
                className="p-5 flex flex-col md:flex-row md:items-center justify-between gap-4 hover:bg-slate-50 dark:hover:bg-slate-800/40 transition-colors"
              >
                <div className="space-y-1.5 max-w-lg">
                  <div className="flex items-center space-x-2">
                    <Link
                      to={`/resources/${app.resource_id}`}
                      className="font-bold text-slate-900 dark:text-white text-sm hover:text-brand-600 transition-colors"
                    >
                      {app.resource?.title || 'Tracked Opportunity'}
                    </Link>
                  </div>

                  {app.resource?.organization && (
                    <div className="flex items-center space-x-1.5 text-xs text-slate-500">
                      <Building className="w-3.5 h-3.5" />
                      <span>{app.resource.organization}</span>
                    </div>
                  )}

                  {app.notes && (
                    <p className="text-xs text-slate-600 dark:text-slate-400 italic">
                      "{app.notes}"
                    </p>
                  )}
                </div>

                <div className="flex flex-wrap items-center gap-4">
                  {/* Deadline */}
                  {app.deadline && (
                    <div className="flex items-center space-x-1 text-xs text-rose-600 dark:text-rose-400 font-medium">
                      <Calendar className="w-3.5 h-3.5" />
                      <span>{app.deadline}</span>
                    </div>
                  )}

                  {/* Stage Selector */}
                  <select
                    value={app.status}
                    onChange={(e) => updateAppMutation.mutate({ id: app.id, status: e.target.value as ApplicationStatus })}
                    className="text-xs font-semibold bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl px-3 py-1.5 text-slate-900 dark:text-white focus:outline-none focus:border-brand-500"
                  >
                    {stages.map((s) => (
                      <option key={s} value={s}>{s}</option>
                    ))}
                  </select>

                  <button
                    onClick={() => deleteAppMutation.mutate(app.id)}
                    className="p-1.5 text-slate-400 hover:text-rose-600 transition-colors rounded-lg"
                    title="Remove from applications"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
