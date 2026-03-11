'use client';

import { CSSProperties } from 'react';

interface TerminalGlowProps {
  children: React.ReactNode;
  className?: string;
}

export function TerminalGlow({ children, className = '' }: TerminalGlowProps) {
  const glowStyle: CSSProperties = {
    boxShadow: '0 0 30px rgba(96, 165, 250, 0.4), 0 0 60px rgba(96, 165, 250, 0.2), inset 0 0 30px rgba(96, 165, 250, 0.1)',
    animation: 'terminal-glow 3s ease-in-out infinite',
  };

  return (
    <>
      <style>{`
        @keyframes terminal-glow {
          0% {
            box-shadow: 0 0 20px rgba(96, 165, 250, 0.3), 0 0 40px rgba(96, 165, 250, 0.15);
          }
          50% {
            box-shadow: 0 0 30px rgba(96, 165, 250, 0.5), 0 0 60px rgba(96, 165, 250, 0.25), inset 0 0 30px rgba(96, 165, 250, 0.1);
          }
          100% {
            box-shadow: 0 0 20px rgba(96, 165, 250, 0.3), 0 0 40px rgba(96, 165, 250, 0.15);
          }
        }
        
        @keyframes pulse-glow {
          0%, 100% {
            opacity: 0.5;
            filter: drop-shadow(0 0 8px rgba(96, 165, 250, 0.3));
          }
          50% {
            opacity: 1;
            filter: drop-shadow(0 0 16px rgba(96, 165, 250, 0.6));
          }
        }
      `}</style>
      <div style={glowStyle} className={className}>
        {children}
      </div>
    </>
  );
}
