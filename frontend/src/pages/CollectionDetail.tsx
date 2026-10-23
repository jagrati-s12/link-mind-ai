import React, { useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Folder, ArrowLeft, Trash2, Edit2, Layers } from 'lucide-react';
import { api } from '../services/api';
import { ResourceCard } from '../components/ResourceCard';
import { EmptyState } from '../components/EmptyState';

export const CollectionDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const collectionId = Number(id);

  const { data: collection, isLoading: isColLoading } = useQuery({
    queryKey: ['collection-detail', collectionId],
    queryFn: () => api.getCollection(collectionId)
  });

  const { data: resources, isLoading: isResLoading } = useQuery({
    queryKey: ['collection-resources', collectionId],
    queryFn: () => api.getResources({ collection_id: collectionId })
  });

  const deleteColMutation = useMutation({
    mutationFn: () => api.deleteCollection(collectionId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['collections-list'] });
      navigate('/collections');
    }
  });

  const handleDelete = () => {
    if (window.confirm("Delete this collection? Your saved opportunities will remain safe in your library.")) {
      deleteColMutation.mutate();
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto animate-fade-in">
      <div className="flex items-center space-x-2 text-xs text-slate-500">
        <Link to="/collections" className="hover:text-brand-600 flex items-center space-x-1">
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Collections</span>
        </Link>
        <span>/</span>
        <span className="text-slate-800 dark:text-slate-200 font-medium">{collection?.name || 'Folder'}</span>
      </div>

      {/* Collection Header */}
      <div className="bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-200 dark:border-slate-800 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 shadow-sm">
        <div className="flex items-center space-x-4">
          <div className="w-12 h-12 rounded-2xl bg-brand-50 dark:bg-brand-950/60 text-brand-600 dark:text-brand-400 flex items-center justify-center font-bold">
            <Folder className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-slate-900 dark:text-white">{collection?.name}</h1>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 max-w-xl">
              {collection?.description || 'Custom collection folder'}
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          {!collection?.is_system && (
            <button
              onClick={handleDelete}
              className="flex items-center space-x-1 px-3 py-1.5 rounded-xl text-xs font-medium text-rose-600 hover:bg-rose-50 dark:hover:bg-rose-950/40 border border-rose-200 dark:border-rose-900 transition-colors"
            >
              <Trash2 className="w-3.5 h-3.5" />
              <span>Delete Folder</span>
            </button>
          )}
        </div>
      </div>

      {/* Opportunities inside collection */}
      {(!resources || resources.length === 0) ? (
        <EmptyState
          icon={Layers}
          title="Folder is currently empty"
          description="Opportunities assigned to this subject area will appear here automatically, or you can add items from the resource detail page."
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
