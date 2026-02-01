"use client";

import { ReactNode, useEffect } from "react";

interface FileDisplayWrapperProps {
  onClose: () => void;
  onPrev?: () => void;
  onNext?: () => void;
  hasPrev?: boolean;
  hasNext?: boolean;
  children: ReactNode;
}

export default function FileDisplayWrapper({
  onClose,
  onPrev,
  onNext,
  hasPrev = false,
  hasNext = false,
  children,
}: FileDisplayWrapperProps) {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "ArrowLeft" && hasPrev && onPrev) {
        onPrev();
      } else if (e.key === "ArrowRight" && hasNext && onNext) {
        onNext();
      } else if (e.key === "Escape") {
        onClose();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [hasPrev, hasNext, onPrev, onNext, onClose]);

  return (
    <>
      {/* Previous button */}
      {hasPrev && onPrev && (
        <button
          onClick={onPrev}
          className="fixed left-4 top-1/2 -translate-y-1/2 z-[60] rounded-full bg-background-secondary border-2 border-terminal-border p-3 hover:bg-background-tertiary hover:border-neon-green transition-all shadow-terminal"
          aria-label="Previous file"
        >
          <span className="text-2xl text-neon-green">←</span>
        </button>
      )}

      {/* Next button */}
      {hasNext && onNext && (
        <button
          onClick={onNext}
          className="fixed right-4 top-1/2 -translate-y-1/2 z-[60] rounded-full bg-background-secondary border-2 border-terminal-border p-3 hover:bg-background-tertiary hover:border-neon-green transition-all shadow-terminal"
          aria-label="Next file"
        >
          <span className="text-2xl text-neon-green">→</span>
        </button>
      )}

      {children}
    </>
  );
}
