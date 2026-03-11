'use client';

import { useState, useEffect, useRef } from 'react';

/**
 * useMockRealtime
 * 
 * Provides a high-frequency simulated data stream for a financial terminal feel.
 * It "jitters" the value within a small range to simulate real-time price updates.
 */
export function useMockRealtime(initialValue: number, volatility: number = 0.0002) {
  const [value, setValue] = useState(initialValue);
  const [direction, setDirection] = useState<'up' | 'down' | 'neutral'>('neutral');
  const prevValueRef = useRef(initialValue);
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    if (!initialValue) {
      setValue(0);
      return;
    }
    
    setValue(initialValue);
    prevValueRef.current = initialValue;

    const interval = setInterval(() => {
      // Small random walk (Brownian motion simulation)
      const change = (Math.random() - 0.5) * 2 * initialValue * volatility;
      const newValue = prevValueRef.current + change;
      
      setDirection(newValue > prevValueRef.current ? 'up' : 'down');
      setValue(newValue);
      prevValueRef.current = newValue;

      // Reset flash effect after a short delay for directional visuals
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
      timeoutRef.current = setTimeout(() => setDirection('neutral'), 400);
    }, 600 + Math.random() * 1000); // Institutional jitter frequency

    return () => {
      clearInterval(interval);
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
    };
  }, [initialValue, volatility]);

  return { value, direction };
}