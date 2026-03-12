
'use client';

import { useState, useEffect } from 'react';

/**
 * useMediaQuery - Simple responsive breakpoint detection.
 */
export function useMediaQuery(query: string) {
  const [matches, setValue] = useState(false);

  useEffect(() => {
    const handler = (e: MediaQueryListEvent) => setValue(e.matches);
    const mediaQueryList = window.matchMedia(query);
    
    setValue(mediaQueryList.matches);
    mediaQueryList.addEventListener('change', handler);

    return () => mediaQueryList.removeEventListener('change', handler);
  }, [query]);

  return matches;
}
