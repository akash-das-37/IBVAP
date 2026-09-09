import React from 'react';
import {
  LayoutDashboard,
  Video,
  AlertTriangle,
  History,
  Camera,
  MapPin,
  Settings as SettingsIcon,
  Radio
} from 'lucide-react';

export default function Sidebar({ activeTab, setActiveTab, alertCount = 0 }) {
  const menuItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'live', label: 'Live Monitoring', icon: Video },
    { id: 'alerts', label: 'Alerts', icon: AlertTriangle, badge: alertCount },
    { id: 'history', label: 'Event History', icon: History },
    { id: 'cameras', label: 'Cameras', icon: Camera },
    { id: 'zones', label: 'Zones', icon: MapPin },
    { id: 'settings', label: 'Settings', icon: SettingsIcon }
  ];

  return (
    <aside className="w-60 bg-[#0d1117] border-r border-slate-800 flex flex-col justify-between py-4 select-none shrink-0">
      <div>
        {/* Navigation Category */}
        <div className="px-4 mb-3">
          <span className="text-[10px] font-mono tracking-widest text-slate-500 uppercase font-semibold">
            TACTICAL NAVIGATION
          </span>
        </div>

        <nav className="space-y-1 px-2">
          {menuItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`w-full flex items-center justify-between px-3 py-2.5 rounded text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/30 shadow-[0_0_8px_rgba(0,240,255,0.15)]'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/60'
                }`}
              >
                <div className="flex items-center space-x-3">
                  <Icon className={`w-4 h-4 ${isActive ? 'text-cyan-400' : 'text-slate-400'}`} />
                  <span>{item.label}</span>
                </div>
                {item.badge > 0 && (
                  <span className="px-1.5 py-0.5 text-xs font-mono font-bold bg-rose-500/20 text-rose-400 border border-rose-500/40 rounded-full animate-pulse">
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Mission Footer */}
      <div className="px-4 pt-4 border-t border-slate-800/80">
        <div className="flex items-center space-x-2 text-slate-400 mb-2">
          <Radio className="w-3.5 h-3.5 text-emerald-400 animate-pulse" />
          <span className="text-[11px] font-mono tracking-wide text-slate-300">SURVEILLANCE ACTIVE</span>
        </div>
        <div className="text-[10px] text-slate-500 font-mono leading-relaxed">
          SECURE PERIMETER MONITORING<br />
          EDGE NODE: 01-ONLINE
        </div>
      </div>
    </aside>
  );
}
