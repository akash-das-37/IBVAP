import React from 'react';
import { History, Shield, User, Car, AlertTriangle } from 'lucide-react';

export default function RecentEventsTimeline({ events = [] }) {
  const getEventIcon = (type, objType) => {
    if (type.includes('INTRUSION') || type.includes('TRIPWIRE') || type.includes('LOITERING')) {
      return <AlertTriangle className="w-3.5 h-3.5 text-rose-400 shrink-0" />;
    }
    if (objType === 'person') {
      return <User className="w-3.5 h-3.5 text-cyan-400 shrink-0" />;
    }
    if (['car', 'bus', 'truck', 'motorcycle'].includes(objType)) {
      return <Car className="w-3.5 h-3.5 text-amber-400 shrink-0" />;
    }
    return <Shield className="w-3.5 h-3.5 text-slate-400 shrink-0" />;
  };

  return (
    <div className="bg-[#0d1117] border border-slate-800 rounded flex flex-col h-full overflow-hidden">
      <div className="h-10 bg-slate-900/90 border-b border-slate-800 px-4 flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <History className="w-4 h-4 text-cyan-400" />
          <span className="text-xs font-mono font-bold text-white tracking-wider">RECENT EVENTS</span>
        </div>
        <span className="text-[10px] font-mono text-slate-500">LIVE FEED</span>
      </div>

      <div className="flex-1 overflow-y-auto p-3 space-y-2">
        {events.length === 0 ? (
          <div className="h-32 flex items-center justify-center text-xs font-mono text-slate-500">
            Awaiting events...
          </div>
        ) : (
          events.slice(0, 15).map((e) => {
            const timeFormatted = e.timestamp ? new Date(e.timestamp).toLocaleTimeString() : '';
            return (
              <div
                key={e.event_id}
                className="flex items-start space-x-2.5 p-2 rounded bg-slate-900/40 border border-slate-800/80 text-xs"
              >
                <div className="mt-0.5">
                  {getEventIcon(e.event_type, e.object_type)}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-baseline justify-between">
                    <span className="font-mono text-slate-300 text-[11px] font-medium truncate">
                      {e.event_type.replace('_', ' ')}
                      {e.object_type ? ` — ${e.object_type.toUpperCase()}` : ''}
                    </span>
                    <span className="text-[10px] font-mono text-slate-500 shrink-0 ml-2">
                      {timeFormatted}
                    </span>
                  </div>

                  <div className="text-[10px] font-mono text-slate-500 mt-0.5 flex items-center space-x-2">
                    {e.zone_name && <span>Zone: {e.zone_name}</span>}
                    {e.plate_number && (
                      <span className="px-1 bg-amber-500/10 text-amber-400 border border-amber-500/30 rounded">
                        Plate: {e.plate_number} ({e.plate_confidence})
                      </span>
                    )}
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
