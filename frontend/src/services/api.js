const API_BASE = `http://${window.location.hostname}:8000/api/v1`;

export const api = {
  // Health
  getHealth: async () => {
    const res = await fetch(`${API_BASE}/health`);
    return res.json();
  },

  // Cameras
  getCameras: async () => {
    const res = await fetch(`${API_BASE}/cameras/`);
    return res.json();
  },

  switchCameraSource: async (cameraId, sourceUrl) => {
    const res = await fetch(`${API_BASE}/cameras/${cameraId}/source`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ source_url: sourceUrl })
    });
    return res.json();
  },

  // Zones
  getZones: async () => {
    const res = await fetch(`${API_BASE}/zones/`);
    return res.json();
  },

  saveZone: async (zoneData) => {
    const res = await fetch(`${API_BASE}/zones/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(zoneData)
    });
    return res.json();
  },

  deleteZone: async (zoneId) => {
    const res = await fetch(`${API_BASE}/zones/${zoneId}`, {
      method: 'DELETE'
    });
    return res.json();
  },

  // Alerts
  getAlerts: async (params = {}) => {
    const q = new URLSearchParams(params).toString();
    const res = await fetch(`${API_BASE}/alerts/?${q}`);
    return res.json();
  },

  acknowledgeAlert: async (alertId) => {
    const res = await fetch(`${API_BASE}/alerts/${alertId}/acknowledge`, {
      method: 'PATCH'
    });
    return res.json();
  },

  // Events & Stats
  getEvents: async (params = {}) => {
    const q = new URLSearchParams(params).toString();
    const res = await fetch(`${API_BASE}/events/?${q}`);
    return res.json();
  },

  getStats: async () => {
    const res = await fetch(`${API_BASE}/events/stats`);
    return res.json();
  }
};
