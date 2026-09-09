import React, { useState, useEffect } from 'react';
import { Camera, Smartphone, Video, FileVideo, Plus, CheckCircle2, RefreshCw } from 'lucide-react';
import { api } from '../services/api';

export default function CamerasPage({ liveStats, onSourceChanged }) {
  const [cameras, setCameras] = useState([]);
  const [loading, setLoading] = useState(false);
  const [editingCameraId, setEditingCameraId] = useState(null);
  const [newSourceUrl, setNewSourceUrl] = useState('');

  const fetchCameras = async () => {
    setLoading(true);
    try {
      const data = await api.getCameras();
      setCameras(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCameras();
  }, []);

  const handleUpdateSource = async (camId) => {
    if (!newSourceUrl.trim()) return;
    try {
      await api.switchCameraSource(camId, newSourceUrl);
      setEditingCameraId(null);
      setNewSourceUrl('');
      fetchCameras();
      if (onSourceChanged) onSourceChanged(newSourceUrl);
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="flex-1 p-4 flex flex-col space-y-4 overflow-y-auto">
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <div>
          <h2 className="text-sm font-mono font-bold text-white tracking-wider flex items-center space-x-2">
            <Camera className="w-4 h-4 text-cyan-400" />
            <span>CAMERA MANAGEMENT & INGESTION CONFIGURATION</span>
          </h2>
          <p className="text-xs text-slate-400">
            Configure IP CCTV streams, Smartphone RTSP endpoints, or fallback video sources.
          </p>
        </div>

        <button
          onClick={fetchCameras}
          className="flex items-center space-x-1.5 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-xs font-mono text-cyan-400 rounded border border-slate-700 transition-colors"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>REFRESH STATUS</span>
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {cameras.map((cam) => {
          const isOnline = liveStats?.camera_status === 'ONLINE';
          const isEditing = editingCameraId === cam.camera_id;

          return (
            <div
              key={cam.camera_id}
              className="bg-[#0d1117] border border-slate-800 rounded p-5 relative overflow-hidden space-y-4"
            >
              <div className="flex items-start justify-between">
                <div>
                  <div className="flex items-center space-x-2">
                    <span className="font-mono font-bold text-white text-sm">{cam.camera_id}</span>
                    <span className={`px-2 py-0.2 text-[10px] font-mono font-bold rounded ${
                      isOnline ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40' : 'bg-rose-500/20 text-rose-400 border border-rose-500/40'
                    }`}>
                      {isOnline ? 'ONLINE' : 'OFFLINE'}
                    </span>
                  </div>
                  <h3 className="text-xs text-slate-300 font-semibold mt-0.5">{cam.name}</h3>
                  <span className="text-[11px] text-slate-500 font-mono">{cam.location}</span>
                </div>

                <div className="w-8 h-8 rounded bg-slate-900 border border-slate-800 flex items-center justify-center">
                  <Camera className="w-4 h-4 text-cyan-400" />
                </div>
              </div>

              {/* Source Details */}
              <div className="bg-black/50 border border-slate-800/80 rounded p-3 text-xs font-mono space-y-1.5">
                <div className="text-slate-500 text-[10px]">CURRENT INGESTION STREAM:</div>
                <div className="text-cyan-400 truncate select-all">{cam.source_url}</div>
                <div className="flex items-center space-x-4 text-[10px] text-slate-400 pt-1 border-t border-slate-800">
                  <div>TYPE: <span className="text-white">{cam.type?.toUpperCase()}</span></div>
                  <div>FPS: <span className="text-white">{liveStats?.fps || 0}</span></div>
                  <div>RESOLUTION: <span className="text-white">{cam.resolution || '960x540'}</span></div>
                </div>
              </div>

              {/* Source Switch Form */}
              {isEditing ? (
                <div className="space-y-2 pt-2 border-t border-slate-800">
                  <label className="block text-[11px] font-mono text-slate-400">
                    New Stream URL (RTSP / HTTP / 0 / File path):
                  </label>
                  <input
                    type="text"
                    value={newSourceUrl}
                    onChange={(e) => setNewSourceUrl(e.target.value)}
                    placeholder="rtsp://192.168.x.x:8080/h264_pcm.sdp"
                    className="w-full bg-slate-900 border border-slate-700 rounded px-3 py-1.5 text-xs font-mono text-white focus:outline-none focus:border-cyan-400"
                  />
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => handleUpdateSource(cam.camera_id)}
                      className="px-3 py-1 bg-cyan-500 hover:bg-cyan-400 text-black text-xs font-mono font-bold rounded"
                    >
                      SAVE & CONNECT
                    </button>
                    <button
                      onClick={() => setEditingCameraId(null)}
                      className="px-3 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-mono rounded"
                    >
                      CANCEL
                    </button>
                  </div>
                </div>
              ) : (
                <div className="flex items-center justify-between pt-2 border-t border-slate-800">
                  <button
                    onClick={() => { setEditingCameraId(cam.camera_id); setNewSourceUrl(cam.source_url); }}
                    className="text-xs font-mono text-cyan-400 hover:underline"
                  >
                    CONFIGURE SOURCE URL →
                  </button>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
