'use client';

import { useEffect, useState } from 'react';

/**
 * ScrollProgress provides a global 2px gradient progress bar at the top of the viewport.
 * Synchronized with the terminal's institutional design tokens.
 * Features real-time tracking and technical shadow glow.
 */
export function ScrollProgress() {
  const [progress, setProgress] = useState(0);
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      const scrollY = window.scrollY;
      const height = document.documentElement.scrollHeight - window.innerHeight;
      
      if (height <= 0) {
        setIsVisible(false);
        return;
      }

      setIsVisible(true);
      const scrolled = (scrollY / height) * 100;
      setProgress(scrolled);
    };

    window.addEventListener('scroll', handleScroll, { passive: true });
    // Initial check for long pages on mount
    setTimeout(handleScroll, 100);

    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  if (!isVisible) return null;

  return (
    <div className="fixed top-0 left-0 right-0 h-[2px] z-[100] pointer-events-none overflow-hidden">
      <div 
        className="h-full bg-gradient-to-r from-primary via-accent to-primary bg-[length:200%_auto] animate-gradient-xy shadow-[0_0_15px_rgba(96,165,250,0.8)] transition-all duration-150 ease-out relative" 
        style={{ width: `${progress}%` }} 
      >
        {/* Terminal Glow Tip */}
        <div className="absolute right-0 top-0 bottom-0 w-4 bg-white/20 blur-sm animate-pulse" />
      </div>
    </div>
  );
}
