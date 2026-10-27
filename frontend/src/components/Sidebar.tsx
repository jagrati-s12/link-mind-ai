import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Inbox,
  BookOpen,
  Briefcase,
  Trophy,
  FolderKanban,
  GitFork,
  Map,
  CheckSquare,
  UserCheck,
  Settings,
  Plus,
  Layers,
  Sparkles,
  Sun,
  Moon,
  Building2,
  GraduationCap,
  PanelLeftClose,
  PanelLeftOpen
} from 'lucide-react';
import { useTheme } from '../context/ThemeContext';

interface SidebarProps {
  onOpenCapture: () => void;
  isCollapsed: boolean;
  onToggleCollapse: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ onOpenCapture, isCollapsed, onToggleCollapse }) => {
  const { theme, toggleTheme } = useTheme();

  const navItems = [
    { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { to: '/inbox', label: 'Inbox', icon: Inbox },
    { to: '/resources', label: 'All Resources', icon: Layers },
    { to: '/courses', label: 'Courses', icon: BookOpen },
    { to: '/course-tracker', label: 'Course Tracker', icon: GraduationCap },
    { to: '/internships', label: 'Internships', icon: Briefcase },
    { to: '/jobs', label: 'Jobs', icon: Building2 },
    { to: '/hackathons', label: 'Hackathons', icon: Trophy },
    { to: '/collections', label: 'Collections', icon: FolderKanban },
    { to: '/skills', label: 'Skill Map', icon: GitFork },
    { to: '/roadmaps', label: 'My Roadmaps', icon: Map },
    { to: '/applications', label: 'Internship Tracker', icon: CheckSquare },
    { to: '/profile', label: 'Profile & Resume', icon: UserCheck },
    { to: '/settings', label: 'Settings', icon: Settings },
  ];

  return (
    <aside
      className={`bg-white dark:bg-slate-900 border-r border-slate-200 dark:border-slate-800 flex flex-col h-screen select-none transition-all duration-300 shrink-0 ${
        isCollapsed ? 'w-20' : 'w-64'
      }`}
    >
      {/* Brand Header */}
      <div className="h-16 flex items-center justify-between px-4 border-b border-slate-200 dark:border-slate-800 overflow-hidden">
        <NavLink to="/dashboard" className={`flex items-center space-x-2.5 ${isCollapsed ? 'justify-center w-full' : ''}`}>
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-brand-600 to-indigo-600 flex items-center justify-center text-white shadow-md shadow-brand-500/20 shrink-0">
            <Sparkles className="w-5 h-5" />
          </div>
          {!isCollapsed && (
            <div className="truncate">
              <span className="font-bold text-lg tracking-tight text-slate-900 dark:text-white">
                LinkMind<span className="text-brand-500 font-extrabold ml-0.5">AI</span>
              </span>
              <span className="block text-[10px] uppercase font-semibold text-slate-400 tracking-wider">
                Opportunity Intel
              </span>
            </div>
          )}
        </NavLink>
      </div>

      {/* Quick Action Button / Collapse Toggle */}
      <div className="p-3 space-y-2">
        {!isCollapsed ? (
          <button
            onClick={onOpenCapture}
            className="w-full flex items-center justify-center space-x-2 bg-brand-600 hover:bg-brand-700 text-white font-medium py-2.5 px-4 rounded-xl shadow-sm transition-all duration-150 active:scale-[0.98]"
          >
            <Plus className="w-4 h-4" />
            <span className="text-sm">Capture Link / File</span>
          </button>
        ) : (
          <button
            onClick={onOpenCapture}
            className="w-full flex items-center justify-center bg-brand-600 hover:bg-brand-700 text-white p-2.5 rounded-xl shadow-sm transition-all duration-150"
            title="Capture Link / File"
          >
            <Plus className="w-5 h-5" />
          </button>
        )}
      </div>

      {/* Nav List */}
      <nav className="flex-1 px-3 space-y-1 overflow-y-auto custom-scrollbar">
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.to}
              to={item.to}
              title={isCollapsed ? item.label : undefined}
              className={({ isActive }) =>
                `flex items-center ${isCollapsed ? 'justify-center px-2' : 'space-x-3 px-3'} py-2 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-brand-50 dark:bg-brand-950/60 text-brand-600 dark:text-brand-400'
                    : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800/60 hover:text-slate-900 dark:hover:text-slate-200'
                }`
              }
            >
              <Icon className="w-4 h-4 shrink-0" />
              {!isCollapsed && <span className="truncate">{item.label}</span>}
            </NavLink>
          );
        })}
      </nav>

      {/* Footer controls & Collapse Toggle */}
      <div className="p-3 border-t border-slate-200 dark:border-slate-800 flex items-center justify-between">
        {!isCollapsed && (
          <div className="flex items-center space-x-2 text-xs text-slate-500 dark:text-slate-400 truncate">
            <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse shrink-0" />
            <span className="truncate">Active</span>
          </div>
        )}
        <div className={`flex items-center ${isCollapsed ? 'justify-center w-full space-y-1 flex-col' : 'space-x-1'}`}>
          <button
            onClick={toggleTheme}
            className="p-2 rounded-lg text-slate-500 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
            title="Toggle Theme"
          >
            {theme === 'dark' ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
          </button>
          <button
            onClick={onToggleCollapse}
            className="p-2 rounded-lg text-slate-500 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
            title={isCollapsed ? 'Expand Sidebar' : 'Collapse Sidebar'}
          >
            {isCollapsed ? <PanelLeftOpen className="w-4 h-4" /> : <PanelLeftClose className="w-4 h-4" />}
          </button>
        </div>
      </div>
    </aside>
  );
};
