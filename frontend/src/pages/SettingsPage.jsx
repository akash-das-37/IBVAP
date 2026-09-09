import React, { useState, useEffect } from 'react';
import { Settings as SettingsIcon, Cpu, Database, Shield, Smartphone, Info } from 'lucide-react';
import { api } from '../services/api';

export default function SettingsPage({ liveStats }) {
  const [healthData, setHealthData] = useState(null);

  useEffect(() => {
    api.getHealth().then(setHealthData).catch(console.error);
  }, []);

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
