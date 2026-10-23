import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, Plus, Bell, ShieldCheck } from 'lucide-react';

interface HeaderProps {
  onOpenCapture: () => void;
}

export const Header: React.FC<HeaderProps> = ({ onOpenCapture }) => {
  const [searchQuery, setSearchQuery] = useState('');
  const navigate = useNavigate();

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      navigate(`/resources?search=${encodeURIComponent(searchQuery.trim())}`);
    }
  };

  return (
    <header className="h-16 bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 px-6 flex items-center justify-between sticky top-0 z-20">
      {/* Global Search Bar */}
      <form onSubmit={handleSearchSubmit} className="relative flex-1 max-w-md">
        <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Search opportunities, skills, companies..."
          className="w-full pl-9 pr-4 py-2 bg-slate-100 dark:bg-slate-800/80 border border-transparent focus:border-brand-500 rounded-xl text-sm focus:outline-none text-slate-800 dark:text-slate-100 placeholder-slate-400 transition-all"
        />
      </form>

      {/* Right Controls */}
      <div className="flex items-center space-x-3 ml-4">
        <div className="hidden sm:flex items-center space-x-1.5 px-3 py-1 bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-400 rounded-lg text-xs font-medium border border-emerald-200 dark:border-emerald-800/50">
          <ShieldCheck className="w-3.5 h-3.5" />
          <span>SSRF Protected</span>
        </div>

        <button
          onClick={onOpenCapture}
          className="flex items-center space-x-1.5 bg-brand-50 dark:bg-brand-950/50 hover:bg-brand-100 dark:hover:bg-brand-900/60 text-brand-600 dark:text-brand-400 font-medium text-xs px-3 py-2 rounded-lg border border-brand-200 dark:border-brand-800 transition-colors"
        >
          <Plus className="w-3.5 h-3.5" />
          <span>Quick Capture</span>
        </button>
      </div>
    </header>
  );
};
