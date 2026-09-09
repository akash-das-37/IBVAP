import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import Sidebar from './components/Sidebar';
import DashboardPage from './pages/DashboardPage';
import LiveMonitorPage from './pages/LiveMonitorPage';
import AlertsPage from './pages/AlertsPage';
import EventHistoryPage from './pages/EventHistoryPage';
import CamerasPage from './pages/CamerasPage';
import ZonesPage from './pages/ZonesPage';
import SettingsPage from './pages/SettingsPage';

import { api } from './services/api';
import { wsService } from './services/websocket';

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [liveStats, setLiveStats] = useState({
    camera_status: 'ONLINE',
    fps: 0,
    person_count: 0,
    vehicle_count: 0,
    active_alerts_count: 0,
    source_type: 'webcam'
  });
  const [historicalStats, setHistoricalStats] = useState({
    events_today: 0,
    active_alerts: 0,
    critical_alerts: 0,
    ai_status: 'Running'
  });
  const [cameras, setCameras] = useState([]);
  const [currentCamera, setCurrentCamera] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [events, setEvents] = useState([]);
  const [alertBanner, setAlertBanner] = useState(null);

  // Initial load
  const loadInitialData = async () => {
    try {
      const [camsData, alertsData, eventsData, statsData] = await Promise.all([
        api.getCameras(),
        api.getAlerts({ limit: 15 }),
        api.getEvents({ limit: 20 }),
        api.getStats()
      ]);

      setCameras(Array.isArray(camsData) ? camsData : []);
      if (Array.isArray(camsData) && camsData.length > 0) setCurrentCamera(camsData[0]);
      setAlerts(Array.isArray(alertsData) ? alertsData : []);
      setEvents(Array.isArray(eventsData) ? eventsData : []);
      if (statsData) setHistoricalStats(statsData);
    } catch (err) {
      console.error('Error loading initial data:', err);
    }
  };

  useEffect(() => {
    loadInitialData();

    // Connect WebSocket
    wsService.connect();
    const unsubscribe = wsService.subscribe((message) => {
      if (message.type === 'STATS_UPDATE') {
        setLiveStats(message.data);
      } else if (message.type === 'NEW_ALERT') {
        const newAlert = message.data;
        setAlerts((prev) => [newAlert, ...prev.slice(0, 19)]);
        // Trigger banner alert
        setAlertBanner(newAlert);
        setTimeout(() => setAlertBanner(null), 6000);

        // Refresh stats
        api.getStats().then(setHistoricalStats).catch(console.error);
        api.getEvents({ limit: 20 }).then(setEvents).catch(console.error);
      }
    });

    // Periodic stats refresh (every 10s)
    const statsTimer = setInterval(() => {
      api.getStats().then(setHistoricalStats).catch(console.error);
    }, 10000);

    return () => {
      unsubscribe();
      clearInterval(statsTimer);
    };
  }, []);

  const handleSourceChanged = () => {
    loadInitialData();
  };

  return (
    <div className="flex flex-col h-screen w-screen bg-[#07090e] text-slate-100 overflow-hidden font-sans">
      {/* Platform Header */}
      <Header systemStats={historicalStats} />

      {/* High Severity Flash Alert Banner */}
      {alertBanner && (
        <div className="bg-rose-950/90 border-b border-rose-500/80 px-6 py-2 flex items-center justify-between z-40 animate-pulse">
          <div className="flex items-center space-x-3">
            <span className="text-base">🚨</span>
            <div>
              <span className="font-mono font-bold text-xs text-rose-300 mr-2">
                [{alertBanner.severity} INTRUSION ALERT]
              </span>
              <span className="text-xs text-white font-medium">
                {alertBanner.description}
              </span>
            </div>
          </div>
          <button
            onClick={() => setAlertBanner(null)}
            className="text-rose-300 hover:text-white font-mono text-xs"
          >
            DISMISS ✕
          </button>
        </div>
      )}

      {/* Main Workspace Layout */}
      <div className="flex flex-1 overflow-hidden">
        <Sidebar
          activeTab={activeTab}
          setActiveTab={setActiveTab}
          alertCount={alerts.filter(a => a.status === 'NEW').length}
        />

        <main className="flex-1 flex flex-col bg-[#07090e] overflow-hidden">
          {activeTab === 'dashboard' && (
            <DashboardPage
              liveStats={liveStats}
              historicalStats={historicalStats}
              currentCamera={currentCamera}
              alerts={alerts}
              events={events}
              onAlertUpdated={loadInitialData}
              onSourceChanged={handleSourceChanged}
            />
          )}

          {activeTab === 'live' && (
            <LiveMonitorPage
              liveStats={liveStats}
              currentCamera={currentCamera}
              onSourceChanged={handleSourceChanged}
            />
          )}

          {activeTab === 'alerts' && <AlertsPage />}

          {activeTab === 'history' && <EventHistoryPage />}

          {activeTab === 'cameras' && (
            <CamerasPage
              liveStats={liveStats}
              onSourceChanged={handleSourceChanged}
            />
          )}

          {activeTab === 'zones' && <ZonesPage />}

          {activeTab === 'settings' && <SettingsPage liveStats={liveStats} />}
        </main>
      </div>
    </div>
  );
}
