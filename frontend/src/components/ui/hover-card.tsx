"use client";

import { useState, useRef, useEffect, ReactNode, HTMLAttributes } from "react";
import { createPortal } from "react-dom";
import { cn } from "@/lib/utils";
import { useReducedMotion } from "./accessible-chart";

interface HoverCardProps {
  trigger: ReactNode;
  content: ReactNode;
  side?: "top" | "bottom" | "left" | "right";
  align?: "start" | "center" | "end";
  delay?: number;
  className?: string;
  triggerClassName?: string;
}

export function HoverCard({
  trigger,
  content,
  side = "bottom",
  align = "center",
  delay = 200,
  className,
  triggerClassName,
}: HoverCardProps) {
  const [isVisible, setIsVisible] = useState(false);
  const [position, setPosition] = useState({ top: 0, left: 0 });
  const triggerRef = useRef<HTMLDivElement>(null);
  const cardRef = useRef<HTMLDivElement>(null);
  const timeoutRef = useRef<NodeJS.Timeout>();
  const prefersReducedMotion = useReducedMotion();

  useEffect(() => {
    if (isVisible && triggerRef.current && cardRef.current) {
      const triggerRect = triggerRef.current.getBoundingClientRect();
      const cardRect = cardRef.current.getBoundingClientRect();
      const spacing = 12;

      let top = 0;
      let left = 0;

      // Calculate position based on side
      switch (side) {
        case "top":
          top = triggerRect.top - cardRect.height - spacing;
          break;
        case "bottom":
          top = triggerRect.bottom + spacing;
          break;
        case "left":
          left = triggerRect.left - cardRect.width - spacing;
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
            left = triggerRect.left + (triggerRect.width - cardRect.width) / 2;
            break;
          case "end":
            left = triggerRect.right - cardRect.width;
            break;
        }
      } else {
        switch (align) {
          case "start":
            top = triggerRect.top;
            break;
          case "center":
            top = triggerRect.top + (triggerRect.height - cardRect.height) / 2;
            break;
          case "end":
            top = triggerRect.bottom - cardRect.height;
            break;
        }
      }

      // Ensure card stays within viewport
      const padding = 12;
      top = Math.max(
        padding,
        Math.min(top, window.innerHeight - cardRect.height - padding)
      );
      left = Math.max(
        padding,
        Math.min(left, window.innerWidth - cardRect.width - padding)
      );

      setPosition({ top, left });
    }
  }, [isVisible, side, align]);

  const showCard = () => {
    clearTimeout(timeoutRef.current);
    timeoutRef.current = setTimeout(() => {
      setIsVisible(true);
    }, delay);
  };

  const hideCard = () => {
    clearTimeout(timeoutRef.current);
    timeoutRef.current = setTimeout(() => {
      setIsVisible(false);
    }, 100);
  };

  useEffect(() => {
    return () => {
      clearTimeout(timeoutRef.current);
    };
  }, []);

  return (
    <>
      <div
        ref={triggerRef}
        className={triggerClassName}
        onMouseEnter={showCard}
        onMouseLeave={hideCard}
      >
        {trigger}
      </div>
      {isVisible &&
        typeof document !== "undefined" &&
        createPortal(
          <div
            ref={cardRef}
            className={cn(
              "absolute z-popover bg-popover text-popover-foreground",
              "border border-border rounded-lg shadow-lg",
              "max-w-sm",
              !prefersReducedMotion && "animate-in fade-in-0 zoom-in-95",
              className
            )}
            style={{
              top: `${position.top}px`,
              left: `${position.left}px`,
            }}
            onMouseEnter={showCard}
            onMouseLeave={hideCard}
          >
            {content}
          </div>,
          document.body
        )}
    </>
  );
}

// Interactive hover card with 3D effect
interface HoverCard3DProps extends HTMLAttributes<HTMLDivElement> {
  intensity?: number;
  children: ReactNode;
}

export function HoverCard3D({
  children,
  className,
  intensity = 10,
  ...props
}: HoverCard3DProps) {
  const ref = useRef<HTMLDivElement>(null);
  const [rotateX, setRotateX] = useState(0);
  const [rotateY, setRotateY] = useState(0);
  const prefersReducedMotion = useReducedMotion();

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (prefersReducedMotion || !ref.current) return;

    const rect = ref.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    const centerX = rect.width / 2;
    const centerY = rect.height / 2;

    const rotateXValue = ((y - centerY) / centerY) * -intensity;
    const rotateYValue = ((x - centerX) / centerX) * intensity;

    setRotateX(rotateXValue);
    setRotateY(rotateYValue);
  };

  const handleMouseLeave = () => {
    setRotateX(0);
    setRotateY(0);
  };

  return (
    <div
      ref={ref}
      className={cn(
        "transition-transform duration-200 ease-out",
        "hover:shadow-xl",
        className
      )}
      style={{
        transform: prefersReducedMotion
          ? "none"
          : `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg)`,
        transformStyle: "preserve-3d",
      }}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      {...props}
    >
      {children}
    </div>
  );
}
