class WebSocketService {
  constructor() {
    this.ws = null;
    this.listeners = new Set();
    this.reconnectTimeout = 3000;
    this.pingInterval = null;
    this.isConnected = false;
  }

  connect() {
    const host = window.location.hostname || 'localhost';
    const url = `ws://${host}:8000/ws/alerts`;

    try {
      this.ws = new WebSocket(url);

      this.ws.onopen = () => {
        this.isConnected = true;
        console.log('[IBVAP WS] Connected to live alert stream.');
        // Heartbeat ping every 10s
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

  subscribe(callback) {
    this.listeners.add(callback);
    return () => this.listeners.delete(callback);
  }
}

export const wsService = new WebSocketService();
