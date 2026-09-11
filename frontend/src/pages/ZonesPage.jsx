import React, { useState, useEffect, useRef } from 'react';
import { MapPin, Plus, Trash2, Save, RotateCcw, Crosshair, Check, Eye, AlertTriangle } from 'lucide-react';
import { api, getBackendBase } from '../services/api';

export default function ZonesPage() {
  const [zones, setZones] = useState([]);
  const [selectedZone, setSelectedZone] = useState(null);
  const [loading, setLoading] = useState(false);
  const [statusMessage, setStatusMessage] = useState('');
  const [saveSuccessBanner, setSaveSuccessBanner] = useState(null);
  const [isDrawingMode, setIsDrawingMode] = useState(false);
  const [drawnPoints, setDrawnPoints] = useState([]);
  const [snapshotTimestamp, setSnapshotTimestamp] = useState(Date.now());

  const canvasRef = useRef(null);
  const imageRef = useRef(null);

  const toCanvasPoints = (pts) => {
    if (!pts || !Array.isArray(pts)) return [];
    return pts.map(pt => {
      let x = 0, y = 0;
      if (typeof pt === 'object' && pt !== null && !Array.isArray(pt)) {
        x = Number(pt.x) || 0;
        y = Number(pt.y) || 0;
      } else if (Array.isArray(pt) && pt.length >= 2) {
        x = Number(pt[0]) || 0;
        y = Number(pt[1]) || 0;
      }
      if (x <= 1.0 && y <= 1.0 && (x > 0 || y > 0)) {
        return [Math.round(x * 960), Math.round(y * 540)];
      }
      return [Math.round(x), Math.round(y)];
    });
  };

  const toNormalizedPoints = (canvasPts) => {
    if (!canvasPts || !Array.isArray(canvasPts)) return [];
    return canvasPts.map(pt => {
      const x = Number(pt[0]) || 0;
      const y = Number(pt[1]) || 0;
      return {
        x: Number((x / 960).toFixed(4)),
        y: Number((y / 540).toFixed(4))
      };
    });
  };

  const fetchZones = async () => {
    setLoading(true);
    try {
      const data = await api.getZones();
      setZones(data);
      if (data.length > 0) {
        const currentId = selectedZone?.zone_id;
        const toSelect = currentId ? (data.find(z => z.zone_id === currentId) || data[0]) : data[0];
        setSelectedZone(toSelect);
        const rawPts = toSelect.zone_type === 'polygon'
          ? (toSelect.polygon_data || toSelect.polygon_coords || [])
          : (toSelect.line_coords || []);
        setDrawnPoints(toCanvasPoints(rawPts));
      } else {
        setSelectedZone(null);
        setDrawnPoints([]);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchZones();
  }, []);

  const prevZoneId = useRef(null);
  useEffect(() => {
    if (selectedZone && selectedZone.zone_id !== prevZoneId.current) {
      prevZoneId.current = selectedZone.zone_id;
      const rawPts = selectedZone.zone_type === 'polygon'
        ? (selectedZone.polygon_data || selectedZone.polygon_coords || [])
        : (selectedZone.line_coords || []);
      setDrawnPoints(toCanvasPoints(rawPts));
    }
  }, [selectedZone?.zone_id]);

  // Redraw canvas whenever points or zone type changes
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    if (drawnPoints.length === 0) return;

    ctx.lineWidth = 3;
    ctx.strokeStyle = selectedZone?.color || '#ef4444';
    ctx.fillStyle = `${selectedZone?.color || '#ef4444'}33`; // 20% opacity fill

    if (selectedZone?.zone_type === 'tripwire') {
      // Draw line
      if (drawnPoints.length >= 1) {
        ctx.beginPath();
        ctx.arc(drawnPoints[0][0], drawnPoints[0][1], 6, 0, Math.PI * 2);
        ctx.fillStyle = '#00f0ff';
        ctx.fill();
      }
      if (drawnPoints.length >= 2) {
        ctx.beginPath();
        ctx.moveTo(drawnPoints[0][0], drawnPoints[0][1]);
        ctx.lineTo(drawnPoints[1][0], drawnPoints[1][1]);
        ctx.stroke();

        ctx.beginPath();
        ctx.arc(drawnPoints[1][0], drawnPoints[1][1], 6, 0, Math.PI * 2);
        ctx.fillStyle = '#00f0ff';
        ctx.fill();
      }
    } else {
      // Draw Polygon
      ctx.beginPath();
      ctx.moveTo(drawnPoints[0][0], drawnPoints[0][1]);
      for (let i = 1; i < drawnPoints.length; i++) {
        ctx.lineTo(drawnPoints[i][0], drawnPoints[i][1]);
      }
      if (drawnPoints.length >= 3) {
        ctx.closePath();
        ctx.fill();
      }
      ctx.stroke();

      // Draw point markers
      drawnPoints.forEach(([x, y], idx) => {
        ctx.beginPath();
        ctx.arc(x, y, 5, 0, Math.PI * 2);
        ctx.fillStyle = idx === 0 ? '#10b981' : '#00f0ff';
        ctx.fill();
        ctx.strokeStyle = '#000';
        ctx.lineWidth = 1.5;
        ctx.stroke();
      });
    }
  }, [drawnPoints, selectedZone]);

  const handleCanvasClick = (e) => {
    if (!isDrawingMode) return;
    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;

    const clickX = Math.round((e.clientX - rect.left) * scaleX);
    const clickY = Math.round((e.clientY - rect.top) * scaleY);

    if (selectedZone?.zone_type === 'tripwire') {
      if (drawnPoints.length >= 2) {
        setDrawnPoints([[clickX, clickY]]);
      } else {
        setDrawnPoints([...drawnPoints, [clickX, clickY]]);
      }
    } else {
      setDrawnPoints([...drawnPoints, [clickX, clickY]]);
    }
  };

  const handleApplyPreset = (presetType) => {
    const w = 960;
    const h = 540;
    let newPoints = [];

    switch (presetType) {
      case 'left_half':
        newPoints = [[50, 80], [450, 80], [450, 480], [50, 480]];
        break;
      case 'right_half':
        newPoints = [[500, 80], [910, 80], [910, 480], [500, 480]];
        break;
      case 'center_box':
        newPoints = [[250, 120], [710, 120], [710, 440], [250, 440]];
        break;
      case 'tripwire_horizontal':
        newPoints = [[50, 300], [910, 300]];
        if (selectedZone) {
          setSelectedZone({ ...selectedZone, zone_type: 'tripwire' });
        }
        break;
      default:
        break;
    }

    setDrawnPoints(newPoints);
  };

  const handleSaveZone = async (e) => {
    if (e) e.preventDefault();
    if (!selectedZone) return;

    const normPoints = toNormalizedPoints(drawnPoints);
    const updatedZone = {
      ...selectedZone,
      polygon_data: selectedZone.zone_type === 'polygon' ? normPoints : [],
      polygon_coords: selectedZone.zone_type === 'polygon' ? normPoints.map(p => [p.x, p.y]) : [],
      line_coords: selectedZone.zone_type === 'tripwire' ? normPoints.map(p => [p.x, p.y]) : []
    };

    setLoading(true);
    setStatusMessage('');
    setSaveSuccessBanner(null);
    try {
      await api.saveZone(updatedZone);
      setSaveSuccessBanner({
        name: selectedZone.name || 'Border Sector 1',
        camera: 'CAM-01'
      });
      setIsDrawingMode(false);
      setTimeout(() => setSaveSuccessBanner(null), 8000);
      await fetchZones();
    } catch (err) {
      console.error('Failed to save zone:', err);
      setStatusMessage(`Failed to save zone: ${err.message || 'Database error'}`);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteZone = async (zoneId) => {
    if (!zoneId) return;
    setLoading(true);
    setZones((prev) => prev.filter((z) => z.zone_id !== zoneId));
    if (selectedZone?.zone_id === zoneId) {
      setSelectedZone(null);
      setDrawnPoints([]);
    }
    try {
      await api.deleteZone(zoneId);
      setStatusMessage('Zone deleted successfully.');
      setTimeout(() => setStatusMessage(''), 3000);
      await fetchZones();
    } catch (e) {
      console.error(e);
      setStatusMessage('Error deleting zone.');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateNew = () => {
    const newId = `ZONE-${Date.now().toString().slice(-4)}`;
    const newZ = {
      zone_id: newId,
      camera_id: 'CAM-01',
      name: `Custom Border Sector ${zones.length + 1}`,
      zone_type: 'polygon',
      polygon_data: [
        { x: 0.26, y: 0.22 },
        { x: 0.74, y: 0.22 },
        { x: 0.74, y: 0.81 },
        { x: 0.26, y: 0.81 }
      ],
      polygon_coords: [[250, 120], [710, 120], [710, 440], [250, 440]],
      line_coords: [],
      is_restricted: true,
      dwell_threshold: 10.0,
      prohibited_directions: [],
      color: '#ef4444',
      enabled: true
    };
    setZones((prev) => [...prev, newZ]);
    setSelectedZone(newZ);
    setDrawnPoints([[250, 120], [710, 120], [710, 440], [250, 440]]);
    setIsDrawingMode(true);
  };

  return (
    <div className="flex-1 p-4 flex flex-col space-y-4 overflow-y-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-3">
        <div>
          <h2 className="text-sm font-mono font-bold text-white tracking-wider flex items-center space-x-2">
            <MapPin className="w-4 h-4 text-cyan-400" />
            <span>INTERACTIVE BORDER ZONE & VIRTUAL FENCE EDITOR</span>
          </h2>
          <p className="text-xs text-slate-400">
            Click directly on your camera view to define exact restricted boundary zones.
          </p>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={handleCreateNew}
            className="flex items-center space-x-1.5 px-3 py-1.5 bg-cyan-500 hover:bg-cyan-400 text-black text-xs font-mono font-bold rounded transition-colors"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>CREATE NEW ZONE</span>
          </button>
        </div>
      </div>

      {/* Required UI Banner: ZONE CREATED SUCCESSFULLY */}
      {saveSuccessBanner && (
        <div className="p-3 bg-emerald-950/90 border border-emerald-500/80 rounded font-mono text-xs text-emerald-300 shadow-[0_0_15px_rgba(16,185,129,0.3)] space-y-1 animate-fadeIn">
          <div className="flex items-center space-x-2 text-emerald-400 font-bold tracking-wider text-sm">
            <Check className="w-4 h-4" />
            <span>ZONE CREATED SUCCESSFULLY</span>
          </div>
          <div className="pl-6 space-y-0.5 text-slate-200">
            <div><span className="text-slate-400">Zone: </span><span className="font-bold text-white">{saveSuccessBanner.name}</span></div>
            <div><span className="text-slate-400">Camera: </span><span className="font-bold text-cyan-400">{saveSuccessBanner.camera}</span></div>
          </div>
        </div>
      )}

      {statusMessage && (
        <div
          className={`p-2.5 text-xs font-mono rounded flex items-center space-x-2 ${
            statusMessage.toLowerCase().includes('failed') || statusMessage.toLowerCase().includes('error')
              ? 'bg-rose-950/80 border border-rose-500/50 text-rose-300 shadow-[0_0_12px_rgba(244,63,94,0.2)]'
              : 'bg-emerald-950/80 border border-emerald-500/50 text-emerald-300 shadow-[0_0_12px_rgba(16,185,129,0.2)]'
          }`}
        >
          {statusMessage.toLowerCase().includes('failed') || statusMessage.toLowerCase().includes('error') ? (
            <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0" />
          ) : (
            <Check className="w-4 h-4 text-emerald-400 shrink-0" />
          )}
          <span>{statusMessage}</span>
        </div>
      )}

      {/* Main Interactive Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        {/* Left Column: Visual Camera View with Canvas Drawer (8 cols) */}
        <div className="lg:col-span-8 bg-[#0d1117] border border-slate-800 rounded flex flex-col overflow-hidden">
          {/* Canvas Toolbar */}
          <div className="h-10 bg-slate-900/90 border-b border-slate-800 px-4 flex items-center justify-between z-10">
            <div className="flex items-center space-x-2 text-xs font-mono">
              <span className="text-slate-400">TARGET:</span>
              <span className="text-white font-bold">{selectedZone?.name || 'No Zone Selected'}</span>
              <span className="text-slate-600">|</span>
              <span className="text-cyan-400">POINTS: {drawnPoints.length}</span>
            </div>

            <div className="flex items-center space-x-2">
              <button
                onClick={() => setIsDrawingMode(!isDrawingMode)}
                className={`flex items-center space-x-1.5 px-2.5 py-1 text-xs font-mono rounded border transition-colors ${
                  isDrawingMode
                    ? 'bg-rose-500 text-white border-rose-400 animate-pulse'
                    : 'bg-slate-800 text-cyan-400 border-slate-700 hover:bg-slate-700'
                }`}
              >
                <Crosshair className="w-3.5 h-3.5" />
                <span>{isDrawingMode ? 'CLICK ON VIDEO TO DRAW' : 'START DRAWING'}</span>
              </button>

              <button
                onClick={() => setDrawnPoints(drawnPoints.slice(0, -1))}
                disabled={drawnPoints.length === 0}
                className="p-1 px-2 text-xs font-mono bg-slate-800 hover:bg-slate-700 text-slate-300 rounded border border-slate-700 disabled:opacity-40"
                title="Undo last point"
              >
                UNDO
              </button>

              <button
                onClick={() => setDrawnPoints([])}
                className="p-1 px-2 text-xs font-mono bg-slate-800 hover:bg-slate-700 text-slate-300 rounded border border-slate-700"
                title="Clear all points"
              >
                CLEAR
              </button>

              <button
                onClick={() => setSnapshotTimestamp(Date.now())}
                className="p-1 px-2 text-xs font-mono bg-slate-800 hover:bg-slate-700 text-slate-300 rounded border border-slate-700"
                title="Refresh camera snapshot background"
              >
                REFRESH FEED
              </button>
            </div>
          </div>

          {/* Canvas Container with Camera Background */}
          <div className="relative w-full aspect-video bg-black flex items-center justify-center overflow-hidden select-none">
            {/* Live Camera Snapshot Image */}
            <img
              ref={imageRef}
              src={`${getBackendBase()}/api/v1/stream/snapshot/raw?t=${snapshotTimestamp}`}
              alt="Camera Zone View"
              className="absolute inset-0 w-full h-full object-fill pointer-events-none"
              onError={(e) => {
                e.target.style.display = 'none';
              }}
            />

            {/* Interactive Drawing Canvas */}
            <canvas
              ref={canvasRef}
              width={960}
              height={540}
              onClick={handleCanvasClick}
              className={`relative z-10 w-full h-full object-fill ${
                isDrawingMode ? 'cursor-crosshair' : 'cursor-default'
              }`}
            />

            {/* Hint Overlay when in drawing mode */}
            {isDrawingMode && (
              <div className="absolute bottom-3 left-3 z-20 bg-black/80 backdrop-blur-sm border border-cyan-500/40 px-3 py-1.5 rounded text-[11px] font-mono text-cyan-300">
                • Click points on screen to place boundary vertices.<br />
                • For polygons, click 3 or 4 points enclosing the area.<br />
                • Click <strong>SAVE ZONE</strong> when finished.
              </div>
            )}
          </div>

          {/* Quick Presets Bar */}
          <div className="p-3 bg-slate-900/60 border-t border-slate-800 flex flex-wrap items-center justify-between gap-2">
            <span className="text-[11px] font-mono text-slate-400">QUICK PRESETS:</span>
            <div className="flex flex-wrap gap-1.5">
              <button
                onClick={() => handleApplyPreset('left_half')}
                className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-[11px] font-mono text-slate-300 rounded border border-slate-700"
              >
                Left Sector
              </button>
              <button
                onClick={() => handleApplyPreset('right_half')}
                className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-[11px] font-mono text-slate-300 rounded border border-slate-700"
              >
                Right Sector
              </button>
              <button
                onClick={() => handleApplyPreset('center_box')}
                className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-[11px] font-mono text-slate-300 rounded border border-slate-700"
              >
                Center Sector
              </button>
              <button
                onClick={() => handleApplyPreset('tripwire_horizontal')}
                className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-[11px] font-mono text-cyan-400 rounded border border-slate-700"
              >
                Tripwire Line
              </button>
            </div>
          </div>
        </div>

        {/* Right Column: Zone List & Settings Panel (4 cols) */}
        <div className="lg:col-span-4 space-y-4">
          {/* Active Zones List */}
          <div className="bg-[#0d1117] border border-slate-800 rounded p-3">
            <span className="text-[10px] font-mono text-slate-500 uppercase tracking-wider block mb-2">
              ACTIVE DETECTION ZONES ({zones.length})
            </span>
            <div className="space-y-1.5 max-h-48 overflow-y-auto">
              {zones.map((z) => (
                <button
                  key={z.zone_id}
                  onClick={() => {
                    setSelectedZone(z);
                    setDrawnPoints(z.zone_type === 'polygon' ? z.polygon_coords : z.line_coords);
                  }}
                  className={`w-full text-left p-2 rounded border transition-colors flex items-center justify-between ${
                    selectedZone?.zone_id === z.zone_id
                      ? 'bg-cyan-950/40 border-cyan-500/50 text-white'
                      : 'bg-slate-900/40 border-slate-800 text-slate-400 hover:bg-slate-800/60'
                  }`}
                >
                  <div>
                    <div className="text-xs font-mono font-bold">{z.name}</div>
                    <div className="text-[10px] font-mono text-slate-500">
                      {z.zone_type?.toUpperCase()} • {z.dwell_threshold}s DWELL
                    </div>
                  </div>
                  <span
                    className="w-3 h-3 rounded-full shrink-0"
                    style={{ backgroundColor: z.color || '#ef4444' }}
                  />
                </button>
              ))}
            </div>
          </div>

          {/* Zone Rules Configuration Form */}
          {selectedZone && (
            <div className="bg-[#0d1117] border border-slate-800 rounded p-4 space-y-3">
              <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                <span className="font-mono font-bold text-white text-xs">
                  ZONE PARAMETERS
                </span>
                <button
                  type="button"
                  onClick={() => handleDeleteZone(selectedZone.zone_id)}
                  className="text-rose-400 hover:text-rose-300 text-xs font-mono flex items-center space-x-1"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                  <span>DELETE</span>
                </button>
              </div>

              <div>
                <label className="block text-[11px] font-mono text-slate-400 mb-1">Zone Name</label>
                <input
                  type="text"
                  value={selectedZone.name}
                  onChange={(e) => setSelectedZone({ ...selectedZone, name: e.target.value })}
                  className="w-full bg-slate-900 border border-slate-700 rounded px-2.5 py-1.5 text-xs font-mono text-white"
                />
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block text-[11px] font-mono text-slate-400 mb-1">Type</label>
                  <select
                    value={selectedZone.zone_type}
                    onChange={(e) => setSelectedZone({ ...selectedZone, zone_type: e.target.value })}
                    className="w-full bg-slate-900 border border-slate-700 rounded px-2.5 py-1.5 text-xs font-mono text-white"
                  >
                    <option value="polygon">POLYGON</option>
                    <option value="tripwire">TRIPWIRE</option>
                  </select>
                </div>

                <div>
                  <label className="block text-[11px] font-mono text-slate-400 mb-1">Dwell Limit (Sec)</label>
                  <input
                    type="number"
                    min="1"
                    value={selectedZone.dwell_threshold}
                    onChange={(e) => setSelectedZone({ ...selectedZone, dwell_threshold: parseFloat(e.target.value) })}
                    className="w-full bg-slate-900 border border-slate-700 rounded px-2.5 py-1.5 text-xs font-mono text-white"
                  />
                </div>
              </div>

              <div>
                <label className="block text-[11px] font-mono text-slate-400 mb-1">Overlay Color</label>
                <div className="flex items-center space-x-2">
                  <input
                    type="color"
                    value={selectedZone.color}
                    onChange={(e) => setSelectedZone({ ...selectedZone, color: e.target.value })}
                    className="w-8 h-8 rounded bg-transparent border-0 cursor-pointer"
                  />
                  <span className="text-xs font-mono text-slate-300">{selectedZone.color}</span>
                </div>
              </div>

              {/* Coordinates Preview */}
              <div>
                <label className="block text-[11px] font-mono text-slate-400 mb-1">Coordinates (Auto-set by drawing)</label>
                <div className="p-2 bg-black/60 border border-slate-800 rounded text-[10px] font-mono text-cyan-400 max-h-16 overflow-y-auto">
                  {JSON.stringify(drawnPoints)}
                </div>
              </div>

              <button
                type="button"
                onClick={handleSaveZone}
                className="w-full py-2 bg-cyan-500 hover:bg-cyan-400 text-black text-xs font-mono font-bold rounded flex items-center justify-center space-x-2 transition-colors mt-2"
              >
                <Save className="w-4 h-4" />
                <span>SAVE & APPLY TO AI ENGINE</span>
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
