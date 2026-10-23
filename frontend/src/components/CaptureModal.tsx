import React, { useState } from 'react';
import { X, Link2, ListPlus, FileUp, Loader2, CheckCircle2, AlertCircle } from 'lucide-react';
import { api } from '../services/api';

interface CaptureModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export const CaptureModal: React.FC<CaptureModalProps> = ({ isOpen, onClose, onSuccess }) => {
  const [activeTab, setActiveTab] = useState<'single' | 'bulk' | 'file'>('single');
  const [singleUrl, setSingleUrl] = useState('');
  const [bulkUrls, setBulkUrls] = useState('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  if (!isOpen) return null;

  const resetState = () => {
    setSingleUrl('');
    setBulkUrls('');
    setSelectedFile(null);
    setErrorMessage(null);
    setSuccessMessage(null);
    setIsLoading(false);
  };

  const handleClose = () => {
    resetState();
    onClose();
  };

  const handleSingleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!singleUrl.trim()) return;
    setIsLoading(true);
    setErrorMessage(null);
    setSuccessMessage(null);

    try {
      const result = await api.submitUrl(singleUrl.trim());
      setSuccessMessage(`Successfully extracted ${result.resource_count} opportunity/course records!`);
      setTimeout(() => {
        onSuccess();
        handleClose();
      }, 1200);
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to extract opportunity.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleBulkSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const urls = bulkUrls.split('\n').map(u => u.trim()).filter(Boolean);
    if (!urls.length) return;
    setIsLoading(true);
    setErrorMessage(null);
    setSuccessMessage(null);

    try {
      await api.bulkImport(urls);
      setSuccessMessage(`Bulk import job queued for ${urls.length} links!`);
      setTimeout(() => {
        onSuccess();
        handleClose();
      }, 1200);
    } catch (err: any) {
      setErrorMessage(err.message || 'Bulk import failed.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleFileSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) return;
    setIsLoading(true);
    setErrorMessage(null);
    setSuccessMessage(null);

    try {
      const result = await api.uploadDocument(selectedFile);
      setSuccessMessage(`Document parsed: ${result.resource_count} opportunities identified!`);
      setTimeout(() => {
        onSuccess();
        handleClose();
      }, 1200);
    } catch (err: any) {
      setErrorMessage(err.message || 'File upload extraction failed.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-sm animate-fade-in">
      <div className="bg-white dark:bg-slate-900 rounded-2xl max-w-lg w-full border border-slate-200 dark:border-slate-800 shadow-2xl overflow-hidden">
        {/* Modal Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200 dark:border-slate-800">
          <div>
            <h3 className="font-semibold text-slate-900 dark:text-white text-base">Quick Capture</h3>
            <p className="text-xs text-slate-500 dark:text-slate-400">Extract and organize opportunities automatically</p>
          </div>
          <button
            onClick={handleClose}
            className="p-1 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-slate-200 dark:border-slate-800 px-6 pt-2">
          <button
            onClick={() => setActiveTab('single')}
            className={`flex items-center space-x-2 py-2.5 px-3 border-b-2 font-medium text-xs transition-colors ${
              activeTab === 'single'
                ? 'border-brand-600 text-brand-600 dark:text-brand-400'
                : 'border-transparent text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'
            }`}
          >
            <Link2 className="w-3.5 h-3.5" />
            <span>Single Link</span>
          </button>
          <button
            onClick={() => setActiveTab('bulk')}
            className={`flex items-center space-x-2 py-2.5 px-3 border-b-2 font-medium text-xs transition-colors ${
              activeTab === 'bulk'
                ? 'border-brand-600 text-brand-600 dark:text-brand-400'
                : 'border-transparent text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'
            }`}
          >
            <ListPlus className="w-3.5 h-3.5" />
            <span>Bulk Import</span>
          </button>
          <button
            onClick={() => setActiveTab('file')}
            className={`flex items-center space-x-2 py-2.5 px-3 border-b-2 font-medium text-xs transition-colors ${
              activeTab === 'file'
                ? 'border-brand-600 text-brand-600 dark:text-brand-400'
                : 'border-transparent text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'
            }`}
          >
            <FileUp className="w-3.5 h-3.5" />
            <span>PDF / Document</span>
          </button>
        </div>

        {/* Tab Content */}
        <div className="p-6">
          {errorMessage && (
            <div className="mb-4 p-3 bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-900 rounded-xl text-red-600 dark:text-red-400 text-xs flex items-start space-x-2">
              <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
              <span>{errorMessage}</span>
            </div>
          )}

          {successMessage && (
            <div className="mb-4 p-3 bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-900 rounded-xl text-emerald-600 dark:text-emerald-400 text-xs flex items-center space-x-2">
              <CheckCircle2 className="w-4 h-4 shrink-0" />
              <span>{successMessage}</span>
            </div>
          )}

          {activeTab === 'single' && (
            <form onSubmit={handleSingleSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5">
                  Opportunity or Course URL
                </label>
                <input
                  type="url"
                  required
                  value={singleUrl}
                  onChange={(e) => setSingleUrl(e.target.value)}
                  placeholder="https://www.linkedin.com/posts/... or https://coursera.org/..."
                  className="w-full px-3.5 py-2.5 bg-slate-50 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700 rounded-xl text-sm focus:outline-none focus:border-brand-500 text-slate-900 dark:text-white"
                />
                <p className="text-[11px] text-slate-400 mt-1">
                  Supports LinkedIn posts, company job pages, course syllabi, and docs with multiple opportunities.
                </p>
              </div>

              <div className="flex justify-end space-x-2 pt-2">
                <button
                  type="button"
                  onClick={handleClose}
                  className="px-4 py-2 text-xs font-medium text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-xl"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isLoading || !singleUrl.trim()}
                  className="flex items-center space-x-1.5 px-4 py-2 text-xs font-medium bg-brand-600 hover:bg-brand-700 text-white rounded-xl disabled:opacity-50 transition-colors"
                >
                  {isLoading && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                  <span>{isLoading ? 'Extracting...' : 'Extract & Save'}</span>
                </button>
              </div>
            </form>
          )}

          {activeTab === 'bulk' && (
            <form onSubmit={handleBulkSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5">
                  Enter URLs (one per line)
                </label>
                <textarea
                  rows={5}
                  required
                  value={bulkUrls}
                  onChange={(e) => setBulkUrls(e.target.value)}
                  placeholder="https://careers.google.com/jobs/1&#10;https://stripe.com/jobs/intern&#10;https://coursera.org/learn/ml"
                  className="w-full px-3.5 py-2.5 bg-slate-50 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700 rounded-xl text-xs font-mono focus:outline-none focus:border-brand-500 text-slate-900 dark:text-white"
                />
              </div>

              <div className="flex justify-end space-x-2 pt-2">
                <button
                  type="button"
                  onClick={handleClose}
                  className="px-4 py-2 text-xs font-medium text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-xl"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isLoading || !bulkUrls.trim()}
                  className="flex items-center space-x-1.5 px-4 py-2 text-xs font-medium bg-brand-600 hover:bg-brand-700 text-white rounded-xl disabled:opacity-50 transition-colors"
                >
                  {isLoading && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                  <span>{isLoading ? 'Queueing Import...' : 'Import All URLs'}</span>
                </button>
              </div>
            </form>
          )}

          {activeTab === 'file' && (
            <form onSubmit={handleFileSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5">
                  Upload PDF, DOCX, or Text Document
                </label>
                <div className="border-2 border-dashed border-slate-300 dark:border-slate-700 rounded-2xl p-6 text-center hover:bg-slate-50 dark:hover:bg-slate-800/40 transition-colors">
                  <FileUp className="w-8 h-8 text-slate-400 mx-auto mb-2" />
                  <input
                    type="file"
                    id="docUpload"
                    accept=".pdf,.docx,.txt,.md"
                    className="hidden"
                    onChange={(e) => {
                      if (e.target.files && e.target.files[0]) {
                        setSelectedFile(e.target.files[0]);
                      }
                    }}
                  />
                  <label
                    htmlFor="docUpload"
                    className="cursor-pointer text-xs font-medium text-brand-600 dark:text-brand-400 hover:underline"
                  >
                    {selectedFile ? selectedFile.name : 'Choose a file from your computer'}
                  </label>
                  <p className="text-[11px] text-slate-400 mt-1">
                    Supports documents with lists of multiple internship vacancies or course catalogs
                  </p>
                </div>
              </div>

              <div className="flex justify-end space-x-2 pt-2">
                <button
                  type="button"
                  onClick={handleClose}
                  className="px-4 py-2 text-xs font-medium text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-xl"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isLoading || !selectedFile}
                  className="flex items-center space-x-1.5 px-4 py-2 text-xs font-medium bg-brand-600 hover:bg-brand-700 text-white rounded-xl disabled:opacity-50 transition-colors"
                >
                  {isLoading && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                  <span>{isLoading ? 'Processing Document...' : 'Upload & Parse'}</span>
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  );
};
