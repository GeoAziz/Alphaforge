'use client';

/**
 * NoiseOverlay provides a global subtle grain texture to the terminal,
 * reinforcing the high-end technical hardware aesthetic.
 */
export function NoiseOverlay() {
  return (
    <div className="fixed inset-0 pointer-events-none z-[100] opacity-[0.03] noise-surface" aria-hidden="true" />
  );
}
