'use client';

import { useEffect, useState } from 'react';

/**
 * ScrollProgress provides a global 2px gradient progress bar at the top of the viewport.
 * Synchronized with the terminal's institutional design tokens.
 */
export function ScrollProgress() {
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    const handleScroll = () => {
      const scrollY = window.scrollY;
      const height = document.documentElement.scrollHeight - window.innerHeight;
      const scrolled = (scrollY / height) * 100;
      setProgress(scrolled);
    };

    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <div className="fixed top-0 left-0 right-0 h-[2px] z-[100] pointer-events-none">
      <div 
        className="h-full bg-gradient-to-r from-primary via-accent to-primary bg-[length:200%_auto] animate-gradient-xy shadow-[0_0_15px_rgba(96,165,250,0.5)] transition-all duration-150 ease-out" 
        style={{ width: `${progress}%` }} 
      />
    </div>
  );
}
