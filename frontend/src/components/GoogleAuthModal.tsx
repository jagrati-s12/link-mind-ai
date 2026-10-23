import React, { useState, useEffect } from 'react';
import { Shield, ShieldCheck, ShieldAlert, Copy, Check, X, Loader2, Smartphone, Key } from 'lucide-react';
import { api } from '../services/api';
import { TOTPSetupResponse } from '../types';

interface GoogleAuthModalProps {
  isOpen: boolean;
  onClose: () => void;
  isEnabled: boolean;
  onStatusChange?: () => void;
}

export const GoogleAuthModal: React.FC<GoogleAuthModalProps> = ({
  isOpen,
  onClose,
  isEnabled,
  onStatusChange
}) => {
  const [setupData, setSetupData] = useState<TOTPSetupResponse | null>(null);
  const [code, setCode] = useState('');
  const [copied, setCopied] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen && !isEnabled) {
      loadSetupData();
    } else {
      setSetupData(null);
      setCode('');
      setError(null);
      setSuccessMsg(null);
    }
  }, [isOpen, isEnabled]);

  const loadSetupData = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.get2FASetup();
      setSetupData(data);
    } catch (err: any) {
      setError(err.message || 'Failed to initialize Google Authenticator setup.');
    } finally {
      setLoading(false);
    }
  };

  const handleCopySecret = () => {
    if (setupData?.secret) {
      navigator.clipboard.writeText(setupData.secret);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleEnable = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!code || code.length < 6) {
      setError('Please enter the 6-digit verification code from your Google Authenticator app.');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const res = await api.enable2FA(code);
      setSuccessMsg(res.message || 'Google Authenticator 2FA enabled successfully!');
      setCode('');
      if (onStatusChange) onStatusChange();
      setTimeout(() => {
        onClose();
      }, 1800);
    } catch (err: any) {
      setError(err.message || 'Invalid verification code. Please check Google Authenticator.');
    } finally {
      setLoading(false);
    }
  };

  const handleDisable = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!code || code.length < 6) {
      setError('Please enter your current 6-digit Google Authenticator code to confirm disabling.');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const res = await api.disable2FA(code);
      setSuccessMsg(res.message || 'Google Authenticator 2FA has been disabled.');
      setCode('');
      if (onStatusChange) onStatusChange();
      setTimeout(() => {
        onClose();
      }, 1800);
    } catch (err: any) {
      setError(err.message || 'Verification failed. Could not disable 2FA.');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in">
      <div className="relative w-full max-w-lg bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-2xl overflow-hidden p-6 max-h-[90vh] overflow-y-auto custom-scrollbar">
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 p-1 rounded-lg transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Modal Header */}
        <div className="flex items-center gap-3 mb-5">
          <div className="w-11 h-11 rounded-xl bg-blue-50 dark:bg-blue-950/70 border border-blue-200 dark:border-blue-800 flex items-center justify-center text-blue-600 dark:text-blue-400">
            <Smartphone className="w-6 h-6" />
          </div>
          <div>
            <h3 className="text-xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
              Google Authenticator
              {isEnabled ? (
                <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300 font-medium">
                  Active
                </span>
              ) : (
                <span className="text-xs px-2 py-0.5 rounded-full bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300 font-medium">
                  Two-Factor Auth
                </span>
              )}
            </h3>
            <p className="text-sm text-slate-500 dark:text-slate-400">
              {isEnabled
                ? 'Your account is secured with 2FA code verification.'
                : 'Protect your saved opportunities, roadmaps, and profile with TOTP 2FA.'}
            </p>
          </div>
        </div>

        {/* Error / Success messages */}
        {error && (
          <div className="mb-4 p-3.5 rounded-xl bg-red-50 dark:bg-red-950/60 border border-red-200 dark:border-red-900/60 text-sm text-red-700 dark:text-red-300 flex items-start gap-2.5">
            <ShieldAlert className="w-5 h-5 flex-shrink-0 mt-0.5 text-red-600" />
            <span>{error}</span>
          </div>
        )}

        {successMsg && (
          <div className="mb-4 p-3.5 rounded-xl bg-emerald-50 dark:bg-emerald-950/60 border border-emerald-200 dark:border-emerald-900/60 text-sm text-emerald-700 dark:text-emerald-300 flex items-start gap-2.5">
            <ShieldCheck className="w-5 h-5 flex-shrink-0 mt-0.5 text-emerald-600" />
            <span>{successMsg}</span>
          </div>
        )}

        {/* Flow: Setup (When not enabled) */}
        {!isEnabled ? (
          <div>
            {loading && !setupData ? (
              <div className="py-12 flex flex-col items-center justify-center gap-3">
                <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
                <p className="text-sm text-slate-500">Generating Google Authenticator key...</p>
              </div>
            ) : setupData ? (
              <form onSubmit={handleEnable} className="space-y-5">
                {/* Step 1: Scan QR */}
                <div className="p-4 bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-800 rounded-xl space-y-3">
                  <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-blue-600 dark:text-blue-400">
                    <span className="w-5 h-5 rounded-full bg-blue-100 dark:bg-blue-900 flex items-center justify-center text-xs">1</span>
                    Scan QR code with Google Authenticator
                  </div>
                  <p className="text-xs text-slate-500 dark:text-slate-400">
                    Open Google Authenticator on your phone, tap the <b>+</b> button, and choose <b>Scan a QR code</b>.
                  </p>
                  <div className="flex justify-center p-3 bg-white rounded-lg border border-slate-200 w-fit mx-auto">
                    <img
                      src={setupData.qr_code}
                      alt="Google Authenticator QR Code"
                      className="w-44 h-44 object-contain"
                    />
                  </div>

                  {/* Manual Secret Key */}
                  <div className="pt-2 border-t border-slate-200 dark:border-slate-700/60">
                    <p className="text-xs text-slate-500 dark:text-slate-400 mb-1 flex items-center gap-1">
                      <Key className="w-3.5 h-3.5" /> Can't scan? Enter secret manually:
                    </p>
                    <div className="flex items-center gap-2">
                      <code className="flex-1 px-2.5 py-1.5 text-xs font-mono bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-800 dark:text-slate-200 select-all overflow-x-auto">
                        {setupData.secret}
                      </code>
                      <button
                        type="button"
                        onClick={handleCopySecret}
                        className="px-2.5 py-1.5 text-xs bg-slate-200 hover:bg-slate-300 dark:bg-slate-700 dark:hover:bg-slate-600 text-slate-700 dark:text-slate-200 rounded-lg flex items-center gap-1 transition-colors"
                      >
                        {copied ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
                        {copied ? 'Copied' : 'Copy'}
                      </button>
                    </div>
                  </div>
                </div>

                {/* Step 2: Verification Code */}
                <div className="p-4 bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-800 rounded-xl space-y-3">
                  <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-blue-600 dark:text-blue-400">
                    <span className="w-5 h-5 rounded-full bg-blue-100 dark:bg-blue-900 flex items-center justify-center text-xs">2</span>
                    Enter 6-digit code to activate
                  </div>
                  <p className="text-xs text-slate-500 dark:text-slate-400">
                    Enter the time-sensitive 6-digit verification code generated by Google Authenticator:
                  </p>
                  <div>
                    <input
                      type="text"
                      maxLength={6}
                      value={code}
                      onChange={(e) => setCode(e.target.value.replace(/\D/g, ''))}
                      placeholder="e.g. 123456"
                      className="w-full text-center text-2xl font-mono tracking-widest px-4 py-2.5 bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-xl focus:ring-2 focus:ring-blue-500 focus:outline-none dark:text-white"
                      autoFocus
                    />
                  </div>
                </div>

                {/* Actions */}
                <div className="flex items-center justify-end gap-3 pt-2">
                  <button
                    type="button"
                    onClick={onClose}
                    className="px-4 py-2 text-sm text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-xl transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={loading || code.length < 6}
                    className="px-5 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed rounded-xl shadow-sm transition-all flex items-center gap-2"
                  >
                    {loading && <Loader2 className="w-4 h-4 animate-spin" />}
                    Activate Google Authenticator
                  </button>
                </div>
              </form>
            ) : null}
          </div>
        ) : (
          /* Flow: Disable 2FA (When already enabled) */
          <form onSubmit={handleDisable} className="space-y-4">
            <div className="p-4 bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-900/50 rounded-xl text-amber-800 dark:text-amber-300 text-sm">
              <p className="font-semibold mb-1">Disable Two-Factor Authentication?</p>
              <p className="text-xs text-amber-700 dark:text-amber-400">
                Disabling 2FA makes your account less secure. To confirm that it is you, please enter your current 6-digit code from Google Authenticator.
              </p>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5">
                Current 6-Digit Google Authenticator Code
              </label>
              <input
                type="text"
                maxLength={6}
                value={code}
                onChange={(e) => setCode(e.target.value.replace(/\D/g, ''))}
                placeholder="123456"
                className="w-full text-center text-xl font-mono tracking-widest px-4 py-2.5 bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 rounded-xl focus:ring-2 focus:ring-red-500 focus:outline-none dark:text-white"
                autoFocus
              />
            </div>

            <div className="flex items-center justify-end gap-3 pt-3">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 text-sm text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-xl transition-colors"
              >
                Keep Active
              </button>
              <button
                type="submit"
                disabled={loading || code.length < 6}
                className="px-5 py-2 text-sm font-medium text-white bg-red-600 hover:bg-red-500 disabled:opacity-50 disabled:cursor-not-allowed rounded-xl shadow-sm transition-all flex items-center gap-2"
              >
                {loading && <Loader2 className="w-4 h-4 animate-spin" />}
                Confirm & Disable 2FA
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
};
