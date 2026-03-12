
'use client';

import { useState, useEffect } from 'react';

/**
 * useAnimatedCounter - Core easing logic for numerical value transitions.
 */
export function useAnimatedCounter(value: number, duration: number = 800) {
  const [displayValue, setDisplayValue] = useState(0);

  useEffect(() => {
    let startTimestamp: number | null = null;
    const startValue = displayValue;

    const step = (timestamp: number) => {
      if (!startTimestamp) startTimestamp = timestamp;
      const progress = Math.min((timestamp - startTimestamp) / duration, 1);
      
      // Easing: easeOutQuart
      const easedProgress = 1 - Math.pow(1 - progress, 4);
      const current = startValue + easedProgress * (value - startValue);
      
      setDisplayValue(current);

      if (progress < 1) {
        window.requestAnimationFrame(step);
      }
    };

    window.requestAnimationFrame(step);
  }, [value, duration]);

  return displayValue;
}
