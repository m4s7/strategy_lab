"use client";

import { useState, useEffect, useRef } from "react";
import { createPortal } from "react-dom";
import { X, ChevronLeft, ChevronRight } from "lucide-react";
import { cn } from "@/lib/utils";
import { useFocusTrap } from "@/hooks/use-focus-trap";

interface TourStep {
  target: string; // CSS selector for the target element
  title: string;
  content: string;
  placement?: "top" | "bottom" | "left" | "right";
  highlightPadding?: number;
}

interface OnboardingTourProps {
  steps: TourStep[];
  onComplete?: () => void;
  onSkip?: () => void;
  storageKey?: string; // Key to store tour completion in localStorage
}

export function OnboardingTour({
  steps,
  onComplete,
  onSkip,
  storageKey = "onboarding-completed",
}: OnboardingTourProps) {
  const [isActive, setIsActive] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [targetElement, setTargetElement] = useState<HTMLElement | null>(null);
  const [position, setPosition] = useState({ top: 0, left: 0 });
  const tooltipRef = useRef<HTMLDivElement>(null);

  useFocusTrap(tooltipRef, {
    enabled: isActive,
    escapeDeactivates: true,
    onDeactivate: () => handleSkip(),
  });

  // Check if tour has been completed before
  useEffect(() => {
    if (storageKey) {
      const completed = localStorage.getItem(storageKey);
      if (!completed) {
        // Start tour after a short delay to let the page load
        setTimeout(() => setIsActive(true), 1000);
      }
    } else {
      setIsActive(true);
    }
  }, [storageKey]);

  // Find and highlight current step target
  useEffect(() => {
    if (!isActive || !steps[currentStep]) return;

    const { target } = steps[currentStep];
    const element = document.querySelector(target) as HTMLElement;

    if (element) {
      setTargetElement(element);
      element.scrollIntoView({ behavior: "smooth", block: "center" });

      // Add highlight class
      element.classList.add("tour-highlight");

      return () => {
        element.classList.remove("tour-highlight");
      };
    }
  }, [isActive, currentStep, steps]);

  // Calculate tooltip position
  useEffect(() => {
    if (!targetElement || !tooltipRef.current) return;

    const calculatePosition = () => {
      const targetRect = targetElement.getBoundingClientRect();
      const tooltipRect = tooltipRef.current!.getBoundingClientRect();
      const placement = steps[currentStep].placement || "bottom";
      const padding = 16;

      let top = 0;
      let left = 0;

      switch (placement) {
        case "top":
          top = targetRect.top - tooltipRect.height - padding;
          left = targetRect.left + (targetRect.width - tooltipRect.width) / 2;
          break;
        case "bottom":
          top = targetRect.bottom + padding;
          left = targetRect.left + (targetRect.width - tooltipRect.width) / 2;
          break;
        case "left":
          top = targetRect.top + (targetRect.height - tooltipRect.height) / 2;
          left = targetRect.left - tooltipRect.width - padding;
          break;
        case "right":
          top = targetRect.top + (targetRect.height - tooltipRect.height) / 2;
          left = targetRect.right + padding;
          break;
      }

      // Ensure tooltip stays within viewport
      top = Math.max(
        padding,
        Math.min(top, window.innerHeight - tooltipRect.height - padding)
      );
      left = Math.max(
        padding,
        Math.min(left, window.innerWidth - tooltipRect.width - padding)
      );

      setPosition({ top, left });
    };

    calculatePosition();

    // Recalculate on scroll or resize
    window.addEventListener("scroll", calculatePosition);
    window.addEventListener("resize", calculatePosition);

    return () => {
      window.removeEventListener("scroll", calculatePosition);
      window.removeEventListener("resize", calculatePosition);
    };
  }, [targetElement, currentStep, steps]);

  const handleNext = () => {
    if (currentStep < steps.length - 1) {
      setCurrentStep(currentStep + 1);
    } else {
      handleComplete();
    }
  };

  const handlePrevious = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleComplete = () => {
    setIsActive(false);
    if (storageKey) {
      localStorage.setItem(storageKey, "true");
    }
    onComplete?.();
  };

  const handleSkip = () => {
    setIsActive(false);
    if (storageKey) {
      localStorage.setItem(storageKey, "true");
    }
    onSkip?.();
  };

  if (!isActive || !targetElement) return null;

  const step = steps[currentStep];
  const progress = ((currentStep + 1) / steps.length) * 100;

  return typeof document !== "undefined"
    ? createPortal(
        <>
          {/* Backdrop with spotlight */}
          <div className="fixed inset-0 z-40">
            <div className="absolute inset-0 bg-black/50" />
            {targetElement && (
              <div
                className="absolute bg-transparent"
                style={{
                  top:
                    targetElement.getBoundingClientRect().top -
                    (step.highlightPadding || 8),
                  left:
                    targetElement.getBoundingClientRect().left -
                    (step.highlightPadding || 8),
                  width:
                    targetElement.getBoundingClientRect().width +
                    2 * (step.highlightPadding || 8),
                  height:
                    targetElement.getBoundingClientRect().height +
                    2 * (step.highlightPadding || 8),
                  boxShadow: "0 0 0 9999px rgba(0, 0, 0, 0.5)",
                  borderRadius: "8px",
                }}
              />
            )}
          </div>

          {/* Tour tooltip */}
          <div
            ref={tooltipRef}
            className={cn(
              "fixed z-50 w-80 bg-popover text-popover-foreground",
              "border border-border rounded-lg shadow-xl",
              "animate-in fade-in-0 zoom-in-95"
            )}
            style={{
              top: `${position.top}px`,
              left: `${position.left}px`,
            }}
            role="dialog"
            aria-label="Onboarding tour"
          >
            {/* Progress bar */}
            <div className="h-1 bg-muted rounded-t-lg overflow-hidden">
              <div
                className="h-full bg-primary transition-all duration-300"
                style={{ width: `${progress}%` }}
              />
            </div>

            {/* Header */}
            <div className="flex items-center justify-between p-4 border-b border-border">
              <h3 className="font-semibold text-lg">{step.title}</h3>
              <button
                onClick={handleSkip}
                className="text-muted-foreground hover:text-foreground transition-colors"
                aria-label="Skip tour"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Content */}
            <div className="p-4">
              <p className="text-sm text-muted-foreground">{step.content}</p>
            </div>

            {/* Footer */}
            <div className="flex items-center justify-between p-4 border-t border-border">
              <span className="text-xs text-muted-foreground">
                {currentStep + 1} of {steps.length}
              </span>
              <div className="flex gap-2">
                <button
                  onClick={handlePrevious}
                  disabled={currentStep === 0}
                  className={cn(
                    "px-3 py-1.5 text-sm rounded-md transition-colors",
                    "hover:bg-accent hover:text-accent-foreground",
                    currentStep === 0 && "opacity-50 cursor-not-allowed"
                  )}
                >
                  <ChevronLeft className="w-4 h-4 inline mr-1" />
                  Previous
                </button>
                <button
                  onClick={handleNext}
                  className="px-3 py-1.5 text-sm bg-primary text-primary-foreground rounded-md hover:bg-primary-hover transition-colors"
                >
                  {currentStep === steps.length - 1 ? "Finish" : "Next"}
                  {currentStep < steps.length - 1 && (
                    <ChevronRight className="w-4 h-4 inline ml-1" />
                  )}
                </button>
              </div>
            </div>
          </div>
        </>,
        document.body
      )
    : null;
}

// Hook to trigger tour programmatically
export function useOnboardingTour(storageKey: string = "onboarding-completed") {
  const resetTour = () => {
    localStorage.removeItem(storageKey);
    window.location.reload();
  };

  const isTourCompleted = () => {
    return localStorage.getItem(storageKey) === "true";
  };

  return { resetTour, isTourCompleted };
}
