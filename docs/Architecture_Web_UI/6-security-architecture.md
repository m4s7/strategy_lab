# 6. Security Architecture

## 6.1 Security Layers

```yaml
Security Architecture:
  Network Layer:
    - VPN-only access (WireGuard/OpenVPN)
    - No public internet exposure
    - Internal network only (192.168.x.x)

  Application Layer:
    - No authentication needed (single user)
    - CORS disabled (same origin only)
    - CSP headers for XSS protection
    - Input validation on all endpoints

  Data Layer:
    - File system permissions (read-only for data)
    - SQLite with WAL mode for concurrency
    - No sensitive data in logs

  Transport Layer:
    - HTTPS with self-signed cert (internal)
    - WSS for WebSocket connections
```

## 6.2 Security Headers

```typescript
// Next.js Security Configuration
const securityHeaders = [
  {
    key: 'X-Frame-Options',
    value: 'DENY'
  },
  {
    key: 'X-Content-Type-Options',
    value: 'nosniff'
  },
  {
    key: 'X-XSS-Protection',
    value: '1; mode=block'
  },
  {
    key: 'Content-Security-Policy',
    value: `
      default-src 'self';
      script-src 'self' 'unsafe-inline' 'unsafe-eval';
      style-src 'self' 'unsafe-inline';
      img-src 'self' data: blob:;
      connect-src 'self' ws://localhost:* wss://localhost:*;
    `.replace(/\s{2,}/g, ' ').trim()
  }
];
```

---
