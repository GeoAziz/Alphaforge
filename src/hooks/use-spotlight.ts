
'use client';

import { useState, useCallback, RefObject } from 'react';

/**
 * useSpotlight - Tracks relative mouse position for cursor-following glow effects.
 */
export function useSpotlight(ref: RefObject<HTMLElement | null>) {
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const [opacity, setOpacity] = useState(0);

  const handleMouseMove = useCallback((e: React.MouseEvent | MouseEvent) => {
    if (!ref.current) return;

    const rect = ref.current.getBoundingClientRect();
    setPosition({
      x: e.clientX - rect.left,
      y: e.clientY - rect.top,
    });
  }, [ref]);

  const handleMouseEnter = useCallback(() => setOpacity(1), []);
  const handleMouseLeave = useCallback(() => setOpacity(0), []);

  return {
    position,
    opacity,
    handleMouseMove,
    handleMouseEnter,
    handleMouseLeave,
  };
}
