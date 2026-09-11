import React, { useState } from 'react';
import { Shield, Lock, Mail, Key, UserCheck, ArrowRight, AlertTriangle, Eye, EyeOff } from 'lucide-react';
import { supabase } from '../services/supabase';

export default function AuthPage({ onAuthenticated }) {
  const [isSignUp, setIsSignUp] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [infoMessage, setInfoMessage] = useState('');

  const handleAuth = async (e) => {
    e.preventDefault();
    setErrorMessage('');
    setInfoMessage('');
    if (!email || !password) {
      setErrorMessage('Please provide both email address and security passkey.');
      return;
    }

    if (password.length < 6) {
      setErrorMessage('Security passkey must be at least 6 characters.');
      return;
    }

    setLoading(true);
    try {
      if (isSignUp) {
        const { data, error } = await supabase.auth.signUp({
          email,
          password,
        });
        if (error) throw error;
        if (data.session) {
          if (onAuthenticated) onAuthenticated(data.user);
        } else if (data.user) {
          setInfoMessage('Account registered successfully! You can now log in or check your confirmation email.');
          setIsSignUp(false);
        }
      } else {
        const { data, error } = await supabase.auth.signInWithPassword({
          email,
          password,
        });
        if (error) throw error;
        if (onAuthenticated) onAuthenticated(data.user);
      }
    } catch (err) {
      console.error('Authentication error:', err);
      setErrorMessage(err.message || 'Authentication failed. Please verify credentials.');
    } finally {
      setLoading(false);
    }
  };


  return (
    <div className="min-h-screen w-screen bg-[#07090e] flex items-center justify-center p-4 relative overflow-hidden font-sans select-none">
      {/* Background Ambient Tactical Elements */}
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(0,240,255,0.08),transparent_50%)]" />
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_bottom_left,rgba(239,68,68,0.05),transparent_50%)]" />
      <div className="radar-scan-line pointer-events-none opacity-40" />

      <div className="relative z-10 w-full max-w-md bg-[#0d1117]/95 border border-slate-800 rounded-xl shadow-[0_0_50px_rgba(0,0,0,0.8)] backdrop-blur-md p-8 space-y-6">
        {/* Header Badge */}
        <div className="text-center space-y-2">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-cyan-950/60 border border-cyan-500/40 shadow-[0_0_20px_rgba(0,240,255,0.2)] mb-1">
            <Shield className="w-8 h-8 text-cyan-400" />
          </div>
          <div className="flex items-center justify-center space-x-2">
            <h1 className="text-xl font-mono font-bold tracking-widest text-white">IBVAP</h1>
            <span className="px-1.5 py-0.5 text-[10px] font-mono font-bold bg-cyan-950 text-cyan-400 border border-cyan-500/40 rounded">
              DEFENSE EDGE v1.0
            </span>
          </div>
          <p className="text-xs font-mono text-slate-400">
            {isSignUp ? 'REGISTER NEW OPERATOR ACCOUNT' : 'INTELLIGENT BORDER VIDEO ANALYTICS PLATFORM'}
          </p>
        </div>

        {/* Error Banner */}
        {errorMessage && (
          <div className="p-3 bg-rose-950/80 border border-rose-500/50 rounded-lg text-rose-300 text-xs font-mono flex items-start space-x-2">
            <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
            <span>{errorMessage}</span>
          </div>
        )}

        {/* Info Banner */}
        {infoMessage && (
          <div className="p-3 bg-cyan-950/80 border border-cyan-500/50 rounded-lg text-cyan-300 text-xs font-mono flex items-start space-x-2">
            <UserCheck className="w-4 h-4 text-cyan-400 shrink-0 mt-0.5" />
            <span>{infoMessage}</span>
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleAuth} className="space-y-4">
          <div className="space-y-1">
            <label className="block text-[11px] font-mono text-slate-400">
              {isSignUp ? 'REGISTER EMAIL' : 'OPERATOR EMAIL'}
            </label>
            <div className="relative">
              <Mail className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="operator@defense.gov"
                className="w-full bg-slate-950 border border-slate-800 focus:border-cyan-500 rounded-lg pl-9 pr-3 py-2 text-xs font-mono text-white placeholder-slate-600 outline-none transition-colors"
              />
            </div>
          </div>

          <div className="space-y-1">
            <label className="block text-[11px] font-mono text-slate-400">
              {isSignUp ? 'CREATE PASSKEY (MIN 6 CHARACTERS)' : 'SECURITY PASSKEY'}
            </label>
            <div className="relative">
              <Lock className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type={showPassword ? 'text' : 'password'}
                required
                minLength={6}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••••••"
                className="w-full bg-slate-950 border border-slate-800 focus:border-cyan-500 rounded-lg pl-9 pr-10 py-2 text-xs font-mono text-white placeholder-slate-600 outline-none transition-colors"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300"
              >
                {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-2.5 px-4 bg-cyan-500 hover:bg-cyan-400 text-black font-mono font-bold text-xs rounded-lg transition-all shadow-[0_0_20px_rgba(0,240,255,0.3)] flex items-center justify-center space-x-2 disabled:opacity-50 cursor-pointer"
          >
            <span>{loading ? 'PROCESSING...' : isSignUp ? 'CREATE ACCOUNT & REGISTER' : 'AUTHENTICATE & ENTER'}</span>
            {!loading && <ArrowRight className="w-4 h-4" />}
          </button>

          {/* Quick Toggle: Don't have an account? Register / Already have an account? Sign in */}
          <div className="pt-1 text-center">
            {!isSignUp ? (
              <p className="text-xs font-mono text-slate-400">
                Don&apos;t have an account?{' '}
                <button
                  type="button"
                  onClick={() => {
                    setIsSignUp(true);
                    setErrorMessage('');
                    setInfoMessage('');
                  }}
                  className="text-cyan-400 hover:text-cyan-300 font-bold underline underline-offset-4 ml-1 transition-colors cursor-pointer"
                >
                  Register
                </button>
              </p>
            ) : (
              <p className="text-xs font-mono text-slate-400">
                Already have an account?{' '}
                <button
                  type="button"
                  onClick={() => {
                    setIsSignUp(false);
                    setErrorMessage('');
                    setInfoMessage('');
                  }}
                  className="text-cyan-400 hover:text-cyan-300 font-bold underline underline-offset-4 ml-1 transition-colors cursor-pointer"
                >
                  Operator Login
                </button>
              </p>
            )}
          </div>
        </form>


        {/* Footer Security Notice */}
        <p className="text-[10px] font-mono text-slate-500 text-center">
          RESTRICTED GOVERNMENT & DEFENSE SYSTEM • UNAUTHORIZED ACCESS PROHIBITED
        </p>
      </div>
    </div>
  );
}
