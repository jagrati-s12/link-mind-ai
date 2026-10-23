import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  BrainCircuit,
  Lock,
  Mail,
  User,
  ShieldCheck,
  ShieldAlert,
  ArrowRight,
  ArrowLeft,
  Loader2,
  Sparkles,
  Smartphone,
  CheckCircle2,
  KeyRound
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export const Login: React.FC = () => {
  const navigate = useNavigate();
  const { login, register, verify2FA } = useAuth();

  const [mode, setMode] = useState<'signin' | 'signup' | 'totp_challenge'>('signin');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [totpCode, setTotpCode] = useState('');
  const [tempToken, setTempToken] = useState<string | null>(null);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSignIn = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const res = await login(email, password);
      if (res.requires_2fa && res.temp_token) {
        // Transition smoothly to Google Authenticator verification
        setTempToken(res.temp_token);
        setMode('totp_challenge');
        setTotpCode('');
      } else {
        navigate('/dashboard');
      }
    } catch (err: any) {
      setError(err.message || 'Failed to sign in. Please check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  const handleSignUp = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      await register(email, password, fullName);
      navigate('/dashboard');
    } catch (err: any) {
      setError(err.message || 'Failed to create account. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleVerify2FA = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!tempToken || totpCode.length < 6) {
      setError('Please enter the 6-digit code from Google Authenticator.');
      return;
    }

    setError(null);
    setLoading(true);

    try {
      await verify2FA(tempToken, totpCode);
      navigate('/dashboard');
    } catch (err: any) {
      setError(err.message || 'Invalid Google Authenticator code. Please check your app.');
    } finally {
      setLoading(false);
    }
  };

  const handleDemoSignIn = async () => {
    setError(null);
    setLoading(true);
    try {
      // Demo credentials
      await login('demo@linkmind.ai', 'password123');
      navigate('/dashboard');
    } catch (err: any) {
      setError('Could not connect with demo account.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen w-full flex bg-slate-900 text-slate-100 selection:bg-blue-600 selection:text-white">
      {/* Left Column: Visual Brand & Value Proposition */}
      <div className="hidden lg:flex lg:w-1/2 flex-col justify-between p-12 bg-gradient-to-br from-slate-950 via-slate-900 to-blue-950/40 border-r border-slate-800 relative overflow-hidden">
        {/* Background ambient glow circles */}
        <div className="absolute top-1/4 -left-20 w-96 h-96 bg-blue-600/10 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute bottom-10 right-0 w-80 h-80 bg-indigo-600/10 rounded-full blur-3xl pointer-events-none" />

        {/* Brand header */}
        <div className="relative z-10 flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-500 flex items-center justify-center text-white shadow-lg shadow-blue-500/25">
            <BrainCircuit className="w-6 h-6" />
          </div>
          <div>
            <span className="text-xl font-bold tracking-tight text-white">LinkMind AI</span>
            <span className="ml-2 text-xs font-semibold px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/20">
              v2.0
            </span>
          </div>
        </div>

        {/* Center message & feature list */}
        <div className="relative z-10 my-auto py-12 max-w-lg space-y-8">
          <div>
            <h1 className="text-4xl font-extrabold tracking-tight text-white leading-tight">
              Your Personal Opportunity Intelligence Platform.
            </h1>
            <p className="mt-4 text-base text-slate-400 leading-relaxed">
              Transform scattered bookmark URLs from LinkedIn, Hackathons, Devpost, and courses into a structured, personalized opportunity library with zero hallucinations.
            </p>
          </div>

          <div className="space-y-4">
            <div className="flex items-start gap-3.5 p-3.5 rounded-xl bg-slate-800/40 border border-slate-700/50 backdrop-blur-sm">
              <CheckCircle2 className="w-5 h-5 text-blue-400 mt-0.5 flex-shrink-0" />
              <div>
                <h4 className="text-sm font-semibold text-white">One Source → Many Canonical Opportunities</h4>
                <p className="text-xs text-slate-400 mt-0.5">Parse composite posts into individual internships and hackathons without duplication.</p>
              </div>
            </div>

            <div className="flex items-start gap-3.5 p-3.5 rounded-xl bg-slate-800/40 border border-slate-700/50 backdrop-blur-sm">
              <CheckCircle2 className="w-5 h-5 text-blue-400 mt-0.5 flex-shrink-0" />
              <div>
                <h4 className="text-sm font-semibold text-white">Transparent Resume Fit Scoring</h4>
                <p className="text-xs text-slate-400 mt-0.5">Deterministic 5-factor formula: $S = 0.35K + 0.25P + 0.20G + 0.10L + 0.10C$.</p>
              </div>
            </div>

            <div className="flex items-start gap-3.5 p-3.5 rounded-xl bg-slate-800/40 border border-slate-700/50 backdrop-blur-sm">
              <ShieldCheck className="w-5 h-5 text-emerald-400 mt-0.5 flex-shrink-0" />
              <div>
                <h4 className="text-sm font-semibold text-white">Two-Factor Authentication</h4>
                <p className="text-xs text-slate-400 mt-0.5">Industry-standard TOTP with Google Authenticator to keep your career pipeline secure.</p>
              </div>
            </div>
          </div>
        </div>

        {/* Footer info */}
        <div className="relative z-10 flex items-center justify-between text-xs text-slate-500 border-t border-slate-800/80 pt-6">
          <span>© 2026 LinkMind AI. All rights reserved.</span>
          <span className="flex items-center gap-1.5 text-slate-400">
            <Sparkles className="w-3.5 h-3.5 text-blue-400" />
            Built with FastAPI & React
          </span>
        </div>
      </div>

      {/* Right Column: Form Container */}
      <div className="w-full lg:w-1/2 flex items-center justify-center p-6 sm:p-12">
        <div className="w-full max-w-md space-y-6">
          {/* Mobile brand header */}
          <div className="lg:hidden flex items-center gap-3 justify-center mb-6">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-500 flex items-center justify-center text-white shadow-lg">
              <BrainCircuit className="w-6 h-6" />
            </div>
            <span className="text-2xl font-bold tracking-tight text-white">LinkMind AI</span>
          </div>

          {/* Error Banner */}
          {error && (
            <div className="p-4 rounded-xl bg-red-950/60 border border-red-800/60 text-red-200 text-sm flex items-start gap-3 animate-fade-in">
              <ShieldAlert className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
              <div>{error}</div>
            </div>
          )}

          {/* STATE 1 & 2: SIGN IN / SIGN UP */}
          {mode !== 'totp_challenge' ? (
            <div className="bg-slate-800/40 border border-slate-700/60 rounded-2xl p-7 shadow-xl backdrop-blur-sm">
              {/* Tab Selector */}
              <div className="flex bg-slate-900/80 p-1 rounded-xl mb-6 border border-slate-800">
                <button
                  type="button"
                  onClick={() => { setMode('signin'); setError(null); }}
                  className={`flex-1 py-2 text-xs font-semibold rounded-lg transition-all ${
                    mode === 'signin'
                      ? 'bg-blue-600 text-white shadow'
                      : 'text-slate-400 hover:text-white'
                  }`}
                >
                  Sign In
                </button>
                <button
                  type="button"
                  onClick={() => { setMode('signup'); setError(null); }}
                  className={`flex-1 py-2 text-xs font-semibold rounded-lg transition-all ${
                    mode === 'signup'
                      ? 'bg-blue-600 text-white shadow'
                      : 'text-slate-400 hover:text-white'
                  }`}
                >
                  Create Account
                </button>
              </div>

              <div className="mb-6">
                <h2 className="text-2xl font-bold text-white tracking-tight">
                  {mode === 'signin' ? 'Welcome back' : 'Get started with LinkMind'}
                </h2>
                <p className="text-xs text-slate-400 mt-1">
                  {mode === 'signin'
                    ? 'Enter your credentials to access your opportunity dashboard.'
                    : 'Create your account to start managing learning and career opportunities.'}
                </p>
              </div>

              {/* Form */}
              <form onSubmit={mode === 'signin' ? handleSignIn : handleSignUp} className="space-y-4">
                {mode === 'signup' && (
                  <div>
                    <label className="block text-xs font-medium text-slate-300 mb-1.5">
                      Full Name
                    </label>
                    <div className="relative">
                      <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-500">
                        <User className="w-4 h-4" />
                      </div>
                      <input
                        type="text"
                        required
                        value={fullName}
                        onChange={(e) => setFullName(e.target.value)}
                        placeholder="e.g. Alex Sharma"
                        className="w-full pl-10 pr-4 py-2.5 bg-slate-900/90 border border-slate-700 rounded-xl text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors"
                      />
                    </div>
                  </div>
                )}

                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1.5">
                    Email Address
                  </label>
                  <div className="relative">
                    <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-500">
                      <Mail className="w-4 h-4" />
                    </div>
                    <input
                      type="email"
                      required
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder="student@university.edu"
                      className="w-full pl-10 pr-4 py-2.5 bg-slate-900/90 border border-slate-700 rounded-xl text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors"
                    />
                  </div>
                </div>

                <div>
                  <div className="flex items-center justify-between mb-1.5">
                    <label className="text-xs font-medium text-slate-300">Password</label>
                  </div>
                  <div className="relative">
                    <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-500">
                      <Lock className="w-4 h-4" />
                    </div>
                    <input
                      type="password"
                      required
                      minLength={6}
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder="••••••••••••"
                      className="w-full pl-10 pr-4 py-2.5 bg-slate-900/90 border border-slate-700 rounded-xl text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-colors"
                    />
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full py-2.5 mt-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white font-medium text-sm rounded-xl shadow-lg shadow-blue-600/30 transition-all flex items-center justify-center gap-2 group"
                >
                  {loading ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <>
                      {mode === 'signin' ? 'Sign In' : 'Create Account'}
                      <ArrowRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
                    </>
                  )}
                </button>
              </form>

              {/* Divider */}
              <div className="relative my-6">
                <div className="absolute inset-0 flex items-center">
                  <div className="w-full border-t border-slate-700/60" />
                </div>
                <div className="relative flex justify-center text-xs uppercase">
                  <span className="bg-slate-800/90 px-2.5 text-slate-400">or continue with</span>
                </div>
              </div>

              {/* Google Sign In & Demo Account */}
              <div className="space-y-2.5">
                <button
                  type="button"
                  onClick={() => setError('Google OAuth is enabled via Google Authenticator 2FA for secure sign-in.')}
                  className="w-full py-2.5 bg-slate-900 hover:bg-slate-900/80 border border-slate-700 rounded-xl text-sm font-medium text-slate-200 transition-colors flex items-center justify-center gap-3"
                >
                  <svg className="w-4 h-4" viewBox="0 0 24 24">
                    <path
                      fill="#4285F4"
                      d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                    />
                    <path
                      fill="#34A853"
                      d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                    />
                    <path
                      fill="#FBBC05"
                      d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"
                    />
                    <path
                      fill="#EA4335"
                      d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"
                    />
                  </svg>
                  Sign in with Google
                </button>

                <button
                  type="button"
                  onClick={handleDemoSignIn}
                  className="w-full py-2 bg-blue-950/40 hover:bg-blue-900/40 border border-blue-800/40 rounded-xl text-xs font-semibold text-blue-300 transition-colors flex items-center justify-center gap-2"
                >
                  <Sparkles className="w-3.5 h-3.5 text-blue-400" />
                  Try Demo Workspace (1-Click)
                </button>
              </div>
            </div>
          ) : (
            /* STATE 3: GOOGLE AUTHENTICATOR 2FA CHALLENGE */
            <div className="bg-slate-800/40 border border-slate-700/60 rounded-2xl p-7 shadow-xl backdrop-blur-sm animate-fade-in">
              <button
                type="button"
                onClick={() => { setMode('signin'); setTempToken(null); setError(null); }}
                className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-slate-200 mb-4 transition-colors"
              >
                <ArrowLeft className="w-3.5 h-3.5" />
                Back to sign in
              </button>

              <div className="text-center mb-6">
                <div className="w-14 h-14 rounded-2xl bg-blue-600/10 border border-blue-500/20 text-blue-400 flex items-center justify-center mx-auto mb-3 shadow-lg">
                  <Smartphone className="w-7 h-7" />
                </div>
                <h2 className="text-2xl font-bold text-white tracking-tight">
                  Google Authenticator
                </h2>
                <p className="text-xs text-slate-400 mt-1.5 max-w-xs mx-auto">
                  Enter the 6-digit verification code from your <b className="text-slate-300">Google Authenticator</b> app for <span className="text-blue-400 font-mono">{email}</span>.
                </p>
              </div>

              <form onSubmit={handleVerify2FA} className="space-y-5">
                <div>
                  <div className="relative">
                    <input
                      type="text"
                      maxLength={6}
                      autoFocus
                      required
                      value={totpCode}
                      onChange={(e) => setTotpCode(e.target.value.replace(/\D/g, ''))}
                      placeholder="123456"
                      className="w-full text-center text-3xl font-mono tracking-[0.3em] py-3.5 bg-slate-900/90 border border-slate-700 rounded-xl text-white placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all"
                    />
                  </div>
                  <p className="text-center text-[11px] text-slate-500 mt-2 flex items-center justify-center gap-1">
                    <KeyRound className="w-3 h-3" /> Codes change every 30 seconds
                  </p>
                </div>

                <button
                  type="submit"
                  disabled={loading || totpCode.length < 6}
                  className="w-full py-3 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed text-white font-medium text-sm rounded-xl shadow-lg shadow-blue-600/30 transition-all flex items-center justify-center gap-2"
                >
                  {loading ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <>
                      Verify & Enter Workspace
                      <ArrowRight className="w-4 h-4" />
                    </>
                  )}
                </button>
              </form>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
