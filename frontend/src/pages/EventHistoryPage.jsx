import React, { useState, useEffect } from 'react';
import { History, Search, Download, Eye } from 'lucide-react';
import { api } from '../services/api';

export default function EventHistoryPage() {
  const [events, setEvents] = useState([]);
  const [eventTypeFilter, setEventTypeFilter] = useState('');
  const [selectedSnapshot, setSelectedSnapshot] = useState(null);
  const [loading, setLoading] = useState(false);

  const fetchEvents = async () => {
    setLoading(true);
    try {
      const params = {};
      if (eventTypeFilter) params.event_type = eventTypeFilter;
      const data = await api.getEvents(params);
      setEvents(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEvents();
  }, [eventTypeFilter]);

  const exportCSV = () => {
    if (!events.length) return;
    const headers = ["Event ID", "Timestamp", "Camera", "Type", "Object", "Track ID", "Confidence", "Plate", "Zone"];
    const rows = events.map(e => [
      e.event_id,
      e.timestamp,
      e.camera_id,
      e.event_type,
      e.object_type || '',
      e.track_id || '',
      e.confidence,
      e.plate_number || '',
      e.zone_name || ''
    ]);
    const csvContent = "data:text/csv;charset=utf-8," + [headers.join(","), ...rows.map(r => r.join(","))].join("\n");
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `IBVAP_Audit_Log_${new Date().toISOString().slice(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="flex-1 p-4 flex flex-col space-y-4 overflow-y-auto">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-3">
        <div>
          <h2 className="text-sm font-mono font-bold text-white tracking-wider flex items-center space-x-2">
            <History className="w-4 h-4 text-cyan-400" />
            <span>HISTORICAL SURVEILLANCE AUDIT TRAIL</span>
          </h2>
          <p className="text-xs text-slate-400">
            Immutable log of detected edge events, ANPR plate captures, and zone crossings.
          </p>
        </div>

        <div className="flex items-center space-x-2">
          <select
            value={eventTypeFilter}
            onChange={(e) => setEventTypeFilter(e.target.value)}
            className="bg-slate-900 border border-slate-700 text-xs font-mono text-slate-300 rounded px-2.5 py-1.5 focus:outline-none focus:border-cyan-400"
          >
            <option value="">ALL EVENT TYPES</option>
            <option value="ZONE_INTRUSION">ZONE INTRUSION</option>
            <option value="TRIPWIRE_CROSSING">TRIPWIRE CROSSING</option>
            <option value="LOITERING">LOITERING</option>
            <option value="DIRECTION_VIOLATION">DIRECTION VIOLATION</option>
          </select>

          <button
            onClick={exportCSV}
            className="flex items-center space-x-1.5 px-3 py-1.5 bg-cyan-950/60 hover:bg-cyan-900/60 text-cyan-400 text-xs font-mono rounded border border-cyan-500/40 transition-colors"
          >
            <Download className="w-3.5 h-3.5" />
            <span>EXPORT CSV</span>
          </button>
        </div>
      </div>

      {/* Events Table */}
      <div className="bg-[#0d1117] border border-slate-800 rounded overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-slate-900/90 text-slate-400 border-b border-slate-800">
              <tr>
                <th className="py-2.5 px-3">TIMESTAMP</th>
                <th className="py-2.5 px-3">CAMERA</th>
                <th className="py-2.5 px-3">EVENT</th>
                <th className="py-2.5 px-3">TARGET OBJECT</th>
                <th className="py-2.5 px-3">CONFIDENCE</th>
                <th className="py-2.5 px-3">ZONE</th>
                <th className="py-2.5 px-3">ANPR PLATE</th>
                <th className="py-2.5 px-3 text-right">EVIDENCE</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-slate-300">
              {events.length === 0 ? (
                <tr>
                  <td colSpan="8" className="py-8 text-center text-slate-500">
                    {loading ? 'Loading audit trail...' : 'No historical records found.'}
                  </td>
                </tr>
              ) : (
                events.map((e) => (
                  <tr key={e.event_id} className="hover:bg-slate-900/40 transition-colors">
                    <td className="py-2.5 px-3 text-slate-400 whitespace-nowrap">
                      {e.timestamp ? new Date(e.timestamp).toLocaleString() : ''}
                    </td>
                    <td className="py-2.5 px-3 text-white font-semibold">{e.camera_id}</td>
                    <td className="py-2.5 px-3">
                      <span className="px-1.5 py-0.5 rounded text-[10px] bg-cyan-500/10 text-cyan-400 border border-cyan-500/30">
                        {e.event_type}
                      </span>
                    </td>
                    <td className="py-2.5 px-3">
                      {e.object_type ? `${e.object_type.toUpperCase()} #${e.track_id ?? ''}` : 'N/A'}
                    </td>
                    <td className="py-2.5 px-3 text-slate-400">{e.confidence}</td>
                    <td className="py-2.5 px-3 text-slate-300">{e.zone_name || '—'}</td>
                    <td className="py-2.5 px-3">
                      {e.plate_number ? (
                        <span className="px-1.5 py-0.5 rounded text-[10px] bg-amber-500/10 text-amber-400 border border-amber-500/30 font-bold">
                          {e.plate_number} ({e.plate_confidence})
                        </span>
                      ) : (
                        <span className="text-slate-600">—</span>
                      )}
                    </td>
                    <td className="py-2.5 px-3 text-right">
                      {e.snapshot_path ? (
                        <button
                          onClick={() => setSelectedSnapshot(`http://${window.location.hostname}:8000${e.snapshot_path}`)}
                          className="p-1 hover:bg-slate-800 rounded text-cyan-400"
                          title="View Snapshot"
                        >
                          <Eye className="w-4 h-4 inline" />
                        </button>
                      ) : (
                        <span className="text-slate-600">—</span>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Snapshot Modal */}
      {selectedSnapshot && (
        <div className="fixed inset-0 bg-black/85 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-[#0d1117] border border-cyan-500/40 rounded-lg p-4 max-w-2xl w-full">
            <div className="flex items-center justify-between mb-3 border-b border-slate-800 pb-2">
              <span className="font-mono font-bold text-white text-xs">EVENT SNAPSHOT EVIDENCE</span>
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
