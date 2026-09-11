import { getBackendBase } from './api';
import { supabase } from './supabase';

class WebSocketService {
  constructor() {
    this.ws = null;
    this.listeners = new Set();
    this.reconnectTimeout = 3000;
    this.pingInterval = null;
    this.isConnected = false;
  }

  async connect() {
    if (this.ws && (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING)) {
      return;
    }

    const backend = getBackendBase();
    const wsProto = backend.startsWith('https') ? 'wss' : 'ws';
    const cleanHost = backend.replace(/^https?:\/\//, '');

    // Token is sent via AUTH message after connection, NOT as a URL query param
    // (URL query params can cause 431 Request Header Fields Too Large with httptools)
    const url = `${wsProto}://${cleanHost}/ws`;

    try {
      this.ws = new WebSocket(url);

      this.ws.onopen = async () => {
        this.isConnected = true;
        console.log('[IBVAP WS] Connected to live tenant-isolated alert stream.');

        // Send explicit handshake with session token
        try {
          const { data: { session } } = await supabase.auth.getSession();
          if (session?.access_token) {
            this.ws.send(JSON.stringify({
              type: 'AUTH',
              token: session.access_token
            }));
          }
        } catch (err) {
          console.warn('[IBVAP WS] Handshake auth error:', err);
        }

        // Heartbeat ping every 10s
        if (this.pingInterval) clearInterval(this.pingInterval);
        this.pingInterval = setInterval(() => {
          if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send('ping');
          }
        }, 10000);
      };

      this.ws.onmessage = (event) => {
        if (event.data === 'pong') return;
        try {
          const message = JSON.parse(event.data);
          this.listeners.forEach(callback => callback(message));
        } catch (e) {
          console.error('[IBVAP WS] Message parse error:', e);
        }
      };

      this.ws.onclose = () => {
        this.isConnected = false;
        clearInterval(this.pingInterval);
        console.warn('[IBVAP WS] Connection closed. Reconnecting in 3s...');
        setTimeout(() => this.connect(), this.reconnectTimeout);
      };

      this.ws.onerror = (err) => {
        console.error('[IBVAP WS] Socket error:', err);
      };
    } catch (e) {
      console.error('[IBVAP WS] Connection failed:', e);
      setTimeout(() => this.connect(), this.reconnectTimeout);
    }
  }

  disconnect() {
    if (this.ws) {
      clearInterval(this.pingInterval);
      this.ws.close();
      this.ws = null;
      this.isConnected = false;
    }
  }

  subscribe(callback) {
    this.listeners.add(callback);
    return () => this.listeners.delete(callback);
  }
}

export const wsService = new WebSocketService();
