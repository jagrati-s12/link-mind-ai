import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { FolderKanban, Plus, Folder, Sparkles, Layers, Trash2 } from 'lucide-react';
import { api } from '../services/api';
import { Collection } from '../types';

export const Collections: React.FC = () => {
  const queryClient = useQueryClient();
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newColName, setNewColName] = useState('');
  const [newColDesc, setNewColDesc] = useState('');

  const { data: collections, isLoading } = useQuery({
    queryKey: ['collections-list'],
    queryFn: api.getCollections
  });

  const createMutation = useMutation({
    mutationFn: (data: { name: string; description: string }) => api.createCollection(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['collections-list'] });
      setShowCreateModal(false);
      setNewColName('');
      setNewColDesc('');
    }
  });

  const handleCreateSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (newColName.trim()) {
      createMutation.mutate({ name: newColName.trim(), description: newColDesc.trim() });
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Your Collections</h1>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            Connected subject folders. Opportunities can belong to multiple folders without duplicate records.
          </p>
        </div>

        <button
          onClick={() => setShowCreateModal(true)}
          className="self-start sm:self-auto flex items-center space-x-1.5 bg-brand-600 hover:bg-brand-700 text-white font-medium text-xs px-4 py-2 rounded-xl shadow-sm transition-colors"
        >
          <Plus className="w-4 h-4" />
          <span>New Collection</span>
        </button>
      </div>

      {/* Grid of Collections */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-5">
        {(collections || []).map((col) => (
          <Link
            key={col.id}
            to={`/collections/${col.id}`}
            className="bg-white dark:bg-slate-900 p-5 rounded-2xl border border-slate-200 dark:border-slate-800 hover:border-brand-500/50 hover:shadow-md transition-all flex flex-col justify-between group"
          >
            <div>
              <div className="flex items-center justify-between mb-3">
                <div className="w-10 h-10 rounded-xl bg-brand-50 dark:bg-brand-950/60 text-brand-600 dark:text-brand-400 flex items-center justify-center font-bold">
                  {col.is_smart ? <Sparkles className="w-5 h-5" /> : <Folder className="w-5 h-5" />}
                </div>

                <span className="text-[11px] font-semibold text-slate-500 dark:text-slate-400 bg-slate-100 dark:bg-slate-800 px-2 py-0.5 rounded-full">
                  {col.resource_count} items
                </span>
              </div>

              <h3 className="font-semibold text-slate-900 dark:text-white text-base group-hover:text-brand-600 transition-colors">
                {col.name}
              </h3>

              {col.description && (
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-1.5 line-clamp-2 leading-relaxed">
                  {col.description}
                </p>
              )}
            </div>

            <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between text-xs text-brand-600 dark:text-brand-400 font-medium">
              <span>Open folder</span>
              <span>→</span>
            </div>
          </Link>
        ))}
      </div>

      {/* Modal for creating custom collection */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-sm animate-fade-in">
          <div className="bg-white dark:bg-slate-900 rounded-2xl max-w-md w-full border border-slate-200 dark:border-slate-800 p-6 shadow-2xl">
            <h3 className="text-base font-bold text-slate-900 dark:text-white mb-1">Create New Collection</h3>
            <p className="text-xs text-slate-500 dark:text-slate-400 mb-4">
              Add a custom folder to organize opportunities, courses, or projects.
            </p>

            <form onSubmit={handleCreateSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Collection Name
                </label>
                <input
                  type="text"
                  required
                  value={newColName}
                  onChange={(e) => setNewColName(e.target.value)}
                  placeholder="e.g. Summer 2027 Top Picks, Model Evaluation Courses"
                  className="w-full px-3.5 py-2.5 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-xs sm:text-sm text-slate-900 dark:text-white focus:outline-none focus:border-brand-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Description (optional)
                </label>
                <textarea
                  rows={2}
                  value={newColDesc}
                  onChange={(e) => setNewColDesc(e.target.value)}
                  placeholder="Notes about this collection..."
                  className="w-full px-3.5 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-xs text-slate-900 dark:text-white focus:outline-none focus:border-brand-500"
                />
              </div>

              <div className="flex justify-end space-x-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 text-xs font-medium text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-xl"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={createMutation.isPending || !newColName.trim()}
                  className="px-4 py-2 text-xs font-medium bg-brand-600 hover:bg-brand-700 text-white rounded-xl shadow-sm"
                >
                  Create Collection
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
