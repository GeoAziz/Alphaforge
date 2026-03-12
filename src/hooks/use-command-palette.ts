
'use client';

import { useState, useEffect, useCallback } from 'react';

/**
 * useCommandPalette - Keyboard listener for terminal handshake (⌘K).
 */
export function useCommandPalette() {
  const [isOpen, setIsOpen] = useState(false);

  const toggle = useCallback(() => setIsOpen(prev => !prev), []);
  const open = useCallback(() => setIsOpen(true), []);
  const close = useCallback(() => setIsOpen(false), []);

  useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if (e.key === 'k' && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        toggle();
      }
    };

    document.addEventListener('keydown', down);
    return () => document.removeEventListener('keydown', down);
  }, [toggle]);

  return { isOpen, open, close, toggle, setIsOpen };
}
