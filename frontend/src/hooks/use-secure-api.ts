import { useState, useCallback } from "react";
import { useAuth } from "@/lib/auth/auth-provider";
import { useAuditLog, SecurityEvents } from "@/lib/security/audit-logger";

interface SecureApiOptions {
  method?: "GET" | "POST" | "PUT" | "DELETE" | "PATCH";
  body?: any;
  headers?: Record<string, string>;
  timeout?: number;
  retries?: number;
  validateResponse?: (data: any) => boolean;
  auditAction?: string;
  auditResource?: string;
}

interface SecureApiResponse<T> {
  data: T | null;
  error: Error | null;
  loading: boolean;
}

// Input sanitization helpers
const sanitizeInput = (input: any): any => {
  if (typeof input === "string") {
    // Remove potential XSS vectors
    return input
      .replace(/<script[^>]*>.*?<\/script>/gi, "")
      .replace(/<iframe[^>]*>.*?<\/iframe>/gi, "")
      .replace(/javascript:/gi, "")
      .replace(/on\w+\s*=/gi, "");
  }

  if (Array.isArray(input)) {
    return input.map(sanitizeInput);
  }

  if (input && typeof input === "object") {
    const sanitized: any = {};
    for (const key in input) {
      if (input.hasOwnProperty(key)) {
        // Sanitize key and value
        const sanitizedKey = sanitizeInput(key);
        sanitized[sanitizedKey] = sanitizeInput(input[key]);
      }
    }
    return sanitized;
  }

  return input;
};

// CSRF token management
const getCSRFToken = async (): Promise<string> => {
  const metaTag = document.querySelector<HTMLMetaElement>(
    'meta[name="csrf-token"]'
  );
  if (metaTag?.content) {
    return metaTag.content;
  }

  // Generate a new CSRF token if not found
  const response = await fetch("/api/auth/csrf-token");
  if (response.ok) {
    const { token } = await response.json();

    // Store in meta tag for future use
    const meta = document.createElement("meta");
    meta.name = "csrf-token";
    meta.content = token;
    document.head.appendChild(meta);

    return token;
  }

  throw new Error("Failed to obtain CSRF token");
};

export function useSecureApi<T = any>() {
  const { token, refreshToken } = useAuth();
  const { logAction } = useAuditLog();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const request = useCallback(
    async (
      url: string,
      options: SecureApiOptions = {}
    ): Promise<SecureApiResponse<T>> => {
      setLoading(true);
      setError(null);

      const {
        method = "GET",
        body,
        headers = {},
        timeout = 30000,
        retries = 3,
        validateResponse,
        auditAction,
        auditResource,
      } = options;

      let attempt = 0;

      while (attempt < retries) {
        try {
          // Get CSRF token for state-changing requests
          let csrfToken: string | undefined;
          if (["POST", "PUT", "DELETE", "PATCH"].includes(method)) {
            csrfToken = await getCSRFToken();
          }

          // Sanitize request body
          const sanitizedBody = body ? sanitizeInput(body) : undefined;

          // Build headers
          const requestHeaders: Record<string, string> = {
            "Content-Type": "application/json",
            ...headers,
          };

          if (token) {
            requestHeaders["Authorization"] = `Bearer ${token}`;
          }

          if (csrfToken) {
            requestHeaders["X-CSRF-Token"] = csrfToken;
          }

          // Create abort controller for timeout
          const controller = new AbortController();
          const timeoutId = setTimeout(() => controller.abort(), timeout);

          // Make request
          const response = await fetch(url, {
            method,
            headers: requestHeaders,
            body: sanitizedBody ? JSON.stringify(sanitizedBody) : undefined,
            signal: controller.signal,
            credentials: "same-origin",
          });

          clearTimeout(timeoutId);

          // Handle token refresh
          if (response.status === 401 && attempt === 0) {
            await refreshToken();
            attempt++;
            continue;
          }

          // Check response status
          if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(
              errorData.message ||
                `Request failed with status ${response.status}`
            );
          }

          // Parse response
          const data = await response.json();

          // Validate response if validator provided
          if (validateResponse && !validateResponse(data)) {
            throw new Error("Response validation failed");
          }

          // Log successful action
          if (auditAction && auditResource) {
            await logAction(auditAction, auditResource, "success", {
              method,
              url,
            });
          }

          setLoading(false);
          return { data, error: null, loading: false };
        } catch (err: any) {
          attempt++;

          // Don't retry on client errors
          if (err.name === "AbortError" || err.message.includes("4")) {
            break;
          }

          // Log failed action on last attempt
          if (attempt === retries && auditAction && auditResource) {
            await logAction(
              auditAction,
              auditResource,
              "failure",
              { method, url, error: err.message },
              "medium"
            );
          }

          // Wait before retry with exponential backoff
          if (attempt < retries) {
            await new Promise((resolve) =>
              setTimeout(resolve, Math.pow(2, attempt) * 1000)
            );
          }
        }
      }

      // All attempts failed
      const finalError = new Error(`Request failed after ${retries} attempts`);
      setError(finalError);
      setLoading(false);

      return { data: null, error: finalError, loading: false };
    },
    [token, refreshToken, logAction]
  );

  // Convenience methods
  const get = useCallback(
    (url: string, options?: Omit<SecureApiOptions, "method">) => {
      return request(url, { ...options, method: "GET" });
    },
    [request]
  );

  const post = useCallback(
    (
      url: string,
      body?: any,
      options?: Omit<SecureApiOptions, "method" | "body">
    ) => {
      return request(url, { ...options, method: "POST", body });
    },
    [request]
  );

  const put = useCallback(
    (
      url: string,
      body?: any,
      options?: Omit<SecureApiOptions, "method" | "body">
    ) => {
      return request(url, { ...options, method: "PUT", body });
    },
    [request]
  );

  const del = useCallback(
    (url: string, options?: Omit<SecureApiOptions, "method">) => {
      return request(url, { ...options, method: "DELETE" });
    },
    [request]
  );

  const patch = useCallback(
    (
      url: string,
      body?: any,
      options?: Omit<SecureApiOptions, "method" | "body">
    ) => {
      return request(url, { ...options, method: "PATCH", body });
    },
    [request]
  );

  return {
    request,
    get,
    post,
    put,
    delete: del,
    patch,
    loading,
    error,
  };
}

// Hook for downloading files securely
export function useSecureDownload() {
  const { token } = useAuth();
  const { logAction } = useAuditLog();
  const [downloading, setDownloading] = useState(false);

  const download = useCallback(
    async (url: string, filename?: string, auditResource?: string) => {
      setDownloading(true);

      try {
        const response = await fetch(url, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        if (!response.ok) {
          throw new Error(`Download failed with status ${response.status}`);
        }

        const blob = await response.blob();
        const downloadUrl = window.URL.createObjectURL(blob);

        const a = document.createElement("a");
        a.href = downloadUrl;
        a.download = filename || "download";
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);

        window.URL.revokeObjectURL(downloadUrl);

        // Log download
        if (auditResource) {
          await logAction(
            SecurityEvents.DATA_ACCESS,
            auditResource,
            "success",
            { action: "download", filename }
          );
        }
      } catch (error: any) {
        console.error("Download failed:", error);

        if (auditResource) {
          await logAction(
            SecurityEvents.DATA_ACCESS,
            auditResource,
            "failure",
            { action: "download", error: error.message },
            "medium"
          );
        }

        throw error;
      } finally {
        setDownloading(false);
      }
    },
    [token, logAction]
  );

  return { download, downloading };
}
