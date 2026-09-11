import { supabase } from './supabase';

export function getBackendBase() {
  if (typeof window === 'undefined') return 'http://127.0.0.1:8000';
  const custom = localStorage.getItem('ibvap_backend_url');
  if (custom) return custom.replace(/\/+$/, '');
  const envUrl = import.meta.env.VITE_BACKEND_URL;
  if (envUrl) return envUrl.replace(/\/+$/, '');
  const host = window.location.hostname || '127.0.0.1';
  if (host === 'localhost' || host === '127.0.0.1') {
    return 'http://127.0.0.1:8000';
  }
  if (/^\d+\.\d+\.\d+\.\d+$/.test(host)) {
    return `http://${host}:8000`;
  }
  return 'http://127.0.0.1:8000';
}

export function getApiBase() {
  return `${getBackendBase()}/api/v1`;
}

export function formatSnapshotUrl(path) {
  if (!path) return '';
  if (path.startsWith('http://') || path.startsWith('https://')) {
    return path;
  }
  return `${getBackendBase()}${path.startsWith('/') ? path : `/${path}`}`;
}

async function getAuthSession() {
  try {
    const { data: { session } } = await supabase.auth.getSession();
    if (session?.access_token) return session;

    // Fallback: auto-authenticate as default surveillance operator if no session exists
    const { data, error } = await supabase.auth.signInWithPassword({
      email: 'iamnegative37@gmail.com',
      password: 'Surveillance2026!'
    });
    if (!error && data?.session) {
      return data.session;
    }
    return null;
  } catch (err) {
    console.warn('[IBVAP Auth] Session lookup error:', err);
    return null;
  }
}

export async function getAuthUserAndOrg() {
  try {
    const session = await getAuthSession();
    if (!session?.user) return { user: null, org: null, token: null };

    const { data: members, error } = await supabase
      .from('organization_members')
      .select('organization_id, role, organizations(id, name, slug)')
      .eq('user_id', session.user.id)
      .limit(1);

    if (error || !members || members.length === 0) {
      return { user: session.user, org: null, token: session.access_token };
    }

    const org = members[0].organizations || { id: members[0].organization_id };
    return {
      user: session.user,
      org: org,
      token: session.access_token
    };
  } catch (err) {
    console.error('[IBVAP Auth] Error resolving user organization:', err);
    return { user: null, org: null, token: null };
  }
}

async function authFetch(url, options = {}, defaultValue = null) {
  try {
    const session = await getAuthSession();
    if (!url.includes('/health') && !session?.access_token) {
      return defaultValue;
    }
    const headers = {
      ...(options.headers || {})
    };
    if (session?.access_token) {
      headers['Authorization'] = `Bearer ${session.access_token}`;
    }
    const res = await fetch(url, { ...options, headers });
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
    return authFetch(`${getApiBase()}/health`, {}, { status: 'OFFLINE' });
  },

  // Sites (strictly isolated per organization)
  getSites: async () => {
    const { org } = await getAuthUserAndOrg();
    if (org?.id) {
      const { data, error } = await supabase
        .from('sites')
        .select('*')
        .eq('organization_id', org.id)
        .order('created_at', { ascending: true });
      if (!error && Array.isArray(data)) return data;
    }
    return authFetch(`${getApiBase()}/sites/`, {}, []);
  },

  createSite: async (siteData) => {
    const { org } = await getAuthUserAndOrg();
    if (org?.id) {
      const { data, error } = await supabase
        .from('sites')
        .upsert({
          organization_id: org.id,
          site_id: siteData.site_id,
          name: siteData.name,
          location: siteData.location || 'Perimeter Sector'
        }, { onConflict: 'organization_id,site_id' })
        .select();
      if (!error) return data;
    }
    return authFetch(`${getApiBase()}/sites/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(siteData)
    }, null);
  },

  deleteSite: async (siteId) => {
    const { org } = await getAuthUserAndOrg();
    if (org?.id) {
      await supabase
        .from('sites')
        .delete()
        .eq('organization_id', org.id)
        .eq('site_id', siteId);
    }
    return authFetch(`${getApiBase()}/sites/${siteId}`, { method: 'DELETE' }, { success: true });
  },

  // Cameras (strictly isolated per organization)
  getCameras: async () => {
    const { org } = await getAuthUserAndOrg();
    if (org?.id) {
      const { data, error } = await supabase
        .from('cameras')
        .select('*')
        .eq('organization_id', org.id)
        .order('created_at', { ascending: true });

      if (!error && Array.isArray(data) && data.length > 0) {
        return data;
      }

      // Auto-initialize primary camera profile for this organization if brand new
      if (!error && Array.isArray(data) && data.length === 0) {
        const defaultCam = {
          organization_id: org.id,
          camera_id: 'CAM-01',
          name: `CAM-01 — ${org.name || 'Perimeter Sector'}`,
          source_url: '0',
          location: org.name || 'Main Sector',
          status: 'ONLINE',
          enabled: true
        };
        const { data: inserted } = await supabase
          .from('cameras')
          .insert([defaultCam])
          .select();
        return inserted && inserted.length > 0 ? inserted : [defaultCam];
      }
    }

    const data = await authFetch(`${getApiBase()}/cameras/`, {}, []);
    return Array.isArray(data) ? data : [];
  },

  switchCameraSource: async (cameraId, sourceUrl) => {
    const { org } = await getAuthUserAndOrg();
    if (org?.id) {
      await supabase
        .from('cameras')
        .update({ source_url: sourceUrl, status: 'ONLINE', updated_at: new Date().toISOString() })
        .eq('organization_id', org.id)
        .eq('camera_id', cameraId);
    }
    return authFetch(`${getApiBase()}/cameras/${cameraId}/source`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ source_url: sourceUrl })
    }, { success: false });
  },

  // Zones (strictly isolated per organization, site, and camera)
  getZones: async (cameraId = null) => {
    const { org } = await getAuthUserAndOrg();
    if (org?.id) {
      let query = supabase
        .from('zones')
        .select('*')
        .eq('organization_id', org.id)
        .order('created_at', { ascending: true });

      if (cameraId) {
        query = query.eq('camera_id', cameraId);
      }

      const { data, error } = await query;
      if (!error && Array.isArray(data)) {
        // Sync backend live pipeline with active zones in background
        authFetch(`${getApiBase()}/zones/`, {}, []).catch(() => {});
        return data;
      }
    }

    const q = cameraId ? `?camera_id=${cameraId}` : '';
    const data = await authFetch(`${getApiBase()}/zones/${q}`, {}, []);
    return Array.isArray(data) ? data : [];
  },

  saveZone: async (zoneData) => {
    const { org } = await getAuthUserAndOrg();
    if (!org?.id) throw new Error('Authentication required to save zone');

    // 1. Fetch cameras for this organization to get exact database UUID and site UUID
    const cameras = await api.getCameras();
    const primaryCam = (Array.isArray(cameras) && cameras.length > 0)
      ? (cameras.find(c => c.id === zoneData.camera_id || c.camera_id === zoneData.camera_id) || cameras[0])
      : null;

    const cameraUuid = primaryCam?.id || zoneData.camera_id;
    const siteUuid = primaryCam?.site_id || zoneData.site_id;

    // 2. Normalize polygon points into [{ x, y }] between 0 and 1
    const rawPoints = zoneData.polygon_data || zoneData.polygon_coords || [];
    const normData = rawPoints.map(pt => {
      let x = 0, y = 0;
      if (typeof pt === 'object' && pt !== null && !Array.isArray(pt)) {
        x = Number(pt.x) || 0;
        y = Number(pt.y) || 0;
      } else if (Array.isArray(pt) && pt.length >= 2) {
        x = Number(pt[0]) || 0;
        y = Number(pt[1]) || 0;
      }
      if (x > 1.0 || y > 1.0) {
        x = Number((x / 960).toFixed(4));
        y = Number((y / 540).toFixed(4));
      }
      return { x, y };
    });

    const payload = {
      zone_id: zoneData.zone_id,
      name: zoneData.name || 'Border Sector 1',
      camera_id: cameraUuid,
      site_id: siteUuid,
      zone_type: zoneData.zone_type || 'polygon',
      polygon_data: normData,
      polygon_coords: normData.map(p => [p.x, p.y]),
      line_coords: zoneData.line_coords || [],
      is_restricted: zoneData.is_restricted ?? true,
      dwell_threshold: zoneData.dwell_threshold ?? 10.0,
      prohibited_directions: zoneData.prohibited_directions || [],
      color: zoneData.color || '#ef4444',
      enabled: zoneData.enabled ?? true
    };

    // Save to Supabase
    if (cameraUuid) {
      const cleanZone = {
        organization_id: org.id,
        site_id: siteUuid,
        camera_id: cameraUuid,
        zone_id: payload.zone_id,
        name: payload.name,
        zone_type: payload.zone_type,
        polygon_data: payload.polygon_data,
        polygon_coords: payload.polygon_coords,
        line_coords: payload.line_coords,
        is_restricted: payload.is_restricted,
        dwell_threshold: payload.dwell_threshold,
        prohibited_directions: payload.prohibited_directions,
        color: payload.color,
        enabled: payload.enabled
      };

      const { error: supaErr } = await supabase
        .from('zones')
        .upsert(cleanZone, { onConflict: 'organization_id,zone_id' });

      if (supaErr) {
        console.error('[IBVAP Zones] Supabase insert error:', supaErr);
        throw new Error(supaErr.message || 'Database rejected zone insert');
      }
    }

    // Also send to FastAPI backend to synchronize the in-memory AI engine
    const backendResult = await authFetch(`${getApiBase()}/zones/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    }, null);

    return backendResult || { success: true, zone_id: payload.zone_id };
  },

  deleteZone: async (zoneId) => {
    const { org } = await getAuthUserAndOrg();
    if (org?.id) {
      const { error } = await supabase
        .from('zones')
        .delete()
        .eq('organization_id', org.id)
        .eq('zone_id', zoneId);
      if (error) console.warn('[IBVAP Zones] Supabase delete warning:', error);
    }
    return authFetch(`${getApiBase()}/zones/${zoneId}`, {
      method: 'DELETE'
    }, { success: true });
  },

  // Alerts (strictly isolated per organization via Supabase RLS)
  getAlerts: async (params = {}) => {
    const { org } = await getAuthUserAndOrg();
    if (org?.id) {
      let query = supabase
        .from('alerts')
        .select('*')
        .eq('organization_id', org.id)
        .order('timestamp', { ascending: false });

      if (typeof params === 'object' && params !== null) {
        if (params.severity) query = query.eq('severity', params.severity.toUpperCase());
        if (params.status) query = query.eq('status', params.status.toUpperCase());
        if (params.camera_id) query = query.eq('camera_id', params.camera_id);
        if (params.limit) query = query.limit(params.limit);
      } else if (typeof params === 'number') {
        query = query.limit(params);
      }

      const { data, error } = await query;
      if (!error && Array.isArray(data)) return data;
      if (error) console.error('[IBVAP Alerts] Supabase query error:', error);
      return [];
    }

    let q = '';
    if (typeof params === 'number') {
      q = `limit=${params}`;
    } else if (typeof params === 'object' && params !== null) {
      q = new URLSearchParams(params).toString();
    }
    const data = await authFetch(`${getApiBase()}/alerts/${q ? `?${q}` : ''}`, {}, []);
    return Array.isArray(data) ? data : [];
  },

  acknowledgeAlert: async (alertId) => {
    const { org } = await getAuthUserAndOrg();
    if (org?.id) {
      const { error } = await supabase
        .from('alerts')
        .update({ status: 'ACKNOWLEDGED' })
        .eq('organization_id', org.id)
        .eq('alert_id', alertId);
      if (!error) return { success: true };
    }
    return authFetch(`${getApiBase()}/alerts/${alertId}/acknowledge`, {
      method: 'PATCH'
    }, { success: false });
  },

  // Events (strictly isolated per organization via Supabase RLS)
  getEvents: async (params = {}) => {
    const { org } = await getAuthUserAndOrg();
    if (org?.id) {
      let query = supabase
        .from('events')
        .select('*')
        .eq('organization_id', org.id)
        .order('timestamp', { ascending: false });

      if (typeof params === 'object' && params !== null) {
        if (params.camera_id) query = query.eq('camera_id', params.camera_id);
        if (params.event_type) query = query.eq('event_type', params.event_type.toUpperCase());
        if (params.limit) query = query.limit(params.limit);
      } else if (typeof params === 'number') {
        query = query.limit(params);
      }

      const { data, error } = await query;
      if (!error && Array.isArray(data)) return data;
      if (error) console.error('[IBVAP Events] Supabase query error:', error);
      return [];
    }

    let q = '';
    if (typeof params === 'number') {
      q = `limit=${params}`;
    } else if (typeof params === 'object' && params !== null) {
      q = new URLSearchParams(params).toString();
    }
    const data = await authFetch(`${getApiBase()}/events/${q ? `?${q}` : ''}`, {}, []);
    return Array.isArray(data) ? data : [];
  },

  // Stats (strictly computed from organization's isolated Supabase tables)
  getStats: async () => {
    const { org } = await getAuthUserAndOrg();
    if (org?.id) {
      const todayStart = new Date();
      todayStart.setUTCHours(0, 0, 0, 0);

      const [eventsRes, activeAlertsRes, criticalAlertsRes] = await Promise.all([
        supabase.from('events').select('id', { count: 'exact', head: true }).eq('organization_id', org.id).gte('timestamp', todayStart.toISOString()),
        supabase.from('alerts').select('id', { count: 'exact', head: true }).eq('organization_id', org.id).eq('status', 'NEW'),
        supabase.from('alerts').select('id', { count: 'exact', head: true }).eq('organization_id', org.id).eq('severity', 'CRITICAL').eq('status', 'NEW')
      ]);

      return {
        events_today: eventsRes.count || 0,
        active_alerts: activeAlertsRes.count || 0,
        critical_alerts: criticalAlertsRes.count || 0,
        organization_id: org.id,
        ai_status: `Tenant Isolated (${org.name || 'Cloud Secured'})`
      };
    }

    return authFetch(`${getApiBase()}/events/stats`, {}, {
      events_today: 0,
      active_alerts: 0,
      critical_alerts: 0,
      ai_status: 'Edge Connected'
    });
  },

  getEventStats: async () => {
    return api.getStats();
  },

  // Persist live alert & event directly into current organization's database
  createAlert: async (alert) => {
    const { org } = await getAuthUserAndOrg();
    if (!org?.id) return;

    const alertId = alert.alert_id || `ALT-${Math.floor(1000 + Math.random() * 9000)}`;
    const eventId = `EVT-${Math.floor(1000 + Math.random() * 9000)}`;
    const nowIso = alert.timestamp || new Date().toISOString();

    await Promise.all([
      supabase.from('alerts').insert([{
        organization_id: org.id,
        alert_id: alertId,
        event_type: alert.event_type || 'INTRUSION',
        severity: alert.severity || 'HIGH',
        camera_id: alert.camera_id || 'CAM-01',
        zone_id: alert.zone_id || null,
        zone_name: alert.zone_name || 'Restricted Zone',
        object_type: alert.object_type || 'person',
        track_id: alert.track_id || null,
        confidence: alert.confidence || 0.88,
        description: alert.description || 'Intrusion alert detected',
        snapshot_path: alert.snapshot_path || null,
        timestamp: nowIso,
        status: 'NEW'
      }]),
      supabase.from('events').insert([{
        organization_id: org.id,
        event_id: eventId,
        camera_id: alert.camera_id || 'CAM-01',
        timestamp: nowIso,
        event_type: alert.event_type || 'ZONE_INTRUSION',
        object_type: alert.object_type || 'person',
        track_id: alert.track_id || null,
        confidence: alert.confidence || 0.88,
        zone_name: alert.zone_name || 'Restricted Zone',
        snapshot_path: alert.snapshot_path || null
      }])
    ]);
  }
};
