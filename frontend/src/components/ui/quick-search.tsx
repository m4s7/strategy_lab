"use client";

import { useState, useEffect, useRef } from "react";
import { Search, FileText, Activity, BarChart, Settings } from "lucide-react";
import { useRouter } from "next/navigation";
import { useFocusTrap } from "@/hooks/use-focus-trap";
import { Dialog, DialogContent } from "@/components/ui/dialog";

interface SearchResult {
  id: string;
  title: string;
  description: string;
  icon: React.ReactNode;
  category: string;
  url: string;
  keywords: string[];
}

const searchableItems: SearchResult[] = [
  {
    id: "dashboard",
    title: "Dashboard",
    description: "System overview and metrics",
    icon: <Activity className="w-4 h-4" />,
    category: "Navigation",
    url: "/dashboard",
    keywords: ["home", "overview", "metrics", "status"],
  },
  {
    id: "new-backtest",
    title: "New Backtest",
    description: "Create a new backtest configuration",
    icon: <FileText className="w-4 h-4" />,
    category: "Actions",
    url: "/backtesting/new",
    keywords: ["create", "test", "strategy", "run"],
  },
  {
    id: "backtest-results",
    title: "Backtest Results",
    description: "View backtest results and analysis",
    icon: <BarChart className="w-4 h-4" />,
    category: "Navigation",
    url: "/backtesting/results",
    keywords: ["results", "analysis", "performance", "report"],
  },
  {
    id: "optimization",
    title: "Parameter Optimization",
    description: "Optimize strategy parameters",
    icon: <Settings className="w-4 h-4" />,
    category: "Navigation",
    url: "/optimization",
    keywords: ["optimize", "parameters", "tuning", "genetic"],
  },
  {
    id: "strategy-config",
    title: "Strategy Configuration",
    description: "Configure trading strategies",
    icon: <Settings className="w-4 h-4" />,
    category: "Navigation",
    url: "/strategies",
    keywords: ["strategy", "config", "settings", "parameters"],
  },
];

export function QuickSearch() {
  const [isOpen, setIsOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [selectedIndex, setSelectedIndex] = useState(0);
  const router = useRouter();
  const dialogRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useFocusTrap(dialogRef, {
    enabled: isOpen,
    initialFocus: inputRef,
    onDeactivate: () => setIsOpen(false),
  });

  // Filter results based on query
  const filteredResults = searchableItems.filter((item) => {
    const searchQuery = query.toLowerCase();
    return (
      item.title.toLowerCase().includes(searchQuery) ||
      item.description.toLowerCase().includes(searchQuery) ||
      item.keywords.some((keyword) => keyword.includes(searchQuery))
    );
  });

  // Handle opening via keyboard shortcut
  useEffect(() => {
    const handleOpen = () => setIsOpen(true);
    window.addEventListener("openQuickSearch", handleOpen);
    return () => window.removeEventListener("openQuickSearch", handleOpen);
  }, []);

  // Reset selection when results change
  useEffect(() => {
    setSelectedIndex(0);
  }, [query]);

  const handleKeyDown = (event: React.KeyboardEvent) => {
    switch (event.key) {
      case "ArrowDown":
        event.preventDefault();
        setSelectedIndex((prev) =>
          prev < filteredResults.length - 1 ? prev + 1 : 0
        );
        break;
      case "ArrowUp":
        event.preventDefault();
        setSelectedIndex((prev) =>
          prev > 0 ? prev - 1 : filteredResults.length - 1
        );
        break;
      case "Enter":
        event.preventDefault();
        if (filteredResults[selectedIndex]) {
          handleSelect(filteredResults[selectedIndex]);
        }
        break;
    }
  };

  const handleSelect = (result: SearchResult) => {
    router.push(result.url);
    setIsOpen(false);
    setQuery("");
  };

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogContent
        ref={dialogRef}
        className="p-0 max-w-2xl top-[20%] translate-y-0"
      >
        <div className="flex items-center px-4 border-b border-border">
          <Search className="w-5 h-5 text-muted-foreground" />
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Search for pages, actions, or settings..."
            className="w-full px-3 py-4 bg-transparent outline-none placeholder:text-muted-foreground"
          />
        </div>

        {filteredResults.length > 0 ? (
          <div className="max-h-[400px] overflow-y-auto">
            {filteredResults.map((result, index) => (
              <button
                key={result.id}
                onClick={() => handleSelect(result)}
                onMouseEnter={() => setSelectedIndex(index)}
                className={`
                  w-full px-4 py-3 flex items-center gap-3 text-left
                  transition-colors-smooth
                  ${
                    index === selectedIndex
                      ? "bg-accent text-accent-foreground"
                      : "hover:bg-accent/50"
                  }
                `}
              >
                <div className="flex-shrink-0 w-8 h-8 rounded-lg bg-muted flex items-center justify-center">
                  {result.icon}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="font-medium">{result.title}</div>
                  <div className="text-sm text-muted-foreground truncate">
                    {result.description}
                  </div>
                </div>
                <div className="text-xs text-muted-foreground">
                  {result.category}
                </div>
              </button>
            ))}
          </div>
        ) : query ? (
          <div className="p-8 text-center text-muted-foreground">
            No results found for "{query}"
          </div>
        ) : (
          <div className="p-8 text-center text-muted-foreground">
            Start typing to search...
          </div>
        )}

        <div className="px-4 py-3 border-t border-border text-xs text-muted-foreground flex items-center justify-between">
          <div className="flex items-center gap-4">
            <span className="flex items-center gap-1">
              <kbd className="px-1.5 py-0.5 bg-muted rounded">↑</kbd>
              <kbd className="px-1.5 py-0.5 bg-muted rounded">↓</kbd>
              to navigate
            </span>
            <span className="flex items-center gap-1">
              <kbd className="px-1.5 py-0.5 bg-muted rounded">⏎</kbd>
              to select
            </span>
            <span className="flex items-center gap-1">
              <kbd className="px-1.5 py-0.5 bg-muted rounded">Esc</kbd>
              to close
            </span>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
