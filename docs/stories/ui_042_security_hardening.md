# UI_042: Security Hardening

## Story
As a trader, I want my trading data and strategies to be secure from unauthorized access and vulnerabilities so that my intellectual property and trading edge are protected.

## Acceptance Criteria
1. Implement authentication and authorization system
2. Secure all API endpoints with proper validation
3. Encrypt sensitive data in transit and at rest
4. Implement rate limiting and DDoS protection
5. Add input sanitization and XSS prevention
6. Set up security headers and CSP policies
7. Implement audit logging for all actions
8. Regular security vulnerability scanning

## Technical Requirements

### Authentication System
```typescript
// lib/auth/auth-provider.tsx
import { createContext, useContext, useState, useEffect } from 'react';
import jwt from 'jsonwebtoken';

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  permissions: Permission[];
}

interface AuthContextType extends AuthState {
  login: (credentials: LoginCredentials) => Promise<void>;
  logout: () => void;
  refreshToken: () => Promise<void>;
  hasPermission: (permission: string) => boolean;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [authState, setAuthState] = useState<AuthState>({
    user: null,
    token: null,
    isAuthenticated: false,
    permissions: []
  });

  // Initialize auth state from secure storage
  useEffect(() => {
    const initAuth = async () => {
      const token = await SecureStorage.getItem('authToken');
      if (token && isValidToken(token)) {
        const user = decodeToken(token);
        setAuthState({
          user,
          token,
          isAuthenticated: true,
          permissions: user.permissions
        });
      }
    };
    initAuth();
  }, []);

  const login = async (credentials: LoginCredentials) => {
    try {
      // Validate input
      validateLoginInput(credentials);

      // Hash password before sending
      const hashedPassword = await hashPassword(credentials.password);

      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRF-Token': await getCSRFToken()
        },
        body: JSON.stringify({
          username: credentials.username,
          password: hashedPassword,
          mfaCode: credentials.mfaCode
        })
      });

      if (!response.ok) {
        const error = await response.json();
        throw new AuthError(error.message, error.code);
      }

      const { token, user } = await response.json();

      // Validate token signature
      if (!verifyTokenSignature(token)) {
        throw new AuthError('Invalid token signature');
      }

      // Store in secure storage
      await SecureStorage.setItem('authToken', token);

      setAuthState({
        user,
        token,
        isAuthenticated: true,
        permissions: user.permissions
      });

      // Set up token refresh
      scheduleTokenRefresh(token);

    } catch (error) {
      console.error('Login failed:', error);
      throw error;
    }
  };

  const refreshToken = async () => {
    try {
      const response = await fetch('/api/auth/refresh', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${authState.token}`,
          'X-CSRF-Token': await getCSRFToken()
        }
      });

      if (!response.ok) {
        throw new AuthError('Token refresh failed');
      }

      const { token } = await response.json();
      await SecureStorage.setItem('authToken', token);

      setAuthState(prev => ({ ...prev, token }));
      scheduleTokenRefresh(token);

    } catch (error) {
      // Refresh failed, logout user
      logout();
      throw error;
    }
  };

  const logout = () => {
    SecureStorage.removeItem('authToken');
    setAuthState({
      user: null,
      token: null,
      isAuthenticated: false,
      permissions: []
    });

    // Clear all sensitive data
    clearSensitiveData();
  };

  const hasPermission = (permission: string): boolean => {
    return authState.permissions.some(p =>
      p.name === permission || p.name === 'admin'
    );
  };

  return (
    <AuthContext.Provider value={{
      ...authState,
      login,
      logout,
      refreshToken,
      hasPermission
    }}>
      {children}
    </AuthContext.Provider>
  );
}

// Secure storage implementation
class SecureStorage {
  private static encryptionKey: CryptoKey | null = null;

  private static async getKey(): Promise<CryptoKey> {
    if (!this.encryptionKey) {
      const keyMaterial = await window.crypto.subtle.importKey(
        'raw',
        new TextEncoder().encode(process.env.NEXT_PUBLIC_STORAGE_KEY!),
        'PBKDF2',
        false,
        ['deriveBits', 'deriveKey']
      );

      this.encryptionKey = await window.crypto.subtle.deriveKey(
        {
          name: 'PBKDF2',
          salt: new TextEncoder().encode('strategy-lab-salt'),
          iterations: 100000,
          hash: 'SHA-256'
        },
        keyMaterial,
        { name: 'AES-GCM', length: 256 },
        false,
        ['encrypt', 'decrypt']
      );
    }
    return this.encryptionKey;
  }

  static async setItem(key: string, value: string): Promise<void> {
    const cryptoKey = await this.getKey();
    const iv = window.crypto.getRandomValues(new Uint8Array(12));

    const encrypted = await window.crypto.subtle.encrypt(
      { name: 'AES-GCM', iv },
      cryptoKey,
      new TextEncoder().encode(value)
    );

    const data = {
      iv: Array.from(iv),
      data: Array.from(new Uint8Array(encrypted))
    };

    localStorage.setItem(key, JSON.stringify(data));
  }

  static async getItem(key: string): Promise<string | null> {
    const stored = localStorage.getItem(key);
    if (!stored) return null;

    try {
      const { iv, data } = JSON.parse(stored);
      const cryptoKey = await this.getKey();

      const decrypted = await window.crypto.subtle.decrypt(
        { name: 'AES-GCM', iv: new Uint8Array(iv) },
        cryptoKey,
        new Uint8Array(data)
      );

      return new TextDecoder().decode(decrypted);
    } catch (error) {
      console.error('Decryption failed:', error);
      return null;
    }
  }

  static removeItem(key: string): void {
    localStorage.removeItem(key);
  }
}
```

### API Security Middleware
```typescript
// api/middleware/security.ts
import rateLimit from 'express-rate-limit';
import helmet from 'helmet';
import { body, validationResult } from 'express-validator';
import jwt from 'jsonwebtoken';
import crypto from 'crypto';

// Rate limiting configuration
export const rateLimiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100, // Limit each IP to 100 requests per windowMs
  message: 'Too many requests from this IP',
  standardHeaders: true,
  legacyHeaders: false,
  handler: (req, res) => {
    logSecurityEvent('RATE_LIMIT_EXCEEDED', {
      ip: req.ip,
      path: req.path,
      timestamp: new Date()
    });
    res.status(429).json({ error: 'Too many requests' });
  }
});

// Strict rate limiting for sensitive endpoints
export const strictRateLimiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 5,
  skipSuccessfulRequests: true
});

// Security headers middleware
export const securityHeaders = helmet({
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      scriptSrc: ["'self'", "'unsafe-inline'", 'https://cdn.jsdelivr.net'],
      styleSrc: ["'self'", "'unsafe-inline'"],
      imgSrc: ["'self'", 'data:', 'https:'],
      connectSrc: ["'self'", 'wss://localhost:8000'],
      fontSrc: ["'self'"],
      objectSrc: ["'none'"],
      mediaSrc: ["'self'"],
      frameSrc: ["'none'"],
      sandbox: ['allow-forms', 'allow-scripts', 'allow-same-origin'],
      reportUri: '/api/security/csp-report'
    }
  },
  hsts: {
    maxAge: 31536000,
    includeSubDomains: true,
    preload: true
  }
});

// JWT authentication middleware
export const authenticate = async (req: Request, res: Response, next: NextFunction) => {
  try {
    const token = req.headers.authorization?.replace('Bearer ', '');

    if (!token) {
      return res.status(401).json({ error: 'Authentication required' });
    }

    // Verify token
    const decoded = jwt.verify(token, process.env.JWT_SECRET!, {
      algorithms: ['HS256'],
      issuer: 'strategy-lab',
      audience: 'strategy-lab-api'
    }) as JWTPayload;

    // Check if token is blacklisted
    if (await isTokenBlacklisted(token)) {
      return res.status(401).json({ error: 'Token revoked' });
    }

    // Validate user still exists and is active
    const user = await User.findById(decoded.userId);
    if (!user || !user.isActive) {
      return res.status(401).json({ error: 'Invalid user' });
    }

    req.user = user;
    req.token = token;

    next();
  } catch (error) {
    if (error.name === 'TokenExpiredError') {
      return res.status(401).json({ error: 'Token expired' });
    }

    logSecurityEvent('AUTH_FAILURE', {
      error: error.message,
      ip: req.ip,
      path: req.path
    });

    return res.status(401).json({ error: 'Authentication failed' });
  }
};

// Authorization middleware
export const authorize = (...permissions: string[]) => {
  return (req: Request, res: Response, next: NextFunction) => {
    if (!req.user) {
      return res.status(401).json({ error: 'Authentication required' });
    }

    const hasPermission = permissions.some(permission =>
      req.user.permissions.includes(permission) ||
      req.user.permissions.includes('admin')
    );

    if (!hasPermission) {
      logSecurityEvent('AUTHORIZATION_FAILURE', {
        userId: req.user.id,
        requiredPermissions: permissions,
        userPermissions: req.user.permissions,
        path: req.path
      });

      return res.status(403).json({ error: 'Insufficient permissions' });
    }

    next();
  };
};

// Input validation middleware
export const validateInput = (validations: any[]) => {
  return async (req: Request, res: Response, next: NextFunction) => {
    await Promise.all(validations.map(validation => validation.run(req)));

    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      logSecurityEvent('VALIDATION_FAILURE', {
        errors: errors.array(),
        ip: req.ip,
        path: req.path
      });

      return res.status(400).json({ errors: errors.array() });
    }

    next();
  };
};

// CSRF protection
export const csrfProtection = (req: Request, res: Response, next: NextFunction) => {
  if (['GET', 'HEAD', 'OPTIONS'].includes(req.method)) {
    return next();
  }

  const token = req.headers['x-csrf-token'] as string;
  const sessionToken = req.session?.csrfToken;

  if (!token || !sessionToken || !crypto.timingSafeEqual(
    Buffer.from(token),
    Buffer.from(sessionToken)
  )) {
    logSecurityEvent('CSRF_FAILURE', {
      ip: req.ip,
      path: req.path,
      method: req.method
    });

    return res.status(403).json({ error: 'Invalid CSRF token' });
  }

  next();
};

// SQL injection prevention
export const sanitizeSQL = (value: string): string => {
  // Basic SQL injection prevention
  return value
    .replace(/['";\\]/g, '')
    .replace(/--/g, '')
    .replace(/\/\*/g, '')
    .replace(/\*\//g, '')
    .replace(/xp_/gi, '')
    .replace(/sp_/gi, '');
};

// XSS prevention
export const sanitizeHTML = (value: string): string => {
  const map: Record<string, string> = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#x27;',
    '/': '&#x2F;'
  };

  return value.replace(/[&<>"'/]/g, (s) => map[s]);
};
```

### Audit Logging
```typescript
// lib/security/audit-logger.ts
interface AuditLog {
  id: string;
  timestamp: Date;
  userId?: string;
  action: string;
  resource: string;
  method: string;
  ip: string;
  userAgent: string;
  status: 'success' | 'failure';
  details?: any;
  risk: 'low' | 'medium' | 'high' | 'critical';
}

class AuditLogger {
  private queue: AuditLog[] = [];
  private flushInterval: NodeJS.Timeout;

  constructor() {
    // Flush logs every 10 seconds
    this.flushInterval = setInterval(() => {
      this.flush();
    }, 10000);
  }

  async log(entry: Omit<AuditLog, 'id' | 'timestamp'>): Promise<void> {
    const log: AuditLog = {
      ...entry,
      id: crypto.randomUUID(),
      timestamp: new Date()
    };

    this.queue.push(log);

    // Immediate flush for high-risk events
    if (log.risk === 'high' || log.risk === 'critical') {
      await this.flush();
    }
  }

  private async flush(): Promise<void> {
    if (this.queue.length === 0) return;

    const logs = [...this.queue];
    this.queue = [];

    try {
      // Write to database
      await AuditLogModel.insertMany(logs);

      // Send critical events to monitoring service
      const criticalLogs = logs.filter(log => log.risk === 'critical');
      if (criticalLogs.length > 0) {
        await this.notifySecurityTeam(criticalLogs);
      }

    } catch (error) {
      console.error('Failed to flush audit logs:', error);
      // Re-add logs to queue
      this.queue.unshift(...logs);
    }
  }

  private async notifySecurityTeam(logs: AuditLog[]): Promise<void> {
    // Send to monitoring service
    await fetch(process.env.SECURITY_WEBHOOK_URL!, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${process.env.SECURITY_WEBHOOK_TOKEN}`
      },
      body: JSON.stringify({
        alerts: logs.map(log => ({
          severity: 'critical',
          title: `Security Alert: ${log.action}`,
          description: `User ${log.userId} performed ${log.action} on ${log.resource}`,
          details: log.details,
          timestamp: log.timestamp
        }))
      })
    });
  }

  async query(filters: AuditLogFilters): Promise<AuditLog[]> {
    const query: any = {};

    if (filters.userId) query.userId = filters.userId;
    if (filters.action) query.action = filters.action;
    if (filters.risk) query.risk = filters.risk;
    if (filters.dateFrom || filters.dateTo) {
      query.timestamp = {};
      if (filters.dateFrom) query.timestamp.$gte = filters.dateFrom;
      if (filters.dateTo) query.timestamp.$lte = filters.dateTo;
    }

    return AuditLogModel.find(query)
      .sort({ timestamp: -1 })
      .limit(filters.limit || 1000)
      .exec();
  }
}

// Express middleware for audit logging
export const auditLog = (action: string, resource: string, risk: AuditLog['risk'] = 'low') => {
  return async (req: Request, res: Response, next: NextFunction) => {
    const startTime = Date.now();

    // Capture original end function
    const originalEnd = res.end;

    res.end = function(...args: any[]) {
      // Calculate response time
      const responseTime = Date.now() - startTime;

      // Log the request
      auditLogger.log({
        userId: req.user?.id,
        action,
        resource,
        method: req.method,
        ip: req.ip,
        userAgent: req.get('user-agent') || '',
        status: res.statusCode < 400 ? 'success' : 'failure',
        details: {
          path: req.path,
          query: req.query,
          responseTime,
          statusCode: res.statusCode
        },
        risk
      });

      // Call original end function
      originalEnd.apply(res, args);
    };

    next();
  };
};
```

### Data Encryption
```typescript
// lib/security/encryption.ts
import crypto from 'crypto';

class DataEncryption {
  private algorithm = 'aes-256-gcm';
  private keyDerivationIterations = 100000;

  // Derive encryption key from password
  private async deriveKey(password: string, salt: Buffer): Promise<Buffer> {
    return new Promise((resolve, reject) => {
      crypto.pbkdf2(password, salt, this.keyDerivationIterations, 32, 'sha256',
        (err, derivedKey) => {
          if (err) reject(err);
          else resolve(derivedKey);
        }
      );
    });
  }

  async encrypt(data: string, password: string): Promise<EncryptedData> {
    const salt = crypto.randomBytes(32);
    const key = await this.deriveKey(password, salt);
    const iv = crypto.randomBytes(16);

    const cipher = crypto.createCipheriv(this.algorithm, key, iv);

    const encrypted = Buffer.concat([
      cipher.update(data, 'utf8'),
      cipher.final()
    ]);

    const authTag = cipher.getAuthTag();

    return {
      encrypted: encrypted.toString('base64'),
      salt: salt.toString('base64'),
      iv: iv.toString('base64'),
      authTag: authTag.toString('base64'),
      algorithm: this.algorithm
    };
  }

  async decrypt(encryptedData: EncryptedData, password: string): Promise<string> {
    const salt = Buffer.from(encryptedData.salt, 'base64');
    const key = await this.deriveKey(password, salt);
    const iv = Buffer.from(encryptedData.iv, 'base64');
    const authTag = Buffer.from(encryptedData.authTag, 'base64');

    const decipher = crypto.createDecipheriv(this.algorithm, key, iv);
    decipher.setAuthTag(authTag);

    const decrypted = Buffer.concat([
      decipher.update(Buffer.from(encryptedData.encrypted, 'base64')),
      decipher.final()
    ]);

    return decrypted.toString('utf8');
  }

  // Hash sensitive data for storage
  hash(data: string): string {
    return crypto
      .createHash('sha256')
      .update(data)
      .digest('hex');
  }

  // Generate secure random tokens
  generateToken(length: number = 32): string {
    return crypto
      .randomBytes(length)
      .toString('base64')
      .replace(/[+/=]/g, '');
  }
}

// Database field encryption
export const encryptedField = (fieldName: string) => {
  return {
    type: String,
    get: function(this: any) {
      const encrypted = this.getDataValue(fieldName);
      if (!encrypted) return null;

      try {
        return encryption.decrypt(
          JSON.parse(encrypted),
          process.env.FIELD_ENCRYPTION_KEY!
        );
      } catch (error) {
        console.error('Decryption failed:', error);
        return null;
      }
    },
    set: function(this: any, value: string) {
      if (!value) {
        this.setDataValue(fieldName, null);
        return;
      }

      const encrypted = encryption.encrypt(
        value,
        process.env.FIELD_ENCRYPTION_KEY!
      );

      this.setDataValue(fieldName, JSON.stringify(encrypted));
    }
  };
};
```

### Security Configuration
```typescript
// next.config.js - Security Headers
module.exports = {
  async headers() {
    return [
      {
        source: '/:path*',
        headers: [
          {
            key: 'X-DNS-Prefetch-Control',
            value: 'on'
          },
          {
            key: 'Strict-Transport-Security',
            value: 'max-age=63072000; includeSubDomains; preload'
          },
          {
            key: 'X-Frame-Options',
            value: 'SAMEORIGIN'
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
            key: 'Referrer-Policy',
            value: 'strict-origin-when-cross-origin'
          },
          {
            key: 'Permissions-Policy',
            value: 'camera=(), microphone=(), geolocation=()'
          }
        ]
      }
    ];
  }
};

// Environment validation
const requiredEnvVars = [
  'JWT_SECRET',
  'SESSION_SECRET',
  'FIELD_ENCRYPTION_KEY',
  'STORAGE_ENCRYPTION_KEY',
  'DATABASE_URL',
  'SECURITY_WEBHOOK_URL'
];

requiredEnvVars.forEach(varName => {
  if (!process.env[varName]) {
    throw new Error(`Missing required environment variable: ${varName}`);
  }

  // Validate key strength
  if (varName.includes('SECRET') || varName.includes('KEY')) {
    if (process.env[varName]!.length < 32) {
      throw new Error(`${varName} must be at least 32 characters long`);
    }
  }
});
```

## UI/UX Considerations
- Clear security status indicators
- User-friendly error messages (without exposing details)
- Smooth authentication flow
- Password strength indicators
- Two-factor authentication setup
- Security event notifications

## Testing Requirements
1. Penetration testing
2. Authentication flow testing
3. Authorization boundary testing
4. Input validation testing
5. Encryption/decryption verification
6. Rate limiting effectiveness

## Dependencies
- UI_001: Next.js foundation
- UI_002: FastAPI backend
- UI_003: Database setup
- UI_005: Development workflow

## Story Points: 21

## Priority: Critical

## Implementation Notes
- Follow OWASP security guidelines
- Regular security audits
- Implement security monitoring
- Use proven cryptographic libraries
- Keep dependencies updated
