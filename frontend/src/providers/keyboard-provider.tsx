"use client";

import { createContext, useContext, useState, ReactNode } from "react";
import { KeyboardShortcutsModal } from "@/components/ui/keyboard-shortcuts-modal";
import { QuickSearch } from "@/components/ui/quick-search";
import { useKeyboardShortcuts } from "@/hooks/use-keyboard-shortcuts";

interface KeyboardProviderProps {
  children: ReactNode;
  viModeEnabled?: boolean;
}

interface KeyboardContextValue {
  viModeEnabled: boolean;
  setViModeEnabled: (enabled: boolean) => void;
}

const KeyboardContext = createContext<KeyboardContextValue>({
  viModeEnabled: false,
  setViModeEnabled: () => {},
});

export function KeyboardProvider({
  children,
  viModeEnabled: initialViMode = false,
}: KeyboardProviderProps) {
  const [viModeEnabled, setViModeEnabled] = useState(initialViMode);

  // Initialize global keyboard shortcuts
  useKeyboardShortcuts([], {
    preventDefault: true,
    enabled: true,
  });

  return (
    <KeyboardContext.Provider value={{ viModeEnabled, setViModeEnabled }}>
      {children}
      <KeyboardShortcutsModal />
      <QuickSearch />
    </KeyboardContext.Provider>
  );
}

export const useKeyboardContext = () => useContext(KeyboardContext);
