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

async function safeFetch(url, options = {}, defaultValue = null) {
  try {
    const res = await fetch(url, options);
    if (!res.ok) {
      console.warn(`[IBVAP API] HTTP ${res.status} for ${url}`);
      return defaultValue;
    }
    return await res.json();
  } catch (err) {
    console.warn(`[IBVAP API] Request failed for ${url}:`, err.message);
    return defaultValue;
  }
}

export const api = {
  // Health
  getHealth: async () => {
    return safeFetch(`${getApiBase()}/health`, {}, { status: 'OFFLINE' });
  },

  // Cameras
  getCameras: async () => {
    const data = await safeFetch(`${getApiBase()}/cameras/`, {}, []);
    return Array.isArray(data) ? data : [];
  },

  switchCameraSource: async (cameraId, sourceUrl) => {
    return safeFetch(`${getApiBase()}/cameras/${cameraId}/source`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ source_url: sourceUrl })
    }, { success: false });
  },

  // Zones
  getZones: async () => {
    const data = await safeFetch(`${getApiBase()}/zones/`, {}, []);
    return Array.isArray(data) ? data : [];
  },

  saveZone: async (zoneData) => {
    return safeFetch(`${getApiBase()}/zones/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(zoneData)
    }, { success: false });
  },

  deleteZone: async (zoneId) => {
    return safeFetch(`${getApiBase()}/zones/${zoneId}`, {
      method: 'DELETE'
    }, { success: false });
  },

  // Alerts - supports both getAlerts({ limit: 15, severity: 'HIGH' }) and getAlerts(15)
  getAlerts: async (params = {}) => {
    let q = '';
    if (typeof params === 'number') {
      q = `limit=${params}`;
    } else if (typeof params === 'object' && params !== null) {
      q = new URLSearchParams(params).toString();
    }
    const url = `${getApiBase()}/alerts/${q ? `?${q}` : ''}`;
    const data = await safeFetch(url, {}, []);
    return Array.isArray(data) ? data : [];
  },

  acknowledgeAlert: async (alertId) => {
    return safeFetch(`${getApiBase()}/alerts/${alertId}/acknowledge`, {
      method: 'PATCH'
    }, { success: false });
  },

  // Events - supports both getEvents({ limit: 20 }) and getEvents(20)
  getEvents: async (params = {}) => {
    let q = '';
    if (typeof params === 'number') {
      q = `limit=${params}`;
    } else if (typeof params === 'object' && params !== null) {
      q = new URLSearchParams(params).toString();
    }
    const url = `${getApiBase()}/events/${q ? `?${q}` : ''}`;
    const data = await safeFetch(url, {}, []);
    return Array.isArray(data) ? data : [];
  },

  // Stats - alias both getStats and getEventStats
  getStats: async () => {
    return safeFetch(`${getApiBase()}/events/stats`, {}, {
      events_today: 0,
      active_alerts: 0,
      critical_alerts: 0,
      ai_status: 'Edge Connected'
    });
  },

  getEventStats: async () => {
    return api.getStats();
  }
};
