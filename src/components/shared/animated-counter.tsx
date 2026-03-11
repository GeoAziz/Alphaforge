'use client';

import { useEffect, useState } from 'react';

interface AnimatedCounterProps {
  value: number;
  decimals?: number;
  duration?: number;
  prefix?: string;
  suffix?: string;
}

/**
 * AnimatedCounter provides a smooth transition between numerical values.
 * Animates over 600ms using easeOutQuart for smooth deceleration.
 */
export function AnimatedCounter({ 
  value, 
  decimals = 0, 
  duration = 600,
  prefix = '',
  suffix = ''
}: AnimatedCounterProps) {
  const [displayValue, setDisplayValue] = useState(0);

  useEffect(() => {
    // Check for reduced motion preference
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    
    if (prefersReducedMotion) {
      setDisplayValue(value);
      return;
    }

    let startTimestamp: number | null = null;
    const startValue = displayValue;

    const step = (timestamp: number) => {
      if (!startTimestamp) startTimestamp = timestamp;
      const progress = Math.min((timestamp - startTimestamp) / duration, 1);
      
      // Easing function: easeOutQuart
      const easedProgress = 1 - Math.pow(1 - progress, 4);
      
      const current = startValue + easedProgress * (value - startValue);
      setDisplayValue(current);

      if (progress < 1) {
        window.requestAnimationFrame(step);
      }
    };

    window.requestAnimationFrame(step);
  }, [value, duration]);

  return (
    <span className="tabular-nums">
      {prefix}{displayValue.toLocaleString(undefined, {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals,
      })}{suffix}
    </span>
  );
}
