"use client";

import {
  createContext,
  useContext,
  useState,
  useCallback,
  useEffect,
  useRef,
  ReactNode,
} from "react";

type AriaLiveLevel = "polite" | "assertive";

interface AriaLiveContextValue {
  announce: (message: string, level?: AriaLiveLevel) => void;
  announceError: (message: string) => void;
  announceSuccess: (message: string) => void;
}

const AriaLiveContext = createContext<AriaLiveContextValue | null>(null);

interface AriaLiveProviderProps {
  children: ReactNode;
}

export function AriaLiveProvider({ children }: AriaLiveProviderProps) {
  const [announcements, setAnnouncements] = useState<
    {
      id: number;
      message: string;
      level: AriaLiveLevel;
    }[]
  >([]);

  const announce = useCallback(
    (message: string, level: AriaLiveLevel = "polite") => {
      const id = Date.now();
      setAnnouncements((prev) => [...prev, { id, message, level }]);

      // Remove announcement after 1 second to clear the live region
      setTimeout(() => {
        setAnnouncements((prev) => prev.filter((a) => a.id !== id));
      }, 1000);
    },
    []
  );

  const announceError = useCallback(
    (message: string) => {
      announce(`Error: ${message}`, "assertive");
    },
    [announce]
  );

  const announceSuccess = useCallback(
    (message: string) => {
      announce(`Success: ${message}`, "polite");
    },
    [announce]
  );

  return (
    <AriaLiveContext.Provider
      value={{ announce, announceError, announceSuccess }}
    >
      {children}

      {/* Polite announcements */}
      <div
        role="status"
        aria-live="polite"
        aria-atomic="true"
        className="sr-only"
      >
        {announcements
          .filter((a) => a.level === "polite")
          .map((a) => a.message)
          .join(". ")}
      </div>

      {/* Assertive announcements */}
      <div
        role="alert"
        aria-live="assertive"
        aria-atomic="true"
        className="sr-only"
      >
        {announcements
          .filter((a) => a.level === "assertive")
          .map((a) => a.message)
          .join(". ")}
      </div>
    </AriaLiveContext.Provider>
  );
}

export function useAriaLive() {
  const context = useContext(AriaLiveContext);
  if (!context) {
    throw new Error("useAriaLive must be used within AriaLiveProvider");
  }
  return context;
}

// Utility component for inline announcements
interface AriaLiveAnnouncementProps {
  message: string;
  level?: AriaLiveLevel;
  delay?: number;
}

export function AriaLiveAnnouncement({
  message,
  level = "polite",
  delay = 0,
}: AriaLiveAnnouncementProps) {
  const { announce } = useAriaLive();

  useEffect(() => {
    if (message) {
      const timer = setTimeout(() => {
        announce(message, level);
      }, delay);
      return () => clearTimeout(timer);
    }
  }, [message, level, delay, announce]);

  return null;
}

// Loading state announcer
interface LoadingAnnouncerProps {
  isLoading: boolean;
  loadingMessage?: string;
  completeMessage?: string;
  errorMessage?: string;
  hasError?: boolean;
}

export function LoadingAnnouncer({
  isLoading,
  loadingMessage = "Loading content",
  completeMessage = "Content loaded",
  errorMessage = "Failed to load content",
  hasError = false,
}: LoadingAnnouncerProps) {
  const { announce, announceError } = useAriaLive();
  const wasLoadingRef = useRef(false);

  useEffect(() => {
    if (isLoading && !wasLoadingRef.current) {
      announce(loadingMessage);
      wasLoadingRef.current = true;
    } else if (!isLoading && wasLoadingRef.current) {
      if (hasError) {
        announceError(errorMessage);
      } else {
        announce(completeMessage);
      }
      wasLoadingRef.current = false;
    }
  }, [
    isLoading,
    hasError,
    loadingMessage,
    completeMessage,
    errorMessage,
    announce,
    announceError,
  ]);

  return null;
}

// Form validation announcer
interface ValidationAnnouncerProps {
  errors: Record<string, string | string[]>;
  touched: Record<string, boolean>;
}

export function ValidationAnnouncer({
  errors,
  touched,
}: ValidationAnnouncerProps) {
  const { announceError } = useAriaLive();
  const previousErrorsRef = useRef<Record<string, string | string[]>>({});

  useEffect(() => {
    const newErrors = Object.entries(errors)
      .filter(
        ([field, error]) =>
          touched[field] && error && !previousErrorsRef.current[field]
      )
      .map(([field, error]) => {
        const errorMessage = Array.isArray(error) ? error[0] : error;
        return `${field}: ${errorMessage}`;
      });

    if (newErrors.length > 0) {
      announceError(newErrors.join(". "));
    }

    previousErrorsRef.current = { ...errors };
  }, [errors, touched, announceError]);

  return null;
}
