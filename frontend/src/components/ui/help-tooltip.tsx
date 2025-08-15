"use client";

import { useState, useRef, useEffect, ReactNode } from "react";
import { createPortal } from "react-dom";
import { HelpCircle, Info } from "lucide-react";
import { cn } from "@/lib/utils";

interface HelpTooltipProps {
  content: ReactNode;
  title?: string;
  side?: "top" | "bottom" | "left" | "right";
  align?: "start" | "center" | "end";
  delay?: number;
  className?: string;
  triggerClassName?: string;
  variant?: "help" | "info";
  size?: "sm" | "md";
}

export function HelpTooltip({
  content,
  title,
  side = "top",
  align = "center",
  delay = 200,
  className,
  triggerClassName,
  variant = "help",
  size = "sm",
}: HelpTooltipProps) {
  const [isVisible, setIsVisible] = useState(false);
  const [position, setPosition] = useState({ top: 0, left: 0 });
  const triggerRef = useRef<HTMLButtonElement>(null);
  const tooltipRef = useRef<HTMLDivElement>(null);
  const timeoutRef = useRef<NodeJS.Timeout>();

  const Icon = variant === "help" ? HelpCircle : Info;
  const iconSize = size === "sm" ? "w-4 h-4" : "w-5 h-5";

  useEffect(() => {
    if (isVisible && triggerRef.current && tooltipRef.current) {
      const triggerRect = triggerRef.current.getBoundingClientRect();
      const tooltipRect = tooltipRef.current.getBoundingClientRect();
      const spacing = 8;

      let top = 0;
      let left = 0;

      // Calculate position based on side
      switch (side) {
        case "top":
          top = triggerRect.top - tooltipRect.height - spacing;
          break;
        case "bottom":
          top = triggerRect.bottom + spacing;
          break;
        case "left":
          left = triggerRect.left - tooltipRect.width - spacing;
          break;
        case "right":
          left = triggerRect.right + spacing;
          break;
      }

      // Calculate alignment
      if (side === "top" || side === "bottom") {
        switch (align) {
          case "start":
            left = triggerRect.left;
            break;
          case "center":
            left =
              triggerRect.left + (triggerRect.width - tooltipRect.width) / 2;
            break;
          case "end":
            left = triggerRect.right - tooltipRect.width;
            break;
        }
      } else {
        switch (align) {
          case "start":
            top = triggerRect.top;
            break;
          case "center":
            top =
              triggerRect.top + (triggerRect.height - tooltipRect.height) / 2;
            break;
          case "end":
            top = triggerRect.bottom - tooltipRect.height;
            break;
        }
      }

      // Ensure tooltip stays within viewport
      const padding = 8;
      top = Math.max(
        padding,
        Math.min(top, window.innerHeight - tooltipRect.height - padding)
      );
      left = Math.max(
        padding,
        Math.min(left, window.innerWidth - tooltipRect.width - padding)
      );

      setPosition({ top, left });
    }
  }, [isVisible, side, align]);

  const showTooltip = () => {
    clearTimeout(timeoutRef.current);
    timeoutRef.current = setTimeout(() => {
      setIsVisible(true);
    }, delay);
  };

  const hideTooltip = () => {
    clearTimeout(timeoutRef.current);
    setIsVisible(false);
  };

  const toggleTooltip = () => {
    if (isVisible) {
      hideTooltip();
    } else {
      setIsVisible(true);
    }
  };

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        isVisible &&
        triggerRef.current &&
        tooltipRef.current &&
        !triggerRef.current.contains(event.target as Node) &&
        !tooltipRef.current.contains(event.target as Node)
      ) {
        setIsVisible(false);
      }
    };

    if (isVisible) {
      document.addEventListener("click", handleClickOutside);
      return () => document.removeEventListener("click", handleClickOutside);
    }
  }, [isVisible]);

  useEffect(() => {
    return () => {
      clearTimeout(timeoutRef.current);
    };
  }, []);

  return (
    <>
      <button
        ref={triggerRef}
        type="button"
        className={cn(
          "inline-flex items-center justify-center text-muted-foreground",
          "hover:text-foreground transition-colors-smooth",
          "focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2",
          "rounded-full",
          triggerClassName
        )}
        onMouseEnter={showTooltip}
        onMouseLeave={hideTooltip}
        onFocus={showTooltip}
        onBlur={hideTooltip}
        onClick={toggleTooltip}
        aria-label="Show help information"
        aria-describedby={isVisible ? "help-tooltip" : undefined}
      >
        <Icon className={iconSize} />
      </button>
      {isVisible &&
        typeof document !== "undefined" &&
        createPortal(
          <div
            id="help-tooltip"
            ref={tooltipRef}
            role="tooltip"
            className={cn(
              "absolute z-tooltip max-w-sm bg-popover text-popover-foreground",
              "border border-border rounded-lg shadow-lg",
              "animate-in fade-in-0 zoom-in-95",
              className
            )}
            style={{
              top: `${position.top}px`,
              left: `${position.left}px`,
            }}
          >
            {title && (
              <div className="px-3 py-2 border-b border-border">
                <h4 className="font-medium text-sm">{title}</h4>
              </div>
            )}
            <div className="px-3 py-2 text-sm">{content}</div>
            <div
              className={cn(
                "tooltip-arrow absolute w-2 h-2 bg-popover border",
                side === "top" && "tooltip-arrow-bottom border-t-0 border-l-0",
                side === "bottom" && "tooltip-arrow-top border-b-0 border-r-0",
                side === "left" && "tooltip-arrow-right border-t-0 border-r-0",
                side === "right" && "tooltip-arrow-left border-b-0 border-l-0"
              )}
            />
          </div>,
          document.body
        )}
    </>
  );
}
