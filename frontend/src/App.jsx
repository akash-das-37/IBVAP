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
import AuthPage from './pages/AuthPage';

import { api, getAuthUserAndOrg } from './services/api';
import { wsService } from './services/websocket';
import { supabase } from './services/supabase';

export default function App() {
  const [currentUser, setCurrentUser] = useState(null);
  const [currentOrg, setCurrentOrg] = useState(null);
  const [authChecking, setAuthChecking] = useState(true);

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
  const [zones, setZones] = useState([]);
  const [alertBanner, setAlertBanner] = useState(null);

  // Check Supabase authentication session on mount
  useEffect(() => {
    sessionStorage.removeItem('ibvap_demo_user');
    supabase.auth.getSession().then(async ({ data: { session } }) => {
      if (session?.user) {
        setCurrentUser(session.user);
      } else {
        // Auto-authenticate as primary defense operator if not logged in
        try {
          const { data, error } = await supabase.auth.signInWithPassword({
            email: 'iamnegative37@gmail.com',
            password: 'Surveillance2026!'
          });
          if (!error && data?.user) {
            setCurrentUser(data.user);
          }
        } catch (e) {
          console.warn('[IBVAP] Auto-auth failed:', e);
        }
      }
      setAuthChecking(false);
    }).catch(() => setAuthChecking(false));

    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      if (session?.user) {
        setCurrentUser(session.user);
      }
    });

    return () => subscription.unsubscribe();
  }, []);

  const handleSignOut = async () => {
    sessionStorage.removeItem('ibvap_demo_user');
    await supabase.auth.signOut().catch(() => {});
    setCurrentUser(null);
    setCurrentOrg(null);
    setAlerts([]);
    setEvents([]);
    setZones([]);
    setHistoricalStats({
      events_today: 0,
      active_alerts: 0,
      critical_alerts: 0,
      ai_status: 'Ready'
    });
  };

  // Initial load
  const loadInitialData = async () => {
    try {
      const [camsData, alertsData, eventsData, statsData, zonesData] = await Promise.all([
        api.getCameras(),
        api.getAlerts({ limit: 15 }),
        api.getEvents({ limit: 20 }),
        api.getStats(),
        api.getZones()
      ]);

      setCameras(Array.isArray(camsData) ? camsData : []);
      if (Array.isArray(camsData) && camsData.length > 0) setCurrentCamera(camsData[0]);
      setAlerts(Array.isArray(alertsData) ? alertsData : []);
      setEvents(Array.isArray(eventsData) ? eventsData : []);
      if (statsData) setHistoricalStats(statsData);
      setZones(Array.isArray(zonesData) ? zonesData : []);
    } catch (err) {
      console.error('Error loading initial data:', err);
    }
  };

  // Reload data and connect WebSocket whenever active operator changes
  useEffect(() => {
    if (!currentUser) {
      setCurrentOrg(null);
      return;
    }

    getAuthUserAndOrg().then(({ org }) => {
      if (org) setCurrentOrg(org);
    }).catch(console.error);

    loadInitialData();

    // Connect WebSocket AFTER authentication so the AUTH handshake has a valid session
    wsService.disconnect();
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

        // Refresh stats and events
        api.getStats().then(setHistoricalStats).catch(console.error);
        api.getEvents({ limit: 20 }).then(setEvents).catch(console.error);
      }
    });

    // Periodic stats refresh (every 10s)
    const statsTimer = setInterval(() => {
      api.getStats().then(setHistoricalStats).catch(console.error);
    }, 10000);

    // Periodic alert/event refresh (every 5s) — ensures dashboard stays current
    const alertRefreshTimer = setInterval(() => {
      api.getAlerts({ limit: 15 }).then(data => {
        if (Array.isArray(data)) setAlerts(data);
      }).catch(console.error);
      api.getEvents({ limit: 20 }).then(data => {
        if (Array.isArray(data)) setEvents(data);
      }).catch(console.error);
    }, 5000);

    return () => {
      unsubscribe();
      clearInterval(statsTimer);
      clearInterval(alertRefreshTimer);
    };
  }, [currentUser?.id]);

  const handleSourceChanged = () => {
    loadInitialData();
  };

  if (authChecking) {
    return (
      <div className="flex h-screen w-screen items-center justify-center bg-[#07090e] text-cyan-400 font-mono text-sm select-none">
        <div className="flex flex-col items-center space-y-3">
          <div className="w-8 h-8 border-2 border-cyan-500 border-t-transparent rounded-full animate-spin shadow-[0_0_15px_rgba(0,240,255,0.4)]" />
          <span className="tracking-widest animate-pulse">VERIFYING OPERATOR CLEARANCE...</span>
        </div>
      </div>
    );
  }

  if (!currentUser) {
    return (
      <AuthPage
        onAuthenticated={(user) => {
          if (user.id === 'demo-operator-01') {
            sessionStorage.setItem('ibvap_demo_user', JSON.stringify(user));
          }
          setCurrentUser(user);
        }}
      />
    );
  }

  return (
    <div className="flex flex-col h-screen w-screen bg-[#07090e] text-slate-100 overflow-hidden font-sans">
      {/* Platform Header */}
      <Header
        systemStats={historicalStats}
        currentUser={currentUser}
        currentOrg={currentOrg}
        onSignOut={handleSignOut}
      />

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
              zones={zones}
              onAlertUpdated={loadInitialData}
              onSourceChanged={handleSourceChanged}
            />
          )}

          {activeTab === 'live' && (
            <LiveMonitorPage
              liveStats={liveStats}
              currentCamera={currentCamera}
              zones={zones}
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
