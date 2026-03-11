'use client';

import { usePathname } from 'next/navigation';
import { SidebarProvider } from '@/components/ui/sidebar';
import { AppSidebar } from '@/components/layout/sidebar';
import { Topbar } from '@/components/layout/topbar';
import { MobileNav } from '@/components/layout/mobile-nav';
import { CommandPalette } from '@/components/shared/command-palette';
import { ScrollProgress } from '@/components/shared/scroll-progress';
import { NoiseOverlay } from '@/components/shared/noise-overlay';

/**
 * LayoutShell decides whether to render the full Terminal interface 
 * (Sidebar + Topbar) or just the plain content (for Onboarding).
 */
export function LayoutShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const isOnboarding = pathname === '/onboarding';

  if (isOnboarding) {
    return (
      <main className="h-screen w-full bg-background overflow-auto noise-surface">
        <NoiseOverlay />
        {children}
      </main>
    );
  }

  return (
    <SidebarProvider>
      <div className="flex h-screen w-full bg-background noise-surface overflow-hidden">
        <NoiseOverlay />
        <AppSidebar />
        <div className="flex-1 flex flex-col min-w-0 overflow-hidden relative">
          <ScrollProgress />
          <Topbar />
          <main className="flex-1 overflow-y-auto relative pb-16 md:pb-0">
            {children}
          </main>
          <MobileNav />
          <CommandPalette />
        </div>
      </div>
    </SidebarProvider>
  );
}