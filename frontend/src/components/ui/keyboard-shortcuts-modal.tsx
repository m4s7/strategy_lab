"use client";

import { useEffect, useState } from "react";
import { X } from "lucide-react";
import {
  useKeyboardShortcuts,
  formatShortcut,
} from "@/hooks/use-keyboard-shortcuts";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

export function KeyboardShortcutsModal() {
  const [isOpen, setIsOpen] = useState(false);
  const { getShortcutsByCategory } = useKeyboardShortcuts();
  const categories = getShortcutsByCategory();

  useEffect(() => {
    const handleShowShortcuts = () => setIsOpen(true);
    window.addEventListener("showKeyboardShortcuts", handleShowShortcuts);
    return () =>
      window.removeEventListener("showKeyboardShortcuts", handleShowShortcuts);
  }, []);

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="text-xl font-semibold">
            Keyboard Shortcuts
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-6 mt-4">
          {categories.map((category) => (
            <div key={category.name}>
              <h3 className="text-sm font-medium text-muted-foreground mb-3">
                {category.name}
              </h3>
              <div className="space-y-2">
                {category.shortcuts.map((shortcut, index) => (
                  <div
                    key={`${shortcut.key}-${index}`}
                    className="flex items-center justify-between py-2 px-3 rounded-lg hover:bg-surface-hover transition-colors-smooth"
                  >
                    <span className="text-sm">{shortcut.description}</span>
                    <kbd className="px-2 py-1 text-xs font-mono bg-muted rounded-md border border-border">
                      {formatShortcut(shortcut)}
                    </kbd>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>

        <div className="mt-6 pt-6 border-t border-border">
          <div className="flex items-center justify-between text-sm text-muted-foreground">
            <span>Press Ctrl+/ to show this help anytime</span>
            <button
              onClick={() => setIsOpen(false)}
              className="text-primary hover:text-primary-hover transition-colors-smooth"
            >
              Close
            </button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
