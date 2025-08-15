import { useState, useEffect } from "react";

// Breakpoint values
const breakpoints = {
  sm: 640,
  md: 768,
  lg: 1024,
  xl: 1280,
  "2xl": 1536,
  "4k": 2560,
} as const;

type Breakpoint = keyof typeof breakpoints;

// Hook to check if screen matches breakpoint
export function useBreakpoint(breakpoint: Breakpoint): boolean {
  const [matches, setMatches] = useState(false);

  useEffect(() => {
    const query = window.matchMedia(
      `(min-width: ${breakpoints[breakpoint]}px)`
    );
    setMatches(query.matches);

    const handler = (e: MediaQueryListEvent) => setMatches(e.matches);
    query.addEventListener("change", handler);
    return () => query.removeEventListener("change", handler);
  }, [breakpoint]);

  return matches;
}

// Hook to get current breakpoint
export function useCurrentBreakpoint(): Breakpoint | null {
  const [current, setCurrent] = useState<Breakpoint | null>(null);

  useEffect(() => {
    const updateBreakpoint = () => {
      const width = window.innerWidth;
      let currentBreakpoint: Breakpoint | null = null;

      // Find the largest breakpoint that matches
      for (const [key, value] of Object.entries(breakpoints)) {
        if (width >= value) {
          currentBreakpoint = key as Breakpoint;
        }
      }

      setCurrent(currentBreakpoint);
    };

    updateBreakpoint();
    window.addEventListener("resize", updateBreakpoint);
    return () => window.removeEventListener("resize", updateBreakpoint);
  }, []);

  return current;
}

// Hook for responsive values
export function useResponsive<T>(
  values: Partial<Record<Breakpoint | "default", T>>
): T | undefined {
  const current = useCurrentBreakpoint();

  // Start with default value
  let value = values.default;

  // Override with breakpoint-specific values
  if (current) {
    const breakpointKeys = Object.keys(breakpoints) as Breakpoint[];
    for (const breakpoint of breakpointKeys) {
      if (values[breakpoint] !== undefined) {
        value = values[breakpoint];
      }
      if (breakpoint === current) {
        break;
      }
    }
  }

  return value;
}

// Hook to detect mobile/tablet/desktop
export function useDeviceType() {
  const [deviceType, setDeviceType] = useState<"mobile" | "tablet" | "desktop">(
    "desktop"
  );

  useEffect(() => {
    const updateDeviceType = () => {
      const width = window.innerWidth;
      if (width < breakpoints.sm) {
        setDeviceType("mobile");
      } else if (width < breakpoints.lg) {
        setDeviceType("tablet");
      } else {
        setDeviceType("desktop");
      }
    };

    updateDeviceType();
    window.addEventListener("resize", updateDeviceType);
    return () => window.removeEventListener("resize", updateDeviceType);
  }, []);

  return deviceType;
}

// Hook for touch device detection
export function useIsTouchDevice(): boolean {
  const [isTouch, setIsTouch] = useState(false);

  useEffect(() => {
    const checkTouch = () => {
      setIsTouch(
        "ontouchstart" in window ||
          navigator.maxTouchPoints > 0 ||
          window.matchMedia("(pointer: coarse)").matches
      );
    };

    checkTouch();
  }, []);

  return isTouch;
}

// Hook for orientation
export function useOrientation(): "portrait" | "landscape" {
  const [orientation, setOrientation] = useState<"portrait" | "landscape">(
    window.innerHeight > window.innerWidth ? "portrait" : "landscape"
  );

  useEffect(() => {
    const updateOrientation = () => {
      setOrientation(
        window.innerHeight > window.innerWidth ? "portrait" : "landscape"
      );
    };

    window.addEventListener("resize", updateOrientation);
    window.addEventListener("orientationchange", updateOrientation);

    return () => {
      window.removeEventListener("resize", updateOrientation);
      window.removeEventListener("orientationchange", updateOrientation);
    };
  }, []);

  return orientation;
}

// Hook for viewport dimensions
export function useViewport() {
  const [viewport, setViewport] = useState({
    width: window.innerWidth,
    height: window.innerHeight,
    vw: window.innerWidth / 100,
    vh: window.innerHeight / 100,
  });

  useEffect(() => {
    const updateViewport = () => {
      setViewport({
        width: window.innerWidth,
        height: window.innerHeight,
        vw: window.innerWidth / 100,
        vh: window.innerHeight / 100,
      });
    };

    window.addEventListener("resize", updateViewport);
    return () => window.removeEventListener("resize", updateViewport);
  }, []);

  return viewport;
}

// Hook for container queries (with polyfill)
export function useContainerQuery(
  ref: React.RefObject<HTMLElement>,
  query: string
): boolean {
  const [matches, setMatches] = useState(false);

  useEffect(() => {
    if (!ref.current) return;

    // Check for native container query support
    if ("container" in document.documentElement.style) {
      // Native support - use ResizeObserver to simulate
      const observer = new ResizeObserver((entries) => {
        for (const entry of entries) {
          const width = entry.contentBoxSize[0].inlineSize;
          // Simple width-based query parsing (extends as needed)
          if (query.includes("min-width")) {
            const minWidth = parseInt(query.match(/(\d+)px/)?.[1] || "0");
            setMatches(width >= minWidth);
          }
        }
      });

      observer.observe(ref.current);
      return () => observer.disconnect();
    } else {
      // Fallback to window resize
      const checkQuery = () => {
        if (!ref.current) return;
        const width = ref.current.offsetWidth;
        if (query.includes("min-width")) {
          const minWidth = parseInt(query.match(/(\d+)px/)?.[1] || "0");
          setMatches(width >= minWidth);
        }
      };

      checkQuery();
      window.addEventListener("resize", checkQuery);
      return () => window.removeEventListener("resize", checkQuery);
    }
  }, [ref, query]);

  return matches;
}
