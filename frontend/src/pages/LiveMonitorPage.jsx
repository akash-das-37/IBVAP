import React from 'react';
import LiveFeed from '../components/LiveFeed';
import { Shield, Eye, Activity, Cpu } from 'lucide-react';

export default function LiveMonitorPage({ liveStats, currentCamera, zones = [], onSourceChanged }) {
  return (
    <div className="flex-1 p-4 flex flex-col space-y-4 overflow-hidden">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-sm font-mono font-bold text-white tracking-wider flex items-center space-x-2">
            <Eye className="w-4 h-4 text-cyan-400" />
            <span>FULL MONITORING CONSOLE — PERIMETER CAMERA 01</span>
          </h2>
          <p className="text-xs text-slate-400">
            Real-time edge video pipeline with automated ByteTrack tracking and polygon intrusion detection overlays.
          </p>
        </div>

        <div className="flex items-center space-x-3 text-xs font-mono">
          <span className="text-slate-400">RESOLUTION:</span>
          <span className="text-cyan-400 font-bold">960x540 (AUTO-SCALED)</span>
          <span className="text-slate-600">|</span>
          <span className="text-slate-400">ENHANCEMENT:</span>
          <span className="text-emerald-400 font-bold">CLAHE ADAPTIVE</span>
        </div>
      </div>

      <div className="flex-1 min-h-[500px]">
        <LiveFeed
          liveStats={liveStats}
          currentCamera={currentCamera}
          zones={zones}
          onSourceChanged={onSourceChanged}
        />
      </div>
    </div>
  );
}
