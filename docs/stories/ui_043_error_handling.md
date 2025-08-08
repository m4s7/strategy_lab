# UI_043: Error Handling & Recovery

## Story Details
- **Story ID**: UI_043
- **Status**: Done

## Story
As a trader, I want the application to handle errors gracefully and recover automatically when possible so that my trading analysis workflow is not disrupted by technical issues.

## Acceptance Criteria
1. Implement global error boundary for React components
2. Add retry logic for failed API requests
3. Create user-friendly error messages
4. Implement offline mode with data synchronization
5. Add error tracking and monitoring
6. Provide recovery actions for common errors
7. Save application state for crash recovery
8. Show detailed error logs for debugging

## Technical Requirements

### Global Error Handling
```typescript
// components/error/ErrorBoundary.tsx
import { Component, ErrorInfo, ReactNode } from 'react';
import * as Sentry from '@sentry/nextjs';

interface Props {
  children: ReactNode;
  fallback?: (error: Error, reset: () => void) => ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
  errorId: string | null;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      errorId: null
    };
  }

  static getDerivedStateFromError(error: Error): State {
    return {
      hasError: true,
      error,
      errorInfo: null,
      errorId: Date.now().toString()
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    // Log to error tracking service
    const errorId = this.state.errorId || Date.now().toString();

    Sentry.withScope((scope) => {
      scope.setTag('errorBoundary', true);
      scope.setContext('errorInfo', errorInfo);
      scope.setLevel('error');
      const eventId = Sentry.captureException(error);

      this.setState({
        errorInfo,
        errorId: eventId
      });
    });

    // Log to local storage for debugging
    this.logErrorLocally(error, errorInfo);

    // Save application state for recovery
    this.saveApplicationState();
  }

  private logErrorLocally(error: Error, errorInfo: ErrorInfo) {
    const errorLog = {
      id: this.state.errorId,
      timestamp: new Date().toISOString(),
      error: {
        message: error.message,
        stack: error.stack,
        name: error.name
      },
      errorInfo: {
        componentStack: errorInfo.componentStack
      },
      userAgent: navigator.userAgent,
      url: window.location.href
    };

    // Store in IndexedDB for persistence
    ErrorStorage.addError(errorLog);
  }

  private saveApplicationState() {
    try {
      // Save current application state
      const state = {
        route: window.location.pathname,
        scrollPosition: window.scrollY,
        formData: this.captureFormData(),
        timestamp: Date.now()
      };

      localStorage.setItem('app_recovery_state', JSON.stringify(state));
    } catch (e) {
      console.error('Failed to save recovery state:', e);
    }
  }

  private captureFormData(): Record<string, any> {
    const formData: Record<string, any> = {};
    const inputs = document.querySelectorAll('input, textarea, select');

    inputs.forEach((input: Element) => {
      if (input instanceof HTMLInputElement ||
          input instanceof HTMLTextAreaElement ||
          input instanceof HTMLSelectElement) {
        if (input.name && input.value) {
          formData[input.name] = input.value;
        }
      }
    });

    return formData;
  }

  private reset = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
      errorId: null
    });
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback(this.state.error!, this.reset);
      }

      return (
        <ErrorFallback
          error={this.state.error!}
          errorId={this.state.errorId!}
          reset={this.reset}
        />
      );
    }

    return this.props.children;
  }
}

// Default error fallback component
function ErrorFallback({ error, errorId, reset }: ErrorFallbackProps) {
  const [showDetails, setShowDetails] = useState(false);
  const [reportSent, setReportSent] = useState(false);

  const sendReport = async () => {
    try {
      await fetch('/api/errors/report', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          errorId,
          userDescription: document.getElementById('error-description')?.value,
          contactEmail: document.getElementById('contact-email')?.value
        })
      });
      setReportSent(true);
    } catch (e) {
      console.error('Failed to send error report:', e);
    }
  };

  return (
    <div className="error-fallback min-h-screen flex items-center justify-center p-4">
      <Card className="max-w-2xl w-full">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <AlertCircle className="h-6 w-6 text-red-500" />
            Something went wrong
          </CardTitle>
          <CardDescription>
            Error ID: {errorId}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-sm text-muted-foreground">
            We've encountered an unexpected error. The error has been logged and our team has been notified.
          </p>

          <div className="flex gap-2">
            <Button onClick={reset} variant="default">
              Try Again
            </Button>
            <Button onClick={() => window.location.href = '/'} variant="outline">
              Go to Dashboard
            </Button>
            <Button
              onClick={() => setShowDetails(!showDetails)}
              variant="ghost"
            >
              {showDetails ? 'Hide' : 'Show'} Details
            </Button>
          </div>

          {showDetails && (
            <div className="space-y-4">
              <Alert>
                <AlertTitle>Error Details</AlertTitle>
                <AlertDescription>
                  <pre className="text-xs overflow-auto max-h-40">
                    {error.stack || error.message}
                  </pre>
                </AlertDescription>
              </Alert>

              {!reportSent ? (
                <div className="space-y-2">
                  <Label>Help us improve by describing what you were doing:</Label>
                  <Textarea
                    id="error-description"
                    placeholder="I was trying to..."
                    rows={3}
                  />
                  <Input
                    id="contact-email"
                    type="email"
                    placeholder="Contact email (optional)"
                  />
                  <Button onClick={sendReport} size="sm">
                    Send Report
                  </Button>
                </div>
              ) : (
                <Alert>
                  <CheckCircle className="h-4 w-4" />
                  <AlertDescription>
                    Thank you for your feedback!
                  </AlertDescription>
                </Alert>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
```

### API Error Handling with Retry
```typescript
// lib/api/error-handler.ts
import { AxiosError, AxiosInstance, AxiosRequestConfig } from 'axios';
import axiosRetry from 'axios-retry';

interface RetryConfig {
  retries?: number;
  retryDelay?: (retryCount: number) => number;
  retryCondition?: (error: AxiosError) => boolean;
}

class APIErrorHandler {
  private axios: AxiosInstance;
  private offlineQueue: QueuedRequest[] = [];
  private isOnline: boolean = navigator.onLine;

  constructor(baseURL: string, retryConfig: RetryConfig = {}) {
    this.axios = axios.create({ baseURL });

    // Configure retry logic
    axiosRetry(this.axios, {
      retries: retryConfig.retries || 3,
      retryDelay: retryConfig.retryDelay || axiosRetry.exponentialDelay,
      retryCondition: retryConfig.retryCondition || this.shouldRetry,
      onRetry: this.onRetry
    });

    // Add request/response interceptors
    this.setupInterceptors();

    // Monitor online status
    this.setupOnlineMonitoring();
  }

  private shouldRetry = (error: AxiosError): boolean => {
    // Retry on network errors
    if (!error.response) return true;

    // Retry on 5xx errors
    if (error.response.status >= 500) return true;

    // Retry on specific 4xx errors
    if ([408, 429].includes(error.response.status)) return true;

    // Don't retry on client errors
    return false;
  };

  private onRetry = (retryCount: number, error: AxiosError) => {
    console.log(`Retry attempt ${retryCount} for ${error.config?.url}`);

    // Track retry metrics
    this.trackRetryMetric(error, retryCount);
  };

  private setupInterceptors() {
    // Request interceptor
    this.axios.interceptors.request.use(
      (config) => {
        // Add request timestamp for timeout tracking
        config.metadata = { startTime: Date.now() };

        // Add correlation ID for request tracking
        config.headers['X-Correlation-ID'] = this.generateCorrelationId();

        return config;
      },
      (error) => {
        return Promise.reject(this.transformError(error));
      }
    );

    // Response interceptor
    this.axios.interceptors.response.use(
      (response) => {
        // Track response time
        const duration = Date.now() - response.config.metadata.startTime;
        this.trackResponseTime(response.config.url!, duration);

        return response;
      },
      async (error) => {
        // Handle offline scenario
        if (!navigator.onLine && this.isRetriableRequest(error.config)) {
          return this.queueOfflineRequest(error.config);
        }

        // Transform error for consistent handling
        const transformedError = this.transformError(error);

        // Show user notification for certain errors
        this.notifyUser(transformedError);

        return Promise.reject(transformedError);
      }
    );
  }

  private transformError(error: AxiosError): ApplicationError {
    const appError = new ApplicationError(
      error.message,
      error.response?.status || 0,
      error.response?.data
    );

    // Add context based on error type
    if (!error.response) {
      appError.type = 'NETWORK_ERROR';
      appError.userMessage = 'Connection failed. Please check your internet connection.';
    } else if (error.response.status === 401) {
      appError.type = 'AUTH_ERROR';
      appError.userMessage = 'Your session has expired. Please log in again.';
    } else if (error.response.status === 403) {
      appError.type = 'PERMISSION_ERROR';
      appError.userMessage = 'You don\'t have permission to perform this action.';
    } else if (error.response.status === 429) {
      appError.type = 'RATE_LIMIT_ERROR';
      appError.userMessage = 'Too many requests. Please try again later.';
    } else if (error.response.status >= 500) {
      appError.type = 'SERVER_ERROR';
      appError.userMessage = 'Server error. We\'re working on fixing this.';
    }

    return appError;
  }

  private notifyUser(error: ApplicationError) {
    // Don't notify for certain error types
    if (['NETWORK_ERROR', 'AUTH_ERROR'].includes(error.type)) return;

    // Show toast notification
    toast({
      title: 'Error',
      description: error.userMessage || 'An unexpected error occurred',
      variant: 'destructive',
      action: error.type === 'SERVER_ERROR' ? (
        <ToastAction altText="Retry" onClick={() => window.location.reload()}>
          Retry
        </ToastAction>
      ) : undefined
    });
  }

  private setupOnlineMonitoring() {
    window.addEventListener('online', () => {
      this.isOnline = true;
      this.processOfflineQueue();
    });

    window.addEventListener('offline', () => {
      this.isOnline = false;
      toast({
        title: 'Offline Mode',
        description: 'You\'re working offline. Changes will sync when connection is restored.',
        variant: 'warning'
      });
    });
  }

  private async queueOfflineRequest(config: AxiosRequestConfig): Promise<any> {
    const queuedRequest: QueuedRequest = {
      id: this.generateCorrelationId(),
      config,
      timestamp: Date.now()
    };

    this.offlineQueue.push(queuedRequest);

    // Store in IndexedDB for persistence
    await OfflineStorage.saveRequest(queuedRequest);

    // Return optimistic response for certain requests
    if (this.canReturnOptimisticResponse(config)) {
      return this.generateOptimisticResponse(config);
    }

    throw new ApplicationError(
      'Request queued for offline sync',
      0,
      { queued: true, requestId: queuedRequest.id }
    );
  }

  private async processOfflineQueue() {
    const queue = [...this.offlineQueue];
    this.offlineQueue = [];

    for (const request of queue) {
      try {
        await this.axios.request(request.config);
        await OfflineStorage.removeRequest(request.id);
      } catch (error) {
        // Re-queue failed requests
        this.offlineQueue.push(request);
      }
    }

    if (queue.length > 0) {
      toast({
        title: 'Sync Complete',
        description: `${queue.length - this.offlineQueue.length} changes synchronized`,
        variant: 'success'
      });
    }
  }
}

// Custom error class
class ApplicationError extends Error {
  type: string = 'UNKNOWN_ERROR';
  statusCode: number;
  details: any;
  userMessage?: string;

  constructor(message: string, statusCode: number = 0, details?: any) {
    super(message);
    this.name = 'ApplicationError';
    this.statusCode = statusCode;
    this.details = details;
  }
}
```

### Error Recovery Strategies
```typescript
// lib/error/recovery-manager.ts
interface RecoveryStrategy {
  canRecover(error: ApplicationError): boolean;
  recover(error: ApplicationError): Promise<void>;
}

class RecoveryManager {
  private strategies: RecoveryStrategy[] = [];

  constructor() {
    this.registerDefaultStrategies();
  }

  private registerDefaultStrategies() {
    // Auth error recovery
    this.strategies.push({
      canRecover: (error) => error.type === 'AUTH_ERROR',
      recover: async (error) => {
        try {
          // Try to refresh token
          await authService.refreshToken();

          // Retry original request
          if (error.details?.originalRequest) {
            return await axios.request(error.details.originalRequest);
          }
        } catch (e) {
          // Refresh failed, redirect to login
          window.location.href = '/login?redirect=' + encodeURIComponent(window.location.pathname);
        }
      }
    });

    // Connection error recovery
    this.strategies.push({
      canRecover: (error) => error.type === 'NETWORK_ERROR',
      recover: async (error) => {
        // Wait for connection
        await this.waitForConnection();

        // Retry request
        if (error.details?.originalRequest) {
          return await axios.request(error.details.originalRequest);
        }
      }
    });

    // State corruption recovery
    this.strategies.push({
      canRecover: (error) => error.type === 'STATE_ERROR',
      recover: async (error) => {
        // Clear corrupted state
        localStorage.removeItem('app_state');
        sessionStorage.clear();

        // Reload application
        window.location.reload();
      }
    });
  }

  async attemptRecovery(error: ApplicationError): Promise<boolean> {
    for (const strategy of this.strategies) {
      if (strategy.canRecover(error)) {
        try {
          await strategy.recover(error);
          return true;
        } catch (recoveryError) {
          console.error('Recovery failed:', recoveryError);
        }
      }
    }

    return false;
  }

  private waitForConnection(timeout: number = 30000): Promise<void> {
    return new Promise((resolve, reject) => {
      if (navigator.onLine) {
        resolve();
        return;
      }

      const timer = setTimeout(() => {
        reject(new Error('Connection timeout'));
      }, timeout);

      const handleOnline = () => {
        clearTimeout(timer);
        window.removeEventListener('online', handleOnline);
        resolve();
      };

      window.addEventListener('online', handleOnline);
    });
  }
}

// React hook for error recovery
export function useErrorRecovery() {
  const [isRecovering, setIsRecovering] = useState(false);
  const recoveryManager = useMemo(() => new RecoveryManager(), []);

  const recoverFromError = useCallback(async (error: ApplicationError) => {
    setIsRecovering(true);

    try {
      const recovered = await recoveryManager.attemptRecovery(error);

      if (recovered) {
        toast({
          title: 'Recovery Successful',
          description: 'The issue has been resolved automatically.',
          variant: 'success'
        });
      }

      return recovered;
    } finally {
      setIsRecovering(false);
    }
  }, [recoveryManager]);

  return { recoverFromError, isRecovering };
}
```

### Error Logging and Monitoring
```typescript
// lib/error/error-logger.ts
import * as Sentry from '@sentry/nextjs';

interface ErrorLog {
  id: string;
  timestamp: Date;
  level: 'error' | 'warning' | 'info';
  message: string;
  stack?: string;
  context: Record<string, any>;
  user?: {
    id: string;
    email: string;
  };
  session: {
    id: string;
    duration: number;
  };
  device: {
    userAgent: string;
    viewport: { width: number; height: number };
    screen: { width: number; height: number };
  };
}

class ErrorLogger {
  private buffer: ErrorLog[] = [];
  private flushInterval: number = 5000;
  private maxBufferSize: number = 50;

  constructor() {
    // Flush buffer periodically
    setInterval(() => this.flush(), this.flushInterval);

    // Listen for unhandled errors
    this.setupGlobalHandlers();
  }

  private setupGlobalHandlers() {
    // Unhandled promise rejections
    window.addEventListener('unhandledrejection', (event) => {
      this.logError('Unhandled Promise Rejection', event.reason, {
        promise: event.promise,
        type: 'unhandledRejection'
      });
    });

    // Global errors
    window.addEventListener('error', (event) => {
      this.logError('Global Error', event.error || event.message, {
        filename: event.filename,
        lineno: event.lineno,
        colno: event.colno,
        type: 'globalError'
      });
    });

    // Console errors
    const originalError = console.error;
    console.error = (...args) => {
      this.logError('Console Error', args.join(' '), {
        type: 'consoleError',
        args
      });
      originalError.apply(console, args);
    };
  }

  logError(message: string, error?: any, context?: Record<string, any>) {
    const errorLog: ErrorLog = {
      id: this.generateId(),
      timestamp: new Date(),
      level: 'error',
      message,
      stack: error?.stack || new Error().stack,
      context: {
        ...context,
        url: window.location.href,
        referrer: document.referrer,
        ...this.captureErrorContext()
      },
      user: this.getCurrentUser(),
      session: this.getSessionInfo(),
      device: this.getDeviceInfo()
    };

    // Add to buffer
    this.buffer.push(errorLog);

    // Send to Sentry
    Sentry.captureException(error || new Error(message), {
      contexts: {
        custom: errorLog.context
      },
      level: 'error'
    });

    // Flush if buffer is full
    if (this.buffer.length >= this.maxBufferSize) {
      this.flush();
    }
  }

  private captureErrorContext(): Record<string, any> {
    return {
      timestamp: Date.now(),
      memory: this.getMemoryUsage(),
      connection: {
        type: (navigator as any).connection?.effectiveType,
        downlink: (navigator as any).connection?.downlink,
        rtt: (navigator as any).connection?.rtt
      },
      storage: {
        localStorage: this.getStorageUsage(localStorage),
        sessionStorage: this.getStorageUsage(sessionStorage)
      }
    };
  }

  private async flush() {
    if (this.buffer.length === 0) return;

    const logs = [...this.buffer];
    this.buffer = [];

    try {
      await fetch('/api/errors/log', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ logs })
      });

      // Store in IndexedDB as backup
      await ErrorStorage.saveLogs(logs);
    } catch (error) {
      // Re-add to buffer if send failed
      this.buffer.unshift(...logs);
    }
  }

  // Get error logs for debugging
  async getErrorLogs(filters?: {
    level?: string;
    startDate?: Date;
    endDate?: Date;
    limit?: number;
  }): Promise<ErrorLog[]> {
    return ErrorStorage.queryLogs(filters);
  }
}

// Error storage using IndexedDB
class ErrorStorage {
  private static dbName = 'ErrorLogs';
  private static storeName = 'logs';
  private static db: IDBDatabase | null = null;

  static async init() {
    return new Promise<void>((resolve, reject) => {
      const request = indexedDB.open(this.dbName, 1);

      request.onerror = () => reject(request.error);
      request.onsuccess = () => {
        this.db = request.result;
        resolve();
      };

      request.onupgradeneeded = (event) => {
        const db = (event.target as IDBOpenDBRequest).result;

        if (!db.objectStoreNames.contains(this.storeName)) {
          const store = db.createObjectStore(this.storeName, {
            keyPath: 'id'
          });

          store.createIndex('timestamp', 'timestamp', { unique: false });
          store.createIndex('level', 'level', { unique: false });
        }
      };
    });
  }

  static async saveLogs(logs: ErrorLog[]) {
    if (!this.db) await this.init();

    const transaction = this.db!.transaction([this.storeName], 'readwrite');
    const store = transaction.objectStore(this.storeName);

    for (const log of logs) {
      store.add(log);
    }

    return new Promise<void>((resolve, reject) => {
      transaction.oncomplete = () => resolve();
      transaction.onerror = () => reject(transaction.error);
    });
  }

  static async queryLogs(filters?: any): Promise<ErrorLog[]> {
    if (!this.db) await this.init();

    const transaction = this.db!.transaction([this.storeName], 'readonly');
    const store = transaction.objectStore(this.storeName);

    return new Promise((resolve, reject) => {
      const logs: ErrorLog[] = [];
      const request = store.openCursor();

      request.onsuccess = (event) => {
        const cursor = (event.target as IDBRequest).result;

        if (cursor) {
          const log = cursor.value;

          // Apply filters
          if (!filters || this.matchesFilters(log, filters)) {
            logs.push(log);
          }

          if (logs.length < (filters?.limit || 1000)) {
            cursor.continue();
          } else {
            resolve(logs);
          }
        } else {
          resolve(logs);
        }
      };

      request.onerror = () => reject(request.error);
    });
  }

  private static matchesFilters(log: ErrorLog, filters: any): boolean {
    if (filters.level && log.level !== filters.level) return false;
    if (filters.startDate && log.timestamp < filters.startDate) return false;
    if (filters.endDate && log.timestamp > filters.endDate) return false;

    return true;
  }
}
```

## UI/UX Considerations
- Clear error messages without technical jargon
- Actionable recovery options
- Progress indicators during recovery
- Offline mode indicators
- Error log viewer for power users
- Graceful degradation of features

## Testing Requirements
1. Error boundary testing
2. Retry logic verification
3. Offline mode functionality
4. Recovery strategy testing
5. Error logging accuracy
6. Performance impact measurement

## Dependencies
- UI_001: Next.js foundation
- UI_002: FastAPI backend
- UI_041: Performance optimization
- UI_042: Security hardening

## Story Points: 13

## Priority: High

## Implementation Notes
- Use Sentry for production error tracking
- Implement circuit breaker pattern
- Add error budget monitoring
- Consider graceful degradation strategies
- Test error scenarios thoroughly
