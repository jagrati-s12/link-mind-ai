import React, { useState, useEffect } from 'react';
import { Download, Trash2, Shield, Moon, Sun, Database, Smartphone, ShieldCheck, ShieldAlert } from 'lucide-react';
import { api } from '../services/api';
import { useTheme } from '../context/ThemeContext';
import { useAuth } from '../context/AuthContext';
import { GoogleAuthModal } from '../components/GoogleAuthModal';

export const Settings: React.FC = () => {
  const { theme, toggleTheme } = useTheme();
  const { user, refreshUser } = useAuth();
  const [isExporting, setIsExporting] = useState(false);
  const [exportMsg, setExportMsg] = useState<string | null>(null);
  const [is2FAModalOpen, setIs2FAModalOpen] = useState(false);
  const [totpEnabled, setTotpEnabled] = useState<boolean>(user?.is_totp_enabled || false);

  useEffect(() => {
    check2FAStatus();
  }, [user]);

  const check2FAStatus = async () => {
    try {
      const res = await api.get2FAStatus();
      setTotpEnabled(res.is_totp_enabled);
    } catch {
      // fallback to user state
      if (user) setTotpEnabled(user.is_totp_enabled);
    }
  };

  const handleExport = async () => {
    setIsExporting(true);
    setExportMsg(null);
    try {
      const data = await api.exportData();
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `linkmind_library_export_${new Date().toISOString().slice(0, 10)}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      setExportMsg('Export downloaded successfully!');
    } catch (err: any) {
      setExportMsg(`Export failed: ${err.message}`);
    } finally {
      setIsExporting(false);
    }
  };

  const handleDeleteAccount = async () => {
    if (window.confirm("CAUTION: This will permanently erase your entire opportunity library, resumes, and saved applications. Are you sure?")) {
      try {
        await api.deleteAccount();
        window.location.reload();
      } catch (err: any) {
        alert(`Deletion failed: ${err.message}`);
      }
    }
  };

  return (
    <div className="space-y-8 max-w-4xl mx-auto animate-fade-in pb-12">
      <div>
        <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Workspace Settings</h1>
        <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
          Export data, adjust appearance, and view privacy safeguards
        </p>
      </div>

      {/* Appearance */}
      <div className="bg-white dark:bg-slate-900 p-6 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-sm flex items-center justify-between">
        <div>
          <h2 className="text-sm font-bold text-slate-900 dark:text-white">Interface Theme</h2>
          <p className="text-xs text-slate-400 mt-0.5">Toggle between crisp neutral light and dark modes</p>
        </div>
        <button
          onClick={toggleTheme}
          className="flex items-center space-x-2 px-4 py-2 rounded-xl bg-slate-100 dark:bg-slate-800 text-xs font-semibold text-slate-700 dark:text-slate-200 hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors"
        >
          {theme === 'dark' ? <Sun className="w-4 h-4 text-amber-400" /> : <Moon className="w-4 h-4 text-slate-600" />}
          <span>{theme === 'dark' ? 'Light Mode' : 'Dark Mode'}</span>
        </button>
      </div>

      {/* Data Export (GDPR Portability) */}
      <div className="bg-white dark:bg-slate-900 p-6 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-sm space-y-4">
        <div>
          <h2 className="text-sm font-bold text-slate-900 dark:text-white">Data Export & Backup</h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Download your complete opportunity workspace as a JSON archive (courses, internships, resumes, notes, and roadmaps).
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={handleExport}
            disabled={isExporting}
            className="flex items-center space-x-2 bg-slate-800 dark:bg-slate-700 hover:bg-slate-900 text-white font-medium text-xs px-4 py-2.5 rounded-xl shadow-sm transition-colors"
          >
            <Download className="w-4 h-4" />
            <span>{isExporting ? 'Generating JSON...' : 'Export All Library Data (JSON)'}</span>
          </button>
          {exportMsg && <span className="text-xs text-emerald-600 font-medium">{exportMsg}</span>}
        </div>
      </div>

      {/* Google Authenticator Two-Factor Authentication (2FA) */}
      <div className="bg-white dark:bg-slate-900 p-6 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-sm space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-start space-x-3.5">
            <div className={`w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 ${
              totpEnabled
                ? 'bg-emerald-50 dark:bg-emerald-950/60 text-emerald-600 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800/60'
                : 'bg-blue-50 dark:bg-blue-950/60 text-blue-600 dark:text-blue-400 border border-blue-200 dark:border-blue-800/60'
            }`}>
              <Smartphone className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h2 className="text-sm font-bold text-slate-900 dark:text-white">Google Authenticator (TOTP 2FA)</h2>
                {totpEnabled ? (
                  <span className="flex items-center gap-1 text-[11px] font-semibold px-2 py-0.5 rounded-full bg-emerald-100 dark:bg-emerald-950 text-emerald-700 dark:text-emerald-300">
                    <ShieldCheck className="w-3 h-3" /> Enabled
                  </span>
                ) : (
                  <span className="flex items-center gap-1 text-[11px] font-semibold px-2 py-0.5 rounded-full bg-amber-100 dark:bg-amber-950 text-amber-700 dark:text-amber-300">
                    <ShieldAlert className="w-3 h-3" /> Recommended
                  </span>
                )}
              </div>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 max-w-lg">
                Secure your workspace and login credentials with Time-Based One-Time Passwords (TOTP) from the Google Authenticator app on iOS or Android.
              </p>
            </div>
          </div>

          <button
            onClick={() => setIs2FAModalOpen(true)}
            className={`px-4 py-2 rounded-xl text-xs font-semibold shadow-sm transition-colors flex items-center justify-center space-x-1.5 shrink-0 ${
              totpEnabled
                ? 'bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 border border-slate-300 dark:border-slate-700'
                : 'bg-blue-600 hover:bg-blue-700 text-white'
            }`}
          >
            <Smartphone className="w-3.5 h-3.5" />
            <span>{totpEnabled ? 'Manage 2FA Settings' : 'Setup Google Authenticator'}</span>
          </button>
        </div>
      </div>

      {/* Security & SSRF Protection Status */}
      <div className="bg-white dark:bg-slate-900 p-6 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-sm space-y-3">
        <div className="flex items-center space-x-2 text-emerald-600 dark:text-emerald-400">
          <Shield className="w-5 h-5" />
          <h2 className="text-sm font-bold text-slate-900 dark:text-white">Security & SSRF Safeguards Active</h2>
        </div>
        <p className="text-xs text-slate-500 leading-relaxed">
          LinkMind's server-side ingestion enforces strict security validation:
        </p>
        <ul className="text-xs text-slate-600 dark:text-slate-400 space-y-1 list-disc list-inside">
          <li>Blocks loopback destinations (127.0.0.1, localhost)</li>
          <li>Rejects cloud metadata endpoints (169.254.169.254) and private subnets</li>
          <li>Validates redirects dynamically before fetching content</li>
          <li>Strictly separates untrusted scraped webpage content from model instructions</li>
        </ul>
      </div>

      {/* Danger Zone: Delete Account */}
      <div className="bg-red-50/50 dark:bg-red-950/20 p-6 rounded-3xl border border-red-200 dark:border-red-900/40 space-y-3">
        <h2 className="text-sm font-bold text-rose-700 dark:text-rose-400">Danger Zone</h2>
        <p className="text-xs text-slate-600 dark:text-slate-400">
          Permanently delete your account and all associated saved resources and resumes.
        </p>
        <button
          onClick={handleDeleteAccount}
          className="flex items-center space-x-1.5 px-4 py-2 rounded-xl text-xs font-semibold text-white bg-rose-600 hover:bg-rose-700 shadow-sm transition-colors"
        >
          <Trash2 className="w-3.5 h-3.5" />
          <span>Permanently Delete Account</span>
        </button>
      </div>

      <GoogleAuthModal
        isOpen={is2FAModalOpen}
        onClose={() => setIs2FAModalOpen(false)}
        isEnabled={totpEnabled}
        onStatusChange={() => {
          check2FAStatus();
          refreshUser();
        }}
      />
    </div>
  );
};
