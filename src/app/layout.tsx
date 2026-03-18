import type { Metadata } from 'next';
import './globals.css';
import { SidebarProvider } from '@/components/ui/sidebar';
import { AppSidebar } from '@/components/layout/sidebar';
import { Topbar } from '@/components/layout/topbar';
import { Toaster } from '@/components/ui/toaster';
// FirebaseClientProvider disabled in MVP mock mode — re-enable when upgrading to Blaze plan
// import { FirebaseClientProvider } from '@/firebase/client-provider';
import { MockClientProvider } from '@/firebase/mock-provider';
// OnboardingCheck disabled in mock mode — mock user is always onboarded
// import { OnboardingCheck } from '@/components/onboarding/onboarding-check';
import { LayoutShell } from '@/components/layout/layout-shell';
import { PostHogProvider } from '@/providers/posthog-provider';

export const metadata: Metadata = {
  title: 'AlphaForge | Institutional Grade Signal Intelligence',
  description: 'AI-driven trading signals and institutional grade portfolio intelligence.',
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;900&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet" />
      </head>
      <body className="font-body antialiased noise-surface overflow-hidden">
        {/* MVP Mock Mode with PostHog Analytics */}
        <PostHogProvider>
          <MockClientProvider>
            <LayoutShell>
              {children}
            </LayoutShell>
            <Toaster />
          </MockClientProvider>
        </PostHogProvider>
      </body>
    </html>
  );
}
