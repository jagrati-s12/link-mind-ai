import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Inbox as InboxIcon,
  Link2,
  ListPlus,
  FileUp,
  RefreshCw,
  Trash2,
  CheckCircle2,
  AlertTriangle,
  Clock,
  ExternalLink,
  Plus
} from 'lucide-react';
import { api } from '../services/api';
import { EmptyState } from '../components/EmptyState';

interface InboxProps {
  onOpenCapture: () => void;
}

export const Inbox: React.FC<InboxProps> = ({ onOpenCapture }) => {
  const queryClient = useQueryClient();
  const [singleUrl, setSingleUrl] = useState('');
  const [bulkUrls, setBulkUrls] = useState('');
  const [activeTab, setActiveTab] = useState<'single' | 'bulk'>('single');
  const [statusMsg, setStatusMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const { data: sources, isLoading } = useQuery({
    queryKey: ['inbox-sources'],
    queryFn: api.getSources
  });

  const submitSingleMutation = useMutation({
    mutationFn: (url: string) => api.submitUrl(url),
    onSuccess: (data) => {
      setStatusMsg({ type: 'success', text: `Extracted ${data.resource_count} individual opportunities!` });
      setSingleUrl('');
      queryClient.invalidateQueries({ queryKey: ['inbox-sources'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard-stats'] });
    },
    onError: (err: any) => {
      setStatusMsg({ type: 'error', text: err.message || 'Failed to process URL.' });
    }
  });

  const submitBulkMutation = useMutation({
    mutationFn: (urls: string[]) => api.bulkImport(urls),
    onSuccess: () => {
      setStatusMsg({ type: 'success', text: 'Bulk import job started in background!' });
      setBulkUrls('');
      queryClient.invalidateQueries({ queryKey: ['inbox-sources'] });
    },
    onError: (err: any) => {
      setStatusMsg({ type: 'error', text: err.message || 'Failed to start bulk import.' });
    }
  });

  const reprocessMutation = useMutation({
    mutationFn: (id: number) => api.reprocessSource(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['inbox-sources'] });
    }
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => api.deleteSource(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['inbox-sources'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard-stats'] });
    }
  });

  const handleSingleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (singleUrl.trim()) {
      setStatusMsg(null);
      submitSingleMutation.mutate(singleUrl.trim());
    }
  };

  const handleBulkSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const urls = bulkUrls.split('\n').map(u => u.trim()).filter(Boolean);
    if (urls.length) {
      setStatusMsg(null);
      submitBulkMutation.mutate(urls);
    }
  };

  return (
    <div className="space-y-8 max-w-6xl mx-auto animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Universal Link Inbox</h1>
        <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
          Paste links or upload documents. LinkMind extracts individual records, identifies skills, and organizes them automatically.
        </p>
      </div>

      {/* Input Section */}
      <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-6 shadow-sm">
        <div className="flex border-b border-slate-100 dark:border-slate-800 mb-5 pb-2 space-x-4">
          <button
            onClick={() => setActiveTab('single')}
            className={`flex items-center space-x-2 text-xs font-semibold pb-2 border-b-2 transition-colors ${
              activeTab === 'single'
                ? 'border-brand-600 text-brand-600 dark:text-brand-400'
                : 'border-transparent text-slate-400 hover:text-slate-600'
            }`}
          >
            <Link2 className="w-3.5 h-3.5" />
            <span>Single Opportunity or Post</span>
          </button>
          <button
            onClick={() => setActiveTab('bulk')}
            className={`flex items-center space-x-2 text-xs font-semibold pb-2 border-b-2 transition-colors ${
              activeTab === 'bulk'
                ? 'border-brand-600 text-brand-600 dark:text-brand-400'
                : 'border-transparent text-slate-400 hover:text-slate-600'
            }`}
          >
            <ListPlus className="w-3.5 h-3.5" />
            <span>Bulk Links</span>
          </button>
        </div>

        {statusMsg && (
          <div className={`mb-4 p-3 rounded-xl text-xs flex items-center space-x-2 ${
            statusMsg.type === 'success'
              ? 'bg-emerald-50 dark:bg-emerald-950/40 text-emerald-600 border border-emerald-200'
              : 'bg-red-50 dark:bg-red-950/40 text-red-600 border border-red-200'
          }`}>
            <span>{statusMsg.text}</span>
          </div>
        )}

        {activeTab === 'single' ? (
          <form onSubmit={handleSingleSubmit} className="flex gap-2">
            <input
              type="url"
              required
              value={singleUrl}
              onChange={(e) => setSingleUrl(e.target.value)}
              placeholder="Paste LinkedIn post URL, course syllabus, or internship link..."
              className="flex-1 px-4 py-2.5 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-xs sm:text-sm text-slate-900 dark:text-white focus:outline-none focus:border-brand-500"
            />
            <button
              type="submit"
              disabled={submitSingleMutation.isPending || !singleUrl.trim()}
              className="bg-brand-600 hover:bg-brand-700 disabled:opacity-50 text-white font-medium text-xs px-5 py-2.5 rounded-xl shadow-sm whitespace-nowrap transition-colors"
            >
              {submitSingleMutation.isPending ? 'Extracting...' : 'Extract & Save'}
            </button>
          </form>
        ) : (
          <form onSubmit={handleBulkSubmit} className="space-y-3">
            <textarea
              rows={4}
              required
              value={bulkUrls}
              onChange={(e) => setBulkUrls(e.target.value)}
              placeholder="Paste multiple URLs (one per line)..."
              className="w-full p-3.5 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-xs font-mono text-slate-900 dark:text-white focus:outline-none focus:border-brand-500"
            />
            <button
              type="submit"
              disabled={submitBulkMutation.isPending || !bulkUrls.trim()}
              className="bg-brand-600 hover:bg-brand-700 disabled:opacity-50 text-white font-medium text-xs px-5 py-2 rounded-xl shadow-sm transition-colors"
            >
              {submitBulkMutation.isPending ? 'Queueing...' : 'Import All'}
            </button>
          </form>
        )}
      </div>

      {/* Sources List */}
      <div>
        <h2 className="text-base font-bold text-slate-900 dark:text-white mb-3">Ingested Sources & Files</h2>
        
        {(!sources || sources.length === 0) ? (
          <EmptyState
            icon={InboxIcon}
            title="No links or sources ingested yet"
            description="Paste a URL or upload a PDF above to extract individual opportunities."
            actionText="Paste Link"
            onAction={onOpenCapture}
          />
        ) : (
          <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 overflow-hidden shadow-sm">
            <div className="divide-y divide-slate-100 dark:divide-slate-800">
              {sources.map((src) => (
                <div key={src.id} className="p-4 sm:p-5 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 hover:bg-slate-50 dark:hover:bg-slate-800/40 transition-colors">
                  <div className="space-y-1 max-w-xl">
                    <div className="flex items-center space-x-2">
                      <span className="text-xs font-bold text-slate-900 dark:text-white truncate">
                        {src.title}
                      </span>
                      <span className="text-[10px] font-semibold px-2 py-0.5 rounded-md bg-slate-100 dark:bg-slate-800 text-slate-500 uppercase">
                        {src.source_type}
                      </span>
                    </div>

                    {src.original_url && (
                      <a
                        href={src.original_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-xs text-brand-600 dark:text-brand-400 hover:underline flex items-center space-x-1"
                      >
                        <span className="truncate max-w-md">{src.original_url}</span>
                        <ExternalLink className="w-3 h-3 shrink-0" />
                      </a>
                    )}

                    {src.error_message && (
                      <p className="text-xs text-rose-500 font-medium">
                        Error: {src.error_message}
                      </p>
                    )}
                  </div>

                  <div className="flex items-center space-x-4 self-end sm:self-center">
                    {/* Status badge */}
                    <div className="flex items-center space-x-1.5">
                      {src.extraction_status === 'completed' && (
                        <span className="flex items-center space-x-1 text-xs font-medium text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/40 px-2.5 py-1 rounded-lg">
                          <CheckCircle2 className="w-3.5 h-3.5" />
                          <span>{src.resource_count} Extracted</span>
                        </span>
                      )}
                      {src.extraction_status === 'processing' && (
                        <span className="flex items-center space-x-1 text-xs font-medium text-amber-600 bg-amber-50 px-2.5 py-1 rounded-lg animate-pulse">
                          <Clock className="w-3.5 h-3.5" />
                          <span>Processing</span>
                        </span>
                      )}
                      {src.extraction_status === 'failed' && (
                        <span className="flex items-center space-x-1 text-xs font-medium text-rose-600 bg-rose-50 px-2.5 py-1 rounded-lg">
                          <AlertTriangle className="w-3.5 h-3.5" />
                          <span>Failed</span>
                        </span>
                      )}
                    </div>

                    <button
                      onClick={() => reprocessMutation.mutate(src.id)}
                      title="Reprocess Source"
                      className="p-1.5 text-slate-400 hover:text-brand-600 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors"
                    >
                      <RefreshCw className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => deleteMutation.mutate(src.id)}
                      title="Delete Source"
                      className="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors"
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
    </div>
  );
};
