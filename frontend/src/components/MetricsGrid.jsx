import React from 'react';
import { Camera, User, Car, AlertOctagon, Layers, Gauge } from 'lucide-react';

export default function MetricsGrid({ liveStats, historicalStats }) {
  const isOnline = liveStats?.camera_status === 'ONLINE';

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3 mb-4">
      {/* 1. Camera Status */}
      <div className="bg-[#0d1117] border border-slate-800 rounded p-3 relative overflow-hidden">
        <div className="flex items-center justify-between mb-1">
          <span className="text-[11px] font-mono text-slate-400 uppercase">CAMERA STATUS</span>
          <Camera className={`w-4 h-4 ${isOnline ? 'text-emerald-400' : 'text-rose-400'}`} />
        </div>
        <div className="flex items-baseline space-x-2">
          <span className={`text-xl font-mono font-bold ${isOnline ? 'text-emerald-400' : 'text-rose-400'}`}>
            {isOnline ? 'ONLINE' : 'OFFLINE'}
          </span>
        </div>
        <span className="text-[10px] text-slate-500 font-mono">CAM 01 (PERIMETER)</span>
        <div className={`absolute bottom-0 left-0 right-0 h-0.5 ${isOnline ? 'bg-emerald-500' : 'bg-rose-500'}`} />
      </div>

      {/* 2. Detected Persons */}
      <div className="bg-[#0d1117] border border-slate-800 rounded p-3 relative overflow-hidden">
        <div className="flex items-center justify-between mb-1">
          <span className="text-[11px] font-mono text-slate-400 uppercase">PERSON DETECTED</span>
          <User className="w-4 h-4 text-cyan-400" />
        </div>
        <div className="flex items-baseline space-x-2">
          <span className="text-xl font-mono font-bold text-white">
            {liveStats?.person_count ?? 0}
          </span>
          <span className="text-xs text-cyan-400 font-mono">TRACKED</span>
        </div>
        <span className="text-[10px] text-slate-500 font-mono">YOLOv8 + BYTETRACK</span>
        <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-cyan-500" />
      </div>

      {/* 3. Detected Vehicles */}
      <div className="bg-[#0d1117] border border-slate-800 rounded p-3 relative overflow-hidden">
        <div className="flex items-center justify-between mb-1">
          <span className="text-[11px] font-mono text-slate-400 uppercase">VEHICLES</span>
          <Car className="w-4 h-4 text-amber-400" />
        </div>
        <div className="flex items-baseline space-x-2">
          <span className="text-xl font-mono font-bold text-white">
            {liveStats?.vehicle_count ?? 0}
          </span>
          <span className="text-xs text-amber-400 font-mono">ANPR READY</span>
        </div>
        <span className="text-[10px] text-slate-500 font-mono">CAR / TRUCK / BUS</span>
        <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-amber-500" />
      </div>

      {/* 4. Active Alerts */}
      <div className="bg-[#0d1117] border border-slate-800 rounded p-3 relative overflow-hidden">
        <div className="flex items-center justify-between mb-1">
          <span className="text-[11px] font-mono text-slate-400 uppercase">ACTIVE ALERTS</span>
          <AlertOctagon className="w-4 h-4 text-rose-400" />
        </div>
        <div className="flex items-baseline space-x-2">
          <span className="text-xl font-mono font-bold text-rose-400">
            {historicalStats?.active_alerts ?? 0}
          </span>
          <span className="text-xs text-slate-400 font-mono">UNACKNOWLEDGED</span>
        </div>
        <span className="text-[10px] text-rose-400/80 font-mono">
          {historicalStats?.critical_alerts ?? 0} CRITICAL
        </span>
        <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-rose-500" />
      </div>

      {/* 5. Events Today */}
      <div className="bg-[#0d1117] border border-slate-800 rounded p-3 relative overflow-hidden">
        <div className="flex items-center justify-between mb-1">
          <span className="text-[11px] font-mono text-slate-400 uppercase">EVENTS TODAY</span>
          <Layers className="w-4 h-4 text-indigo-400" />
        </div>
        <div className="flex items-baseline space-x-2">
          <span className="text-xl font-mono font-bold text-white">
            {historicalStats?.events_today ?? 0}
          </span>
          <span className="text-xs text-indigo-400 font-mono">LOGGED</span>
        </div>
        <span className="text-[10px] text-slate-500 font-mono">AUDIT TRAIL</span>
        <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-indigo-500" />
      </div>

      {/* 6. Edge FPS & Latency */}
      <div className="bg-[#0d1117] border border-slate-800 rounded p-3 relative overflow-hidden">
        <div className="flex items-center justify-between mb-1">
          <span className="text-[11px] font-mono text-slate-400 uppercase">EDGE INFERENCE</span>
          <Gauge className="w-4 h-4 text-emerald-400" />
        </div>
        <div className="flex items-baseline space-x-2">
          <span className="text-xl font-mono font-bold text-emerald-400">
            {liveStats?.fps ?? 0}
          </span>
          <span className="text-xs text-slate-400 font-mono">FPS</span>
        </div>
        <span className="text-[10px] text-slate-500 font-mono">REAL-TIME EDGE</span>
        <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-emerald-500" />
      </div>
    </div>
  );
}
