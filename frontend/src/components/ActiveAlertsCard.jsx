import React, { useState } from 'react';
import { AlertOctagon, CheckCircle2, Eye, ShieldAlert } from 'lucide-react';
import { api, getBackendBase } from '../services/api';

export default function ActiveAlertsCard({ alerts = [], onAlertUpdated }) {
  const [selectedSnapshot, setSelectedSnapshot] = useState(null);

  const getSeverityStyle = (sev) => {
    switch (sev) {
      case 'CRITICAL':
        return 'border-rose-500/50 bg-rose-950/30 text-rose-400';
      case 'HIGH':
        return 'border-orange-500/50 bg-orange-950/30 text-orange-400';
      case 'MEDIUM':
        return 'border-amber-500/50 bg-amber-950/30 text-amber-400';
      default:
        return 'border-slate-700 bg-slate-900 text-slate-300';
    }
  };

  const handleAcknowledge = async (alertId) => {
    try {
      await api.acknowledgeAlert(alertId);
      if (onAlertUpdated) onAlertUpdated();
    } catch (e) {
      console.error('Failed to acknowledge alert:', e);
    }
  };

  return (
    <div className="bg-[#0d1117] border border-slate-800 rounded flex flex-col h-full overflow-hidden">
      <div className="h-10 bg-slate-900/90 border-b border-slate-800 px-4 flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <ShieldAlert className="w-4 h-4 text-rose-400 animate-pulse" />
          <span className="text-xs font-mono font-bold text-white tracking-wider">ACTIVE ALERTS</span>
          <span className="px-1.5 py-0.2 text-[10px] font-mono bg-rose-500/20 text-rose-400 rounded-full border border-rose-500/40">
            {alerts.length}
          </span>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-3 space-y-2.5">
        {alerts.length === 0 ? (
          <div className="h-44 flex flex-col items-center justify-center text-slate-500">
            <CheckCircle2 className="w-8 h-8 text-emerald-500/40 mb-2" />
            <span className="text-xs font-mono">ALL PERIMETERS SECURE</span>
            <span className="text-[11px] text-slate-600">No active rule violations detected</span>
          </div>
        ) : (
          alerts.map((al) => {
            const timeFormatted = al.timestamp ? new Date(al.timestamp).toLocaleTimeString() : '';
            return (
              <div
                key={al.alert_id}
                className={`border rounded p-3 relative transition-all ${getSeverityStyle(al.severity)}`}
              >
                <div className="flex items-start justify-between">
                  <div>
                    <div className="flex items-center space-x-2 mb-1">
                      <span className="font-mono font-bold text-xs tracking-wider">
                        🚨 {al.event_type.replace('_', ' ')}
                      </span>
                      <span className="px-1.5 py-0.2 text-[9px] font-mono font-bold rounded uppercase bg-black/40">
                        {al.severity}
                      </span>
                    </div>

                    <div className="text-[11px] text-slate-300 font-mono space-y-0.5">
                      <div><span className="text-slate-500">CAMERA:</span> {al.camera_id}</div>
                      <div><span className="text-slate-500">ZONE:</span> {al.zone_name || 'Perimeter'}</div>
                      <div><span className="text-slate-500">TARGET:</span> {al.object_type?.toUpperCase()} {al.track_id ? `#${al.track_id}` : ''} (Conf: {al.confidence})</div>
                      <div className="text-slate-400 text-[10px] mt-1">{al.description}</div>
                    </div>
                  </div>

                  {/* Snapshot Thumbnail if present */}
                  {al.snapshot_path && (
                    <div className="ml-3 shrink-0">
                      <button
                        onClick={() => setSelectedSnapshot(`${getBackendBase()}${al.snapshot_path}`)}
                        className="relative group block w-16 h-12 rounded border border-slate-700 overflow-hidden bg-black"
                      >
                        <img
                          src={`${getBackendBase()}${al.snapshot_path}`}
                          alt="Violation Snapshot"
                          className="w-full h-full object-cover group-hover:scale-105 transition-transform"
                        />
                        <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 flex items-center justify-center transition-opacity">
                          <Eye className="w-3.5 h-3.5 text-cyan-400" />
                        </div>
                      </button>
                    </div>
                  )}
                </div>

                <div className="mt-2.5 pt-2 border-t border-slate-800/60 flex items-center justify-between text-[10px] font-mono">
                  <span className="text-slate-500">{timeFormatted}</span>
                  <button
                    onClick={() => handleAcknowledge(al.alert_id)}
                    className="px-2 py-0.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded border border-slate-700 hover:text-white transition-colors"
                  >
                    ACKNOWLEDGE
                  </button>
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Snapshot Modal */}
      {selectedSnapshot && (
        <div className="fixed inset-0 bg-black/85 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-[#0d1117] border border-cyan-500/40 rounded-lg p-4 max-w-2xl w-full">
            <div className="flex items-center justify-between mb-3 border-b border-slate-800 pb-2">
              <span className="font-mono font-bold text-white text-xs">VIOLATION SNAPSHOT EVIDENCE</span>
              <button
                onClick={() => setSelectedSnapshot(null)}
                className="text-slate-400 hover:text-white font-mono text-sm"
              >
                ✕
              </button>
            </div>
            <div className="bg-black rounded overflow-hidden flex items-center justify-center max-h-[70vh]">
              <img src={selectedSnapshot} alt="Snapshot detail" className="max-w-full max-h-[70vh] object-contain" />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
