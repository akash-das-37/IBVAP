import React, { useState, useEffect } from 'react';
import { Shield, Cpu, Activity, Database, Clock } from 'lucide-react';

export default function Header({ systemStats }) {
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
      <div className="flex items-center space-x-5">
        {/* Edge AI Status */}
        <div className="flex items-center space-x-2 bg-slate-900/80 border border-slate-800 px-3 py-1.5 rounded">
          <Activity className="w-3.5 h-3.5 text-emerald-400 animate-pulse" />
          <span className="text-xs text-slate-400">AI ENGINE:</span>
          <span className="text-xs font-mono font-bold text-emerald-400">YOLOv8n + ByteTrack</span>
        </div>

        {/* Compute Acceleration */}
        <div className="flex items-center space-x-2 bg-slate-900/80 border border-slate-800 px-3 py-1.5 rounded">
          <Cpu className="w-3.5 h-3.5 text-cyan-400" />
          <span className="text-xs text-slate-400">COMPUTE:</span>
          <span className="text-xs font-mono font-bold text-cyan-400">EDGE CPU</span>
        </div>

        {/* Event Queue Telemetry */}
        <div className="flex items-center space-x-2 bg-slate-900/80 border border-slate-800 px-3 py-1.5 rounded">
          <Database className="w-3.5 h-3.5 text-amber-400" />
          <span className="text-xs text-slate-400">QUEUE:</span>
          <span className="text-xs font-mono font-bold text-amber-400">
            {systemStats?.queue_mode || 'BUFFER ACTIVE'}
          </span>
        </div>

        {/* Clock */}
        <div className="flex items-center space-x-2 text-slate-400 border-l border-slate-800 pl-4">
          <Clock className="w-3.5 h-3.5 text-slate-500" />
          <span className="font-mono text-xs text-slate-300 font-medium">{timeStr}</span>
        </div>
      </div>
    </header>
  );
}
