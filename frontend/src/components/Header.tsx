import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Search, Plus, ShieldCheck, Smartphone, LogOut, LogIn, User } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

interface HeaderProps {
  onOpenCapture: () => void;
  isSidebarCollapsed?: boolean;
  onToggleSidebar?: () => void;
}

export const Header: React.FC<HeaderProps> = ({ onOpenCapture }) => {
  const [searchQuery, setSearchQuery] = useState('');
  const navigate = useNavigate();
  const { user, isAuthenticated, logout } = useAuth();

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      navigate(`/resources?search=${encodeURIComponent(searchQuery.trim())}`);
    }
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
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

        {user?.is_totp_enabled && (
          <div className="hidden md:flex items-center space-x-1.5 px-2.5 py-1 bg-blue-50 dark:bg-blue-950/40 text-blue-700 dark:text-blue-300 rounded-lg text-xs font-medium border border-blue-200 dark:border-blue-800/50" title="Protected by Google Authenticator">
            <Smartphone className="w-3.5 h-3.5" />
            <span>2FA Active</span>
          </div>
        )}

        <button
          onClick={onOpenCapture}
          className="flex items-center space-x-1.5 bg-brand-50 dark:bg-brand-950/50 hover:bg-brand-100 dark:hover:bg-brand-900/60 text-brand-600 dark:text-brand-400 font-medium text-xs px-3 py-2 rounded-lg border border-brand-200 dark:border-brand-800 transition-colors"
        >
          <Plus className="w-3.5 h-3.5" />
          <span>Quick Capture</span>
        </button>

        {/* User Account / Auth Actions */}
        {isAuthenticated ? (
          <div className="flex items-center space-x-2 pl-2 border-l border-slate-200 dark:border-slate-800">
            <Link
              to="/profile"
              className="flex items-center space-x-2 p-1.5 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-xl transition-colors text-left"
              title={user?.email}
            >
              <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-blue-600 to-indigo-600 flex items-center justify-center text-white text-xs font-semibold">
                {user?.full_name ? user.full_name[0].toUpperCase() : 'U'}
              </div>
              <div className="hidden xl:block">
                <div className="text-xs font-semibold text-slate-800 dark:text-slate-200 truncate max-w-[110px]">
                  {user?.full_name || 'Account'}
                </div>
                <div className="text-[10px] text-slate-400 truncate max-w-[110px]">
                  {user?.email}
                </div>
              </div>
            </Link>

            <button
              onClick={handleLogout}
              className="p-2 text-slate-400 hover:text-rose-600 dark:hover:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-950/30 rounded-lg transition-colors"
              title="Sign Out"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        ) : (
          <Link
            to="/login"
            className="flex items-center space-x-1.5 px-3 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold transition-colors"
          >
            <LogIn className="w-3.5 h-3.5" />
            <span>Sign In</span>
          </Link>
        )}
      </div>
    </header>
  );
};
