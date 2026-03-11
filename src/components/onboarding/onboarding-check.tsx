'use client';

import { useEffect } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import { useUser, useFirestore, useDoc, useMemoFirebase } from '@/firebase';
import { doc } from 'firebase/firestore';
import { UserProfile } from '@/lib/types';
import { Loader2 } from 'lucide-react';

/**
 * OnboardingCheck enforces the institutional handshake.
 * If a user is logged in but hasn't completed onboarding, they are redirected.
 * It also controls the visibility of the terminal shell (sidebar/topbar).
 */
export function OnboardingCheck({ children }: { children: React.ReactNode }) {
  const { user, isUserLoading } = useUser();
  const db = useFirestore();
  const pathname = usePathname();
  const router = useRouter();

  const profileRef = useMemoFirebase(() => {
    if (!user || !db) return null;
    return doc(db, 'users', user.uid);
  }, [user, db]);

  const { data: profile, isLoading: isProfileLoading } = useDoc<UserProfile>(profileRef);

  useEffect(() => {
    if (isUserLoading || isProfileLoading) return;

    // Redirect to onboarding if not complete
    if (user && profile && !profile.onboardingComplete && pathname !== '/onboarding') {
      router.push('/onboarding');
    }
  }, [user, profile, isUserLoading, isProfileLoading, pathname, router]);

  // Loading state for terminal initialization
  if (isUserLoading || isProfileLoading) {
    return (
      <div className="h-screen w-full flex items-center justify-center bg-background">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="animate-spin text-primary" size={32} />
          <span className="text-[10px] font-black uppercase tracking-widest text-text-muted">Calibrating Node...</span>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}
