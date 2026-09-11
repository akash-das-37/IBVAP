import React, { useState, useEffect } from 'react';
import { Shield, Cpu, Activity, Database, Clock, User, LogOut } from 'lucide-react';

export default function Header({ systemStats, currentUser, currentOrg, onSignOut }) {
  const [timeStr, setTimeStr] = useState('');

  useEffect(() => {
    const update = () => {
      const now = new Date();
      setTimeStr(now.toLocaleTimeString('en-US', { hour12: false }) + ' UTC');
    };
    update();
    const timer = setInterval(update, 1000);
    return () => clearInterval(timer);
  }, []);

  return (
    <header className="h-16 bg-[#0d1117] border-b border-slate-800 flex items-center justify-between px-6 select-none z-30">
      {/* Brand & Platform Identity */}
      <div className="flex items-center space-x-3">
        <div className="w-10 h-10 rounded bg-cyan-950/80 border border-cyan-500/50 flex items-center justify-center shadow-[0_0_12px_rgba(0,240,255,0.25)]">
          <Shield className="w-5 h-5 text-cyan-400" />
        </div>
        <div>
          <div className="flex items-center space-x-2">
            <span className="font-mono font-bold text-lg text-white tracking-widest">IBVAP</span>
            <span className="px-1.5 py-0.5 text-[10px] font-mono uppercase bg-cyan-500/10 text-cyan-400 border border-cyan-500/30 rounded">
              DEFENSE EDGE v1.0
            </span>
          </div>
          <p className="text-[11px] text-slate-400 font-medium tracking-wide">
            Intelligent Border Video Analytics Platform
          </p>
        </div>
      </div>

      {/* Real-time System Telemetry Indicators */}
      <div className="flex items-center space-x-4">
        {/* Edge AI Status */}
        <div className="hidden lg:flex items-center space-x-2 bg-slate-900/80 border border-slate-800 px-3 py-1.5 rounded">
          <Activity className="w-3.5 h-3.5 text-emerald-400 animate-pulse" />
          <span className="text-xs text-slate-400">AI ENGINE:</span>
          <span className="text-xs font-mono font-bold text-emerald-400">YOLOv8n + ByteTrack</span>
        </div>

        {/* Compute Acceleration */}
        <div className="hidden md:flex items-center space-x-2 bg-slate-900/80 border border-slate-800 px-3 py-1.5 rounded">
          <Cpu className="w-3.5 h-3.5 text-cyan-400" />
          <span className="text-xs text-slate-400">COMPUTE:</span>
          <span className="text-xs font-mono font-bold text-cyan-400">EDGE CPU</span>
        </div>

        {/* Event Queue Telemetry */}
        <div className="hidden sm:flex items-center space-x-2 bg-slate-900/80 border border-slate-800 px-3 py-1.5 rounded">
          <Database className="w-3.5 h-3.5 text-amber-400" />
          <span className="text-xs text-slate-400">QUEUE:</span>
          <span className="text-xs font-mono font-bold text-amber-400">
            {systemStats?.queue_mode || 'BUFFER ACTIVE'}
          </span>
        </div>

        {/* Clock */}
        <div className="hidden xl:flex items-center space-x-2 text-slate-400 border-l border-slate-800 pl-4">
          <Clock className="w-3.5 h-3.5 text-slate-500" />
          <span className="font-mono text-xs text-slate-300 font-medium">{timeStr}</span>
        </div>

        {/* Operator Profile, Tenant Org Badge & Logout */}
        {currentUser && (
          <div className="flex items-center space-x-2 border-l border-slate-800 pl-3">
            {currentOrg && (
              <div className="hidden sm:flex items-center space-x-1.5 bg-emerald-950/50 border border-emerald-500/40 px-2.5 py-1 rounded text-xs font-mono text-emerald-300" title={`surveillance tenant: ${currentOrg.name} (${currentOrg.id})`}>
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping"></span>
                <span className="font-semibold uppercase tracking-wide">{currentOrg.name || 'TENANT ISOLATED'}</span>
              </div>
            )}
            <div className="flex items-center space-x-1.5 bg-slate-900/90 border border-cyan-500/30 px-2.5 py-1 rounded text-xs font-mono">
              <User className="w-3.5 h-3.5 text-cyan-400" />
              <span className="text-slate-300 max-w-[120px] truncate" title={currentUser.email}>
                {currentUser.email?.split('@')[0] || 'Operator'}
              </span>
            </div>
            {onSignOut && (
              <button
                onClick={onSignOut}
                title="Sign Out"
                className="p-1.5 bg-slate-900 hover:bg-rose-950/60 text-slate-400 hover:text-rose-400 border border-slate-800 hover:border-rose-500/40 rounded transition-colors"
              >
                <LogOut className="w-3.5 h-3.5" />
              </button>
            )}
          </div>
        )}
      </div>
    </header>
  );
}
