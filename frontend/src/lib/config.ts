// Runtime configuration for client-side environment variables
// Check if we're in development mode based on hostname
const isDevelopment = typeof window !== 'undefined' &&
  (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1');

const isPort3457 = typeof window !== 'undefined' && window.location.port === '3457';

export const config = {
  apiUrl: process.env.NEXT_PUBLIC_API_URL ||
    (isDevelopment
      ? (isPort3457 ? 'http://localhost:8001/api' : 'http://localhost:8000/api')
      : '/api'),
  wsUrl: process.env.NEXT_PUBLIC_WS_URL ||
    (isDevelopment
      ? (isPort3457 ? 'ws://localhost:8001/ws' : 'ws://localhost:8000/ws')
      : '/ws'),
};

// Export for convenience
export const API_URL = config.apiUrl;
export const WS_URL = config.wsUrl;
