"use client";

import { useRef, useEffect, ReactNode, HTMLAttributes } from "react";
import { cn } from "@/lib/utils";
import { useReducedMotion } from "./accessible-chart";

interface AnimationProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode;
  duration?: number;
  delay?: number;
  className?: string;
}

// Fade In Animation
export function FadeIn({
  children,
  duration = 300,
  delay = 0,
  className,
  ...props
}: AnimationProps) {
  const ref = useRef<HTMLDivElement>(null);
  const prefersReducedMotion = useReducedMotion();

  useEffect(() => {
    if (prefersReducedMotion || !ref.current) return;

    const element = ref.current;
    element.style.opacity = "0";
    element.style.transform = "translateY(10px)";

    const timer = setTimeout(() => {
      element.style.transition = `opacity ${duration}ms ease-out, transform ${duration}ms ease-out`;
      element.style.opacity = "1";
      element.style.transform = "translateY(0)";
    }, delay);

    return () => clearTimeout(timer);
  }, [duration, delay, prefersReducedMotion]);

  return (
    <div ref={ref} className={className} {...props}>
      {children}
    </div>
  );
}

// Slide In Animation
interface SlideInProps extends AnimationProps {
  direction?: "left" | "right" | "up" | "down";
}

export function SlideIn({
  children,
  direction = "left",
  duration = 300,
  delay = 0,
  className,
  ...props
}: SlideInProps) {
  const ref = useRef<HTMLDivElement>(null);
  const prefersReducedMotion = useReducedMotion();

  useEffect(() => {
    if (prefersReducedMotion || !ref.current) return;

    const element = ref.current;
    const distance = "20px";

    // Set initial position
    switch (direction) {
      case "left":
        element.style.transform = `translateX(-${distance})`;
        break;
      case "right":
        element.style.transform = `translateX(${distance})`;
        break;
      case "up":
        element.style.transform = `translateY(-${distance})`;
        break;
      case "down":
        element.style.transform = `translateY(${distance})`;
        break;
    }
    element.style.opacity = "0";

    const timer = setTimeout(() => {
      element.style.transition = `opacity ${duration}ms ease-out, transform ${duration}ms ease-out`;
      element.style.opacity = "1";
      element.style.transform = "translate(0, 0)";
    }, delay);

    return () => clearTimeout(timer);
  }, [direction, duration, delay, prefersReducedMotion]);

  return (
    <div ref={ref} className={className} {...props}>
      {children}
    </div>
  );
}

// Stagger Children Animation
interface StaggerChildrenProps extends AnimationProps {
  staggerDelay?: number;
}

export function StaggerChildren({
  children,
  staggerDelay = 100,
  duration = 300,
  className,
  ...props
}: StaggerChildrenProps) {
  const ref = useRef<HTMLDivElement>(null);
  const prefersReducedMotion = useReducedMotion();

  useEffect(() => {
    if (prefersReducedMotion || !ref.current) return;

    const childElements = Array.from(ref.current.children) as HTMLElement[];

    childElements.forEach((child, index) => {
      child.style.opacity = "0";
      child.style.transform = "translateY(10px)";

      setTimeout(() => {
        child.style.transition = `opacity ${duration}ms ease-out, transform ${duration}ms ease-out`;
        child.style.opacity = "1";
        child.style.transform = "translateY(0)";
      }, index * staggerDelay);
    });
  }, [duration, staggerDelay, prefersReducedMotion]);

  return (
    <div ref={ref} className={className} {...props}>
      {children}
    </div>
  );
}

// Hover Scale Animation Component
interface HoverScaleProps extends HTMLAttributes<HTMLDivElement> {
  scale?: number;
  duration?: number;
}

export function HoverScale({
  children,
  scale = 1.05,
  duration = 200,
  className,
  ...props
}: HoverScaleProps) {
  const prefersReducedMotion = useReducedMotion();

  return (
    <div
      className={cn(
        "transition-transform cursor-pointer",
        !prefersReducedMotion && "hover:scale-105",
        className
      )}
      style={
        {
          transitionDuration: prefersReducedMotion ? "0ms" : `${duration}ms`,
          "--hover-scale": scale,
        } as React.CSSProperties
      }
      {...props}
    >
      {children}
    </div>
  );
}

// Ripple Effect
interface RippleProps extends HTMLAttributes<HTMLDivElement> {
  color?: string;
  duration?: number;
}

export function Ripple({
  children,
  color = "currentColor",
  duration = 600,
  className,
  onClick,
  ...props
}: RippleProps) {
  const ref = useRef<HTMLDivElement>(null);
  const prefersReducedMotion = useReducedMotion();

  const createRipple = (event: React.MouseEvent<HTMLDivElement>) => {
    if (prefersReducedMotion || !ref.current) {
      onClick?.(event);
      return;
    }

    const element = ref.current;
    const rect = element.getBoundingClientRect();
    const size = Math.max(rect.width, rect.height);
    const x = event.clientX - rect.left - size / 2;
    const y = event.clientY - rect.top - size / 2;

    const ripple = document.createElement("span");
    ripple.style.width = ripple.style.height = `${size}px`;
    ripple.style.left = `${x}px`;
    ripple.style.top = `${y}px`;
    ripple.style.backgroundColor = color;
    ripple.classList.add("ripple-effect");

    element.appendChild(ripple);

    setTimeout(() => {
      ripple.remove();
    }, duration);

    onClick?.(event);
  };

  return (
    <div
      ref={ref}
      className={cn("relative overflow-hidden", className)}
      onClick={createRipple}
      {...props}
    >
      {children}
      <style jsx>{`
        .ripple-effect {
          position: absolute;
          border-radius: 50%;
          transform: scale(0);
          animation: ripple ${duration}ms ease-out;
          opacity: 0.3;
          pointer-events: none;
        }

        @keyframes ripple {
          to {
            transform: scale(4);
            opacity: 0;
          }
        }
      `}</style>
    </div>
  );
}

// Pulse Animation
interface PulseProps extends AnimationProps {
  intensity?: number;
}

export function Pulse({
  children,
  intensity = 1.05,
  duration = 2000,
  className,
  ...props
}: PulseProps) {
  const prefersReducedMotion = useReducedMotion();

  return (
    <div
      className={cn(!prefersReducedMotion && "animate-pulse-custom", className)}
      style={
        {
          "--pulse-scale": intensity,
          animationDuration: `${duration}ms`,
        } as React.CSSProperties
      }
      {...props}
    >
      {children}
      <style jsx>{`
        @keyframes pulse-custom {
          0%,
          100% {
            transform: scale(1);
          }
          50% {
            transform: scale(var(--pulse-scale));
          }
        }

        .animate-pulse-custom {
          animation: pulse-custom var(--duration) ease-in-out infinite;
        }
      `}</style>
    </div>
  );
}

// Count Up Animation
interface CountUpProps {
  end: number;
  start?: number;
  duration?: number;
  decimals?: number;
  prefix?: string;
  suffix?: string;
  className?: string;
}

export function CountUp({
  end,
  start = 0,
  duration = 2000,
  decimals = 0,
  prefix = "",
  suffix = "",
  className,
}: CountUpProps) {
  const [count, setCount] = useState(start);
  const prefersReducedMotion = useReducedMotion();

  useEffect(() => {
    if (prefersReducedMotion) {
      setCount(end);
      return;
    }

    let startTime: number | null = null;
    const startValue = start;
    const endValue = end;

    const updateCount = (timestamp: number) => {
      if (!startTime) startTime = timestamp;
      const progress = Math.min((timestamp - startTime) / duration, 1);

      // Ease out cubic
      const easeOut = 1 - Math.pow(1 - progress, 3);
      const currentValue = startValue + (endValue - startValue) * easeOut;

      setCount(currentValue);

      if (progress < 1) {
        requestAnimationFrame(updateCount);
      }
    };

    requestAnimationFrame(updateCount);
  }, [end, start, duration, prefersReducedMotion]);

  return (
    <span className={className}>
      {prefix}
      {count.toFixed(decimals)}
      {suffix}
    </span>
  );
}
