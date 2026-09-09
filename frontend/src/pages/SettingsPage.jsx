import React, { useState, useEffect } from 'react';
import { Settings as SettingsIcon, Cpu, Database, Shield, Smartphone, Info, Globe, Save, Check } from 'lucide-react';
import { api, getBackendBase } from '../services/api';

export default function SettingsPage({ liveStats }) {
  const [healthData, setHealthData] = useState(null);
  const [backendUrl, setBackendUrl] = useState(() => localStorage.getItem('ibvap_backend_url') || getBackendBase());
  const [savedSuccess, setSavedSuccess] = useState(false);

  useEffect(() => {
    api.getHealth().then(setHealthData).catch(console.error);
  }, []);

  const handleSaveBackendUrl = (e) => {
    e.preventDefault();
    if (backendUrl.trim()) {
      localStorage.setItem('ibvap_backend_url', backendUrl.trim().replace(/\/+$/, ''));
    } else {
      localStorage.removeItem('ibvap_backend_url');
    }
    setSavedSuccess(true);
    setTimeout(() => {
      setSavedSuccess(false);
      window.location.reload();
    }, 1200);
  };

  return (
    <div className="flex-1 p-4 flex flex-col space-y-4 overflow-y-auto">
      <div className="border-b border-slate-800 pb-3">
        <h2 className="text-sm font-mono font-bold text-white tracking-wider flex items-center space-x-2">
          <SettingsIcon className="w-4 h-4 text-cyan-400" />
          <span>SYSTEM ARCHITECTURE & PLATFORM DIAGNOSTICS</span>
        </h2>
        <p className="text-xs text-slate-400">
          IBVAP runtime environment, edge computer diagnostics, and camera connection guide.
        </p>
      </div>

      {/* Cloud & Edge Network Endpoint Configuration */}
      <div className="bg-[#0d1117] border border-cyan-500/40 rounded p-4 shadow-[0_0_15px_rgba(0,240,255,0.08)]">
        <div className="flex items-center justify-between border-b border-slate-800 pb-2 mb-3">
          <div className="flex items-center space-x-2">
            <Globe className="w-4 h-4 text-cyan-400" />
            <span className="text-xs font-mono font-bold text-white">EDGE BACKEND CONNECTION ENDPOINT</span>
          </div>
          <span className="text-[10px] font-mono text-cyan-400 bg-cyan-950/60 border border-cyan-500/30 px-2 py-0.5 rounded">
            CLOUD & LOCAL ACCESS
          </span>
        </div>
        <p className="text-xs text-slate-400 mb-3">
          Configure the API endpoint of your running IBVAP Edge node. When accessing from Vercel or across Wi-Fi networks, point this to your Edge laptop's local IP (e.g. <code className="text-cyan-300">http://192.168.1.50:8000</code>) or an ngrok / tunnel URL.
        </p>
        <form onSubmit={handleSaveBackendUrl} className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2">
          <input
            type="text"
            value={backendUrl}
            onChange={(e) => setBackendUrl(e.target.value)}
            placeholder="http://localhost:8000"
            className="flex-1 bg-slate-950 border border-slate-700 focus:border-cyan-500 rounded px-3 py-1.5 text-xs font-mono text-white outline-none"
          />
          <button
            type="submit"
            className="flex items-center justify-center space-x-1.5 px-4 py-1.5 bg-cyan-500 hover:bg-cyan-400 text-black text-xs font-mono font-bold rounded transition-colors"
          >
            {savedSuccess ? (
              <>
                <Check className="w-3.5 h-3.5" />
                <span>SAVED & RELOADING...</span>
              </>
            ) : (
              <>
                <Save className="w-3.5 h-3.5" />
                <span>APPLY ENDPOINT</span>
              </>
            )}
          </button>
        </form>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Runtime Diagnostics */}
        <div className="bg-[#0d1117] border border-slate-800 rounded p-4 space-y-4">
          <div className="flex items-center space-x-2 border-b border-slate-800 pb-2">
            <Cpu className="w-4 h-4 text-cyan-400" />
            <span className="text-xs font-mono font-bold text-white">EDGE AI RUNTIME ENVIRONMENT</span>
          </div>

          <div className="space-y-2.5 text-xs font-mono">
            <div className="flex justify-between py-1 border-b border-slate-900">
              <span className="text-slate-400">PLATFORM:</span>
              <span className="text-white font-semibold">{healthData?.platform || 'IBVAP Edge v1.0.0'}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-900">
              <span className="text-slate-400">HARDWARE COMPUTE:</span>
              <span className="text-cyan-400 font-semibold">EDGE MULTI-CORE CPU</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-900">
              <span className="text-slate-400">OBJECT DETECTOR:</span>
              <span className="text-emerald-400 font-semibold">Ultralytics YOLOv8n (CPU-Optimized)</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-900">
              <span className="text-slate-400">OBJECT TRACKER:</span>
              <span className="text-emerald-400 font-semibold">ByteTrack Multi-Object Tracker</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-900">
              <span className="text-slate-400">ANPR RECOGNITION:</span>
              <span className="text-amber-400 font-semibold">EasyOCR (En) + Heuristic Filter</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-900">
              <span className="text-slate-400">CONTRAST ENHANCER:</span>
              <span className="text-cyan-400 font-semibold">CLAHE (L-channel LAB space)</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-900">
              <span className="text-slate-400">CURRENT EDGE FPS:</span>
              <span className="text-emerald-400 font-bold">{liveStats?.fps || 0} FPS</span>
            </div>
          </div>
        </div>

        {/* Central Event Queue & Database */}
        <div className="bg-[#0d1117] border border-slate-800 rounded p-4 space-y-4">
          <div className="flex items-center space-x-2 border-b border-slate-800 pb-2">
            <Database className="w-4 h-4 text-amber-400" />
            <span className="text-xs font-mono font-bold text-white">STORAGE & BUFFER TELEMETRY</span>
          </div>

          <div className="space-y-2.5 text-xs font-mono">
            <div className="flex justify-between py-1 border-b border-slate-900">
              <span className="text-slate-400">EVENT QUEUE DRIVER:</span>
              <span className={`font-semibold ${healthData?.redis_active ? 'text-emerald-400' : 'text-amber-400'}`}>
                {healthData?.queue_mode || 'In-Memory Async Buffer'}
              </span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-900">
              <span className="text-slate-400">REDIS SERVER:</span>
              <span className={`font-semibold ${healthData?.redis_active ? 'text-emerald-400' : 'text-slate-400'}`}>
                {healthData?.redis_active ? 'CONNECTED (localhost:6379)' : 'FALLBACK ACTIVE (Zero-Loss)'}
              </span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-900">
              <span className="text-slate-400">AUDIT DATABASE:</span>
              <span className="text-white font-semibold">SQLite (data/ibvap.db via SQLAlchemy)</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-900">
              <span className="text-slate-400">EVIDENCE SNAPSHOTS:</span>
              <span className="text-white font-semibold">data/snapshots/</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-900">
              <span className="text-slate-400">REAL-TIME PUSH:</span>
              <span className="text-emerald-400 font-semibold">WebSocket Sub-Second Stream (/ws/alerts)</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-900">
              <span className="text-slate-400">CAMERA HEALTH:</span>
              <span className="text-emerald-400 font-bold">{healthData?.camera_status || 'ONLINE'}</span>
            </div>
          </div>
        </div>

        {/* Smartphone Camera Instructions Card */}
        <div className="md:col-span-2 bg-[#0d1117] border border-cyan-500/30 rounded p-4">
          <div className="flex items-center space-x-2 border-b border-slate-800 pb-2 mb-3">
            <Smartphone className="w-4 h-4 text-cyan-400" />
            <span className="text-xs font-mono font-bold text-white">
              SMARTPHONE AS CCTV / IP CAMERA SETUP INSTRUCTIONS
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs font-mono text-slate-300">
            <div className="bg-slate-900/60 p-3 rounded border border-slate-800">
              <div className="text-cyan-400 font-bold mb-1">1. Network Connection</div>
              <p className="text-slate-400 text-[11px] leading-relaxed">
                Connect both your smartphone and this laptop to the same Wi-Fi network, or enable a mobile hotspot on your phone and connect the laptop to it.
              </p>
            </div>

            <div className="bg-slate-900/60 p-3 rounded border border-slate-800">
              <div className="text-cyan-400 font-bold mb-1">2. IP Camera App</div>
              <p className="text-slate-400 text-[11px] leading-relaxed">
                On Android, install <strong>IP Webcam</strong> (by Pavel Khlebovich) and tap <strong>Start server</strong>.
                On iOS, install <strong>Live-Reporter</strong> or <strong>IP Camera Lite</strong>.
              </p>
            </div>

            <div className="bg-slate-900/60 p-3 rounded border border-slate-800">
              <div className="text-cyan-400 font-bold mb-1">3. URL Formats</div>
              <p className="text-slate-400 text-[11px] leading-relaxed">
                RTSP format: <span className="text-white">rtsp://&lt;phone-ip&gt;:8080/h264_pcm.sdp</span><br />
                MJPEG format: <span className="text-white">http://&lt;phone-ip&gt;:8080/video</span><br />
                Enter this in the <strong>Change Source</strong> modal or Cameras tab.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
