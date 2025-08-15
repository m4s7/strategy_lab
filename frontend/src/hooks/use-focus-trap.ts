import { useEffect, useRef, RefObject } from "react";

interface FocusTrapOptions {
  enabled?: boolean;
  initialFocus?: RefObject<HTMLElement>;
  returnFocus?: boolean;
  escapeDeactivates?: boolean;
  onDeactivate?: () => void;
}

export function useFocusTrap(
  containerRef: RefObject<HTMLElement>,
  options: FocusTrapOptions = {}
) {
  const {
    enabled = true,
    initialFocus,
    returnFocus = true,
    escapeDeactivates = true,
    onDeactivate,
  } = options;

  const previouslyFocusedElement = useRef<HTMLElement | null>(null);

  useEffect(() => {
    if (!enabled || !containerRef.current) return;

    const container = containerRef.current;
    previouslyFocusedElement.current = document.activeElement as HTMLElement;

    // Get all focusable elements
    const getFocusableElements = (): HTMLElement[] => {
      const selector = [
        "a[href]",
        "button:not([disabled])",
        "input:not([disabled])",
        "textarea:not([disabled])",
        "select:not([disabled])",
        '[tabindex]:not([tabindex="-1"])',
      ].join(",");

      return Array.from(container.querySelectorAll(selector)) as HTMLElement[];
    };

    // Set initial focus
    const setInitialFocus = () => {
      if (initialFocus?.current) {
        initialFocus.current.focus();
      } else {
        const focusableElements = getFocusableElements();
        if (focusableElements.length > 0) {
          focusableElements[0].focus();
        }
      }
    };

    // Handle tab key
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape" && escapeDeactivates) {
        onDeactivate?.();
        return;
      }

      if (event.key !== "Tab") return;

      const focusableElements = getFocusableElements();
      if (focusableElements.length === 0) return;

      const firstElement = focusableElements[0];
      const lastElement = focusableElements[focusableElements.length - 1];
      const currentElement = document.activeElement as HTMLElement;

      // Forward tab
      if (!event.shiftKey && currentElement === lastElement) {
        event.preventDefault();
        firstElement.focus();
      }
      // Backward tab
      else if (event.shiftKey && currentElement === firstElement) {
        event.preventDefault();
        lastElement.focus();
      }
    };

    // Handle focus leaving the container
    const handleFocusOut = (event: FocusEvent) => {
      const relatedTarget = event.relatedTarget as HTMLElement;

      // If focus is moving outside the container, bring it back
      if (relatedTarget && !container.contains(relatedTarget)) {
        setTimeout(() => {
          const focusableElements = getFocusableElements();
          if (focusableElements.length > 0) {
            focusableElements[0].focus();
          }
        }, 0);
      }
    };

    // Set up event listeners
    container.addEventListener("keydown", handleKeyDown);
    container.addEventListener("focusout", handleFocusOut);
    setInitialFocus();

    // Cleanup
    return () => {
      container.removeEventListener("keydown", handleKeyDown);
      container.removeEventListener("focusout", handleFocusOut);

      if (returnFocus && previouslyFocusedElement.current) {
        previouslyFocusedElement.current.focus();
      }
    };
  }, [
    enabled,
    containerRef,
    initialFocus,
    returnFocus,
    escapeDeactivates,
    onDeactivate,
  ]);
}

// Hook for managing focus order
export function useFocusOrder(refs: RefObject<HTMLElement>[]) {
  const handleKeyDown = (event: KeyboardEvent, currentIndex: number) => {
    if (!["ArrowDown", "ArrowUp", "Home", "End"].includes(event.key)) return;

    event.preventDefault();
    let nextIndex = currentIndex;

    switch (event.key) {
      case "ArrowDown":
        nextIndex = Math.min(currentIndex + 1, refs.length - 1);
        break;
      case "ArrowUp":
        nextIndex = Math.max(currentIndex - 1, 0);
        break;
      case "Home":
        nextIndex = 0;
        break;
      case "End":
        nextIndex = refs.length - 1;
        break;
    }

    refs[nextIndex]?.current?.focus();
  };

  return { handleKeyDown };
}

// Hook for skip navigation links
export function useSkipNavigation() {
  useEffect(() => {
    const skipLink = document.getElementById("skip-navigation");
    const mainContent = document.getElementById("main-content");

    if (!skipLink || !mainContent) return;

    const handleSkipClick = (event: Event) => {
      event.preventDefault();
      mainContent.focus();
      mainContent.scrollIntoView();
    };

    skipLink.addEventListener("click", handleSkipClick);
    return () => skipLink.removeEventListener("click", handleSkipClick);
  }, []);
}

// Hook for roving tabindex pattern
export function useRovingTabIndex(
  items: RefObject<HTMLElement>[],
  options: {
    orientation?: "horizontal" | "vertical" | "grid";
    loop?: boolean;
  } = {}
) {
  const { orientation = "vertical", loop = true } = options;
  const [focusedIndex, setFocusedIndex] = useState(0);

  useEffect(() => {
    items.forEach((item, index) => {
      if (item.current) {
        item.current.tabIndex = index === focusedIndex ? 0 : -1;
      }
    });
  }, [focusedIndex, items]);

  const handleKeyDown = (event: KeyboardEvent, currentIndex: number) => {
    let handled = false;
    let nextIndex = currentIndex;

    switch (event.key) {
      case "ArrowRight":
        if (orientation === "horizontal" || orientation === "grid") {
          nextIndex = currentIndex + 1;
          handled = true;
        }
        break;
      case "ArrowLeft":
        if (orientation === "horizontal" || orientation === "grid") {
          nextIndex = currentIndex - 1;
          handled = true;
        }
        break;
      case "ArrowDown":
        if (orientation === "vertical" || orientation === "grid") {
          nextIndex = currentIndex + (orientation === "grid" ? 4 : 1);
          handled = true;
        }
        break;
      case "ArrowUp":
        if (orientation === "vertical" || orientation === "grid") {
          nextIndex = currentIndex - (orientation === "grid" ? 4 : 1);
          handled = true;
        }
        break;
      case "Home":
        nextIndex = 0;
        handled = true;
        break;
      case "End":
        nextIndex = items.length - 1;
        handled = true;
        break;
    }

    if (handled) {
      event.preventDefault();

      if (loop) {
        nextIndex = (nextIndex + items.length) % items.length;
      } else {
        nextIndex = Math.max(0, Math.min(nextIndex, items.length - 1));
      }

      setFocusedIndex(nextIndex);
      items[nextIndex]?.current?.focus();
    }
  };

  return {
    focusedIndex,
    setFocusedIndex,
    handleKeyDown,
  };
}
