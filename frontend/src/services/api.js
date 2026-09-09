export function getBackendBase() {
  if (typeof window === 'undefined') return 'http://localhost:8000';
  const custom = localStorage.getItem('ibvap_backend_url');
  if (custom) return custom.replace(/\/+$/, '');
  const envUrl = import.meta.env.VITE_BACKEND_URL;
  if (envUrl) return envUrl.replace(/\/+$/, '');
  const host = window.location.hostname || 'localhost';
  if (host === 'localhost' || host === '127.0.0.1') {
    return `http://${host}:8000`;
  }
  // When accessed via local IP on same Wi-Fi
  if (/^\d+\.\d+\.\d+\.\d+$/.test(host)) {
    return `http://${host}:8000`;
  }
  // Cloud deployment (Vercel) fallback to local edge node
  return 'http://localhost:8000';
}

export function getApiBase() {
  return `${getBackendBase()}/api/v1`;
}

export const api = {
  // Health
  getHealth: async () => {
    const res = await fetch(`${getApiBase()}/health`);
    return res.json();
  },

  // Cameras
  getCameras: async () => {
    const res = await fetch(`${getApiBase()}/cameras/`);
    return res.json();
  },

  switchCameraSource: async (cameraId, sourceUrl) => {
    const res = await fetch(`${getApiBase()}/cameras/${cameraId}/source`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ source_url: sourceUrl })
    });
    return res.json();
  },

  // Zones
  getZones: async () => {
    const res = await fetch(`${getApiBase()}/zones/`);
    return res.json();
  },

  saveZone: async (zoneData) => {
    const res = await fetch(`${getApiBase()}/zones/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(zoneData)
    });
    return res.json();
  },

  deleteZone: async (zoneId) => {
    const res = await fetch(`${getApiBase()}/zones/${zoneId}`, {
      method: 'DELETE'
    });
    return res.json();
  },

  // Alerts
  getAlerts: async (limit = 20, unackOnly = false) => {
    const res = await fetch(`${getApiBase()}/alerts/?limit=${limit}&unacknowledged_only=${unackOnly}`);
    return res.json();
  },

  acknowledgeAlert: async (alertId) => {
    const res = await fetch(`${getApiBase()}/alerts/${alertId}/ack`, {
      method: 'PUT'
    });
    return res.json();
  },

  // Events & Telemetry
  getEvents: async (limit = 50, eventType = null) => {
    let url = `${getApiBase()}/events/?limit=${limit}`;
    if (eventType) url += `&event_type=${eventType}`;
    const res = await fetch(url);
    return res.json();
  },

  getEventStats: async () => {
    const res = await fetch(`${getApiBase()}/events/stats`);
    return res.json();
  }
};
