import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

// Security headers configuration
const securityHeaders = {
  "X-DNS-Prefetch-Control": "on",
  "Strict-Transport-Security": "max-age=63072000; includeSubDomains; preload",
  "X-Frame-Options": "SAMEORIGIN",
  "X-Content-Type-Options": "nosniff",
  "X-XSS-Protection": "1; mode=block",
  "Referrer-Policy": "strict-origin-when-cross-origin",
  "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
};

// CSP configuration
const cspDirectives = {
  "default-src": ["'self'"],
  "script-src": ["'self'", "'unsafe-inline'", "https://cdn.jsdelivr.net"],
  "style-src": ["'self'", "'unsafe-inline'"],
  "img-src": ["'self'", "data:", "https:"],
  "connect-src": [
    "'self'",
    "https://lab.m4s8.dev",
    "wss://lab.m4s8.dev",
    "ws://lab.m4s8.dev",
    "http://localhost:8000",
    "http://localhost:8001",
    "ws://localhost:8000",
    "ws://localhost:8001",
  ],
  "font-src": ["'self'"],
  "object-src": ["'none'"],
  "media-src": ["'self'"],
  "frame-src": ["'none'"],
  "base-uri": ["'self'"],
  "form-action": ["'self'"],
  "frame-ancestors": ["'none'"],
  "upgrade-insecure-requests": [],
};

// Rate limiting configuration
const rateLimitMap = new Map<string, { count: number; resetTime: number }>();
const RATE_LIMIT_WINDOW = 60 * 1000; // 1 minute
const RATE_LIMIT_MAX_REQUESTS = 100;

// Protected routes that require authentication
const protectedRoutes = [
  "/dashboard",
  "/strategies",
  "/backtesting",
  "/optimization",
  "/execution",
  "/data",
  "/settings",
  "/admin",
];

// Admin routes that require admin permissions
const adminRoutes = ["/admin", "/security"];

export function middleware(request: NextRequest) {
  const response = NextResponse.next();
  const pathname = request.nextUrl.pathname;

  // Apply security headers
  Object.entries(securityHeaders).forEach(([key, value]) => {
    response.headers.set(key, value);
  });

  // Build and apply CSP header
  const csp = Object.entries(cspDirectives)
    .map(([directive, sources]) => {
      if (sources.length === 0) return directive;
      return `${directive} ${sources.join(" ")}`;
    })
    .join("; ");
  response.headers.set("Content-Security-Policy", csp);

  // Rate limiting
  const clientIp =
    request.ip || request.headers.get("x-forwarded-for") || "unknown";
  const now = Date.now();
  const clientData = rateLimitMap.get(clientIp) || {
    count: 0,
    resetTime: now + RATE_LIMIT_WINDOW,
  };

  if (now > clientData.resetTime) {
    clientData.count = 0;
    clientData.resetTime = now + RATE_LIMIT_WINDOW;
  }

  clientData.count++;
  rateLimitMap.set(clientIp, clientData);

  // Clean up old entries periodically
  if (Math.random() < 0.01) {
    for (const [ip, data] of rateLimitMap.entries()) {
      if (now > data.resetTime + RATE_LIMIT_WINDOW) {
        rateLimitMap.delete(ip);
      }
    }
  }

  if (clientData.count > RATE_LIMIT_MAX_REQUESTS) {
    return new NextResponse("Too Many Requests", {
      status: 429,
      headers: {
        "Retry-After": String(Math.ceil((clientData.resetTime - now) / 1000)),
        "X-RateLimit-Limit": String(RATE_LIMIT_MAX_REQUESTS),
        "X-RateLimit-Remaining": "0",
        "X-RateLimit-Reset": String(clientData.resetTime),
      },
    });
  }

  // Add rate limit headers
  response.headers.set("X-RateLimit-Limit", String(RATE_LIMIT_MAX_REQUESTS));
  response.headers.set(
    "X-RateLimit-Remaining",
    String(Math.max(0, RATE_LIMIT_MAX_REQUESTS - clientData.count))
  );
  response.headers.set("X-RateLimit-Reset", String(clientData.resetTime));

  // Check authentication for protected routes
  const isProtectedRoute = protectedRoutes.some((route) =>
    pathname.startsWith(route)
  );
  const isAdminRoute = adminRoutes.some((route) => pathname.startsWith(route));
  const isAuthRoute = pathname.startsWith("/auth");

  if (isProtectedRoute || isAdminRoute) {
    const token = request.cookies.get("authToken")?.value;

    if (!token) {
      // Redirect to login if no token
      const loginUrl = new URL("/auth/login", request.url);
      loginUrl.searchParams.set("redirect", pathname);
      return NextResponse.redirect(loginUrl);
    }

    // Validate token structure (basic check)
    try {
      const parts = token.split(".");
      if (parts.length !== 3) {
        throw new Error("Invalid token format");
      }

      // Decode token payload (Edge runtime compatible)
      const payload = JSON.parse(atob(parts[1]));

      // Check token expiration
      if (payload.exp && payload.exp * 1000 < Date.now()) {
        throw new Error("Token expired");
      }

      // Check admin permission for admin routes
      if (isAdminRoute) {
        const permissions = payload.permissions || [];
        const hasAdminPermission =
          permissions.includes("admin") ||
          permissions.some((p: any) => p.name === "admin");

        if (!hasAdminPermission) {
          return new NextResponse("Forbidden", { status: 403 });
        }
      }
    } catch (error) {
      // Invalid or expired token, redirect to login
      const loginUrl = new URL("/auth/login", request.url);
      loginUrl.searchParams.set("redirect", pathname);

      // Clear invalid token
      response.cookies.delete("authToken");

      return NextResponse.redirect(loginUrl);
    }
  }

  // Redirect authenticated users away from auth routes
  if (isAuthRoute && request.cookies.get("authToken")?.value) {
    return NextResponse.redirect(new URL("/dashboard", request.url));
  }

  return response;
}

export const config = {
  matcher: [
    // Temporarily disabled due to Edge runtime compatibility issues
    // '/((?!api|_next/static|_next/image|favicon.ico|public).*)',
  ],
};
