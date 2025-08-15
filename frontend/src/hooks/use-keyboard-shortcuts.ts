import { useEffect, useCallback, useRef } from "react";
import { useRouter } from "next/navigation";

interface ShortcutConfig {
  key: string;
  ctrl?: boolean;
  shift?: boolean;
  alt?: boolean;
  meta?: boolean;
  description: string;
  category: string;
  action: () => void;
  enabled?: boolean;
}

interface ShortcutCategory {
  name: string;
  shortcuts: ShortcutConfig[];
}

// Default keyboard shortcuts
const defaultShortcuts: ShortcutConfig[] = [
  // Navigation
  {
    key: "k",
    ctrl: true,
    description: "Open quick search",
    category: "Navigation",
    action: () => {
      const event = new CustomEvent("openQuickSearch");
      window.dispatchEvent(event);
    },
  },
  {
    key: "b",
    ctrl: true,
    description: "Toggle sidebar",
    category: "Navigation",
    action: () => {
      const event = new CustomEvent("toggleSidebar");
      window.dispatchEvent(event);
    },
  },
  {
    key: "/",
    ctrl: true,
    description: "Show keyboard shortcuts",
    category: "Navigation",
    action: () => {
      const event = new CustomEvent("showKeyboardShortcuts");
      window.dispatchEvent(event);
    },
  },
  {
    key: "1",
    ctrl: true,
    description: "Go to Dashboard",
    category: "Navigation",
    action: () => {
      window.location.href = "/dashboard";
    },
  },
  {
    key: "2",
    ctrl: true,
    description: "Go to Backtesting",
    category: "Navigation",
    action: () => {
      window.location.href = "/backtesting";
    },
  },
  {
    key: "3",
    ctrl: true,
    description: "Go to Analysis",
    category: "Navigation",
    action: () => {
      window.location.href = "/analysis";
    },
  },
  {
    key: "4",
    ctrl: true,
    description: "Go to Optimization",
    category: "Navigation",
    action: () => {
      window.location.href = "/optimization";
    },
  },
  // Actions
  {
    key: "n",
    ctrl: true,
    description: "New backtest",
    category: "Actions",
    action: () => {
      const event = new CustomEvent("newBacktest");
      window.dispatchEvent(event);
    },
  },
  {
    key: "s",
    ctrl: true,
    description: "Save configuration",
    category: "Actions",
    action: () => {
      const event = new CustomEvent("saveConfiguration");
      window.dispatchEvent(event);
    },
  },
  {
    key: "r",
    ctrl: true,
    description: "Run backtest",
    category: "Actions",
    action: () => {
      const event = new CustomEvent("runBacktest");
      window.dispatchEvent(event);
    },
  },
  {
    key: "z",
    ctrl: true,
    description: "Undo",
    category: "Actions",
    action: () => {
      const event = new CustomEvent("undo");
      window.dispatchEvent(event);
    },
  },
  {
    key: "z",
    ctrl: true,
    shift: true,
    description: "Redo",
    category: "Actions",
    action: () => {
      const event = new CustomEvent("redo");
      window.dispatchEvent(event);
    },
  },
  // Analysis
  {
    key: " ",
    description: "Play/pause chart",
    category: "Analysis",
    action: () => {
      const event = new CustomEvent("toggleChartPlayback");
      window.dispatchEvent(event);
    },
  },
  {
    key: "z",
    shift: true,
    description: "Zoom to fit",
    category: "Analysis",
    action: () => {
      const event = new CustomEvent("zoomToFit");
      window.dispatchEvent(event);
    },
  },
  {
    key: "ArrowLeft",
    description: "Previous data point",
    category: "Analysis",
    action: () => {
      const event = new CustomEvent("navigateDataPoint", {
        detail: { direction: "prev" },
      });
      window.dispatchEvent(event);
    },
  },
  {
    key: "ArrowRight",
    description: "Next data point",
    category: "Analysis",
    action: () => {
      const event = new CustomEvent("navigateDataPoint", {
        detail: { direction: "next" },
      });
      window.dispatchEvent(event);
    },
  },
  // View
  {
    key: "f",
    ctrl: true,
    shift: true,
    description: "Toggle fullscreen",
    category: "View",
    action: () => {
      if (!document.fullscreenElement) {
        document.documentElement.requestFullscreen();
      } else {
        document.exitFullscreen();
      }
    },
  },
  {
    key: "d",
    ctrl: true,
    shift: true,
    description: "Toggle dark mode",
    category: "View",
    action: () => {
      const event = new CustomEvent("toggleTheme");
      window.dispatchEvent(event);
    },
  },
];

export function useKeyboardShortcuts(
  customShortcuts?: ShortcutConfig[],
  options?: {
    preventDefault?: boolean;
    stopPropagation?: boolean;
    enabled?: boolean;
  }
) {
  const shortcuts = useRef<ShortcutConfig[]>([
    ...defaultShortcuts,
    ...(customShortcuts || []),
  ]);
  const activeKeys = useRef<Set<string>>(new Set());

  const handleKeyDown = useCallback(
    (event: KeyboardEvent) => {
      if (options?.enabled === false) return;

      // Don't trigger shortcuts when typing in inputs
      const target = event.target as HTMLElement;
      if (
        target.tagName === "INPUT" ||
        target.tagName === "TEXTAREA" ||
        target.tagName === "SELECT" ||
        target.contentEditable === "true"
      ) {
        return;
      }

      activeKeys.current.add(event.key);

      // Find matching shortcut
      const matchingShortcut = shortcuts.current.find((shortcut) => {
        if (shortcut.enabled === false) return false;
        if (shortcut.key !== event.key) return false;
        if (shortcut.ctrl !== event.ctrlKey) return false;
        if (shortcut.shift !== event.shiftKey) return false;
        if (shortcut.alt !== event.altKey) return false;
        if (shortcut.meta !== event.metaKey) return false;
        return true;
      });

      if (matchingShortcut) {
        if (options?.preventDefault) {
          event.preventDefault();
        }
        if (options?.stopPropagation) {
          event.stopPropagation();
        }
        matchingShortcut.action();
      }
    },
    [options]
  );

  const handleKeyUp = useCallback((event: KeyboardEvent) => {
    activeKeys.current.delete(event.key);
  }, []);

  useEffect(() => {
    window.addEventListener("keydown", handleKeyDown);
    window.addEventListener("keyup", handleKeyUp);

    return () => {
      window.removeEventListener("keydown", handleKeyDown);
      window.removeEventListener("keyup", handleKeyUp);
    };
  }, [handleKeyDown, handleKeyUp]);

  const addShortcut = useCallback((shortcut: ShortcutConfig) => {
    shortcuts.current.push(shortcut);
  }, []);

  const removeShortcut = useCallback(
    (key: string, modifiers?: Partial<ShortcutConfig>) => {
      shortcuts.current = shortcuts.current.filter((shortcut) => {
        if (shortcut.key !== key) return true;
        if (modifiers?.ctrl !== undefined && shortcut.ctrl !== modifiers.ctrl)
          return true;
        if (
          modifiers?.shift !== undefined &&
          shortcut.shift !== modifiers.shift
        )
          return true;
        if (modifiers?.alt !== undefined && shortcut.alt !== modifiers.alt)
          return true;
        if (modifiers?.meta !== undefined && shortcut.meta !== modifiers.meta)
          return true;
        return false;
      });
    },
    []
  );

  const getShortcutsByCategory = useCallback((): ShortcutCategory[] => {
    const categories = new Map<string, ShortcutConfig[]>();

    shortcuts.current.forEach((shortcut) => {
      const existing = categories.get(shortcut.category) || [];
      categories.set(shortcut.category, [...existing, shortcut]);
    });

    return Array.from(categories.entries()).map(([name, shortcuts]) => ({
      name,
      shortcuts,
    }));
  }, []);

  const isPressed = useCallback((key: string): boolean => {
    return activeKeys.current.has(key);
  }, []);

  return {
    addShortcut,
    removeShortcut,
    getShortcutsByCategory,
    isPressed,
    shortcuts: shortcuts.current,
  };
}

// Format shortcut for display
export function formatShortcut(shortcut: ShortcutConfig): string {
  const parts: string[] = [];

  if (shortcut.ctrl) parts.push("Ctrl");
  if (shortcut.alt) parts.push("Alt");
  if (shortcut.shift) parts.push("Shift");
  if (shortcut.meta) parts.push("⌘");

  // Format special keys
  let key = shortcut.key;
  switch (key) {
    case " ":
      key = "Space";
      break;
    case "ArrowLeft":
      key = "←";
      break;
    case "ArrowRight":
      key = "→";
      break;
    case "ArrowUp":
      key = "↑";
      break;
    case "ArrowDown":
      key = "↓";
      break;
    case "Enter":
      key = "⏎";
      break;
    case "Escape":
      key = "Esc";
      break;
    default:
      key = key.toUpperCase();
  }

  parts.push(key);
  return parts.join("+");
}

// Vi-mode navigation hook
export function useViMode(enabled: boolean = false) {
  const mode = useRef<"normal" | "insert" | "visual">("normal");
  const commandBuffer = useRef<string>("");

  useEffect(() => {
    if (!enabled) return;

    const handleViCommand = (event: KeyboardEvent) => {
      // Skip if in input field
      const target = event.target as HTMLElement;
      if (
        target.tagName === "INPUT" ||
        target.tagName === "TEXTAREA" ||
        target.tagName === "SELECT" ||
        target.contentEditable === "true"
      ) {
        mode.current = "insert";
        return;
      }

      if (mode.current === "normal") {
        event.preventDefault();
        commandBuffer.current += event.key;

        // Process vi commands
        const command = commandBuffer.current;

        // Navigation
        if (command === "j") {
          window.dispatchEvent(
            new CustomEvent("viNavigate", { detail: { direction: "down" } })
          );
          commandBuffer.current = "";
        } else if (command === "k") {
          window.dispatchEvent(
            new CustomEvent("viNavigate", { detail: { direction: "up" } })
          );
          commandBuffer.current = "";
        } else if (command === "h") {
          window.dispatchEvent(
            new CustomEvent("viNavigate", { detail: { direction: "left" } })
          );
          commandBuffer.current = "";
        } else if (command === "l") {
          window.dispatchEvent(
            new CustomEvent("viNavigate", { detail: { direction: "right" } })
          );
          commandBuffer.current = "";
        } else if (command === "gg") {
          window.dispatchEvent(
            new CustomEvent("viNavigate", { detail: { direction: "top" } })
          );
          commandBuffer.current = "";
        } else if (command === "G") {
          window.dispatchEvent(
            new CustomEvent("viNavigate", { detail: { direction: "bottom" } })
          );
          commandBuffer.current = "";
        } else if (command === "/") {
          window.dispatchEvent(new CustomEvent("viSearch"));
          commandBuffer.current = "";
        } else if (command === "i") {
          mode.current = "insert";
          commandBuffer.current = "";
        } else if (command === "v") {
          mode.current = "visual";
          commandBuffer.current = "";
        } else if (command === ":") {
          window.dispatchEvent(new CustomEvent("viCommand"));
          commandBuffer.current = "";
        }

        // Clear buffer if unrecognized after 1 second
        setTimeout(() => {
          commandBuffer.current = "";
        }, 1000);
      } else if (event.key === "Escape") {
        mode.current = "normal";
        commandBuffer.current = "";
      }
    };

    window.addEventListener("keydown", handleViCommand);
    return () => window.removeEventListener("keydown", handleViCommand);
  }, [enabled]);

  return {
    mode: mode.current,
    commandBuffer: commandBuffer.current,
  };
}
