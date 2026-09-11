import React, { useState, useEffect } from 'react';
import { Camera, Smartphone, Video, FileVideo, Plus, CheckCircle2, RefreshCw, Globe, Server, Check } from 'lucide-react';
import { api, getBackendBase } from '../services/api';

const DEFAULT_CAMERAS = [
  {
    camera_id: 'CAM-01',
    name: 'Main Perimeter Camera',
    location: 'North Border Sector Alpha',
    type: 'webcam',
    source_url: '0',
    resolution: '640x480',
    fps: 30,
    status: 'ONLINE'
  },
  {
    camera_id: 'CAM-02',
    name: 'South Checkpoint Sector',
    location: 'Gate 4 Vehicle Ingestion',
    type: 'file',
    source_url: 'data/demo_videos/sample_border.mp4',
    resolution: '1920x1080',
    fps: 25,
    status: 'STANDBY'
  }
];

export default function CamerasPage({ liveStats, onSourceChanged }) {
  const [cameras, setCameras] = useState(DEFAULT_CAMERAS);
  const [loading, setLoading] = useState(false);
  const [editingCameraId, setEditingCameraId] = useState(null);
  const [newSourceUrl, setNewSourceUrl] = useState('');
  const [isBackendReachable, setIsBackendReachable] = useState(true);

  const fetchCameras = async () => {
    setLoading(true);
    try {
      const data = await api.getCameras();
      if (Array.isArray(data) && data.length > 0) {
        setCameras(data);
        setIsBackendReachable(true);
      } else {
        setCameras(DEFAULT_CAMERAS);
        setIsBackendReachable(false);
      }
    } catch (e) {
      console.warn('Failed to fetch cameras from edge backend:', e);
      setCameras(DEFAULT_CAMERAS);
      setIsBackendReachable(false);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCameras();
  }, []);

  const handleUpdateSource = async (camId, overrideUrl) => {
    const targetUrl = overrideUrl !== undefined ? overrideUrl : newSourceUrl;
    if (typeof targetUrl !== 'string' && typeof targetUrl !== 'number') return;
    const strUrl = String(targetUrl).trim();
    if (!strUrl) return;

    setLoading(true);
    try {
      await api.switchCameraSource(camId, strUrl);
      setEditingCameraId(null);
      setNewSourceUrl('');
      await fetchCameras();
      if (onSourceChanged) onSourceChanged(strUrl);
    } catch (e) {
      console.error('Failed to update camera source:', e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex-1 p-4 flex flex-col space-y-4 overflow-y-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-3">
        <div>
          <h2 className="text-sm font-mono font-bold text-white tracking-wider flex items-center space-x-2">
            <Camera className="w-4 h-4 text-cyan-400" />
            <span>CAMERA MANAGEMENT & INGESTION CONFIGURATION</span>
          </h2>
          <p className="text-xs text-slate-400">
            Configure IP CCTV streams, Smartphone RTSP endpoints, or fallback video sources.
          </p>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={fetchCameras}
            disabled={loading}
            className="flex items-center space-x-1.5 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-xs font-mono text-cyan-400 rounded border border-slate-700 transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>{loading ? 'REFRESHING...' : 'REFRESH STATUS'}</span>
          </button>
        </div>
      </div>

      {/* Cloud / Remote Device Notice Banner */}
      {!isBackendReachable && (
        <div className="p-3 bg-amber-950/40 border border-amber-500/40 rounded flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs font-mono text-amber-300">
          <div className="flex items-center space-x-2">
            <Globe className="w-4 h-4 text-amber-400 shrink-0" />
            <span>
              Viewing on Cloud / Remote Device. Showing registered camera profiles. To link this device to your live Edge laptop, configure the Edge URL in Settings.
            </span>
          </div>
          <span className="text-[10px] bg-amber-900/60 border border-amber-500/30 px-2 py-0.5 rounded shrink-0">
            PREVIEW MODE
          </span>
        </div>
      )}

      {/* Cameras Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {cameras.map((cam) => {
          const isOnline = cam.status === 'ONLINE' || liveStats?.camera_status === 'ONLINE';
          const isEditing = editingCameraId === cam.camera_id;

          return (
            <div
              key={cam.camera_id}
              className="bg-[#0d1117] border border-slate-800 rounded p-5 relative overflow-hidden space-y-4 shadow-[0_0_15px_rgba(0,0,0,0.4)]"
            >
              <div className="flex items-start justify-between">
                <div>
                  <div className="flex items-center space-x-2">
                    <span className="font-mono font-bold text-white text-sm">{cam.camera_id}</span>
                    <span className={`px-2 py-0.5 text-[10px] font-mono font-bold rounded ${
                      isOnline ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40' : 'bg-rose-500/20 text-rose-400 border border-rose-500/40'
                    }`}>
                      {isOnline ? 'ONLINE' : 'STANDBY'}
                    </span>
                  </div>
                  <h3 className="text-xs text-slate-300 font-semibold mt-1">{cam.name}</h3>
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
                  <div>FPS: <span className="text-white">{liveStats?.fps || cam.fps || 30}</span></div>
                  <div>RESOLUTION: <span className="text-white">{cam.resolution || '1920x1080'}</span></div>
                </div>
              </div>

              {/* Quick Presets */}
              <div className="space-y-1">
                <span className="text-[10px] font-mono text-slate-500">QUICK SOURCE PRESETS:</span>
                <div className="flex flex-wrap gap-1.5">
                  <button
                    onClick={() => {
                      setEditingCameraId(cam.camera_id);
                      setNewSourceUrl('http://192.168.1.100:8080/video');
                    }}
                    className="flex items-center space-x-1 px-2.5 py-1 bg-slate-900 hover:bg-slate-800 text-slate-300 text-[11px] font-mono rounded border border-slate-800 transition-colors"
                  >
                    <Smartphone className="w-3 h-3 text-cyan-400" />
                    <span>IP Webcam</span>
                  </button>
                  <button
                    onClick={() => handleUpdateSource(cam.camera_id, '0')}
                    className="flex items-center space-x-1 px-2.5 py-1 bg-slate-900 hover:bg-emerald-950/50 text-slate-300 hover:text-emerald-400 text-[11px] font-mono rounded border border-slate-800 hover:border-emerald-500/40 transition-colors"
                    title="Switch immediately to built-in webcam"
                  >
                    <Video className="w-3 h-3 text-emerald-400" />
                    <span>Webcam (0)</span>
                  </button>
                  <button
                    onClick={() => handleUpdateSource(cam.camera_id, 'data/demo_videos/sample_border.mp4')}
                    className="flex items-center space-x-1 px-2.5 py-1 bg-slate-900 hover:bg-amber-950/50 text-slate-300 hover:text-amber-400 text-[11px] font-mono rounded border border-slate-800 hover:border-amber-500/40 transition-colors"
                    title="Switch immediately to demo loop video"
                  >
                    <FileVideo className="w-3 h-3 text-amber-400" />
                    <span>Demo Loop</span>
                  </button>
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
