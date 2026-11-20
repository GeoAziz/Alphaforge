import React from 'react';
import { LayoutShell } from '@/components/layout/layout-shell';

export default function TerminalLayout({ children }: { children: React.ReactNode }) {
  return <LayoutShell>{children}</LayoutShell>;
}
