'use client';

import React from 'react';

// MVP Mock Mode: OnboardingCheck is a pass-through — mock user is always considered onboarded.
// Restore full Firebase-backed logic when upgrading to Blaze plan.
//
// import { useEffect } from 'react';
// import { usePathname, useRouter } from 'next/navigation';
// import { useUser, useFirestore, useDoc, useMemoFirebase } from '@/firebase';
// import { doc } from 'firebase/firestore';
// import { UserProfile } from '@/lib/types';
// import { Loader2 } from 'lucide-react';

/**
 * OnboardingCheck — MVP Mock Mode (pass-through).
 *
 * In mock mode the user is always onboarded, so we just render children.
 *
 * ─────────────────────────────────────────────────────────
 *  TO RESTORE (Firebase Blaze upgrade):
 *  1. Uncomment the imports above
 *  2. Replace this component body with the Firebase-backed version below
 * ─────────────────────────────────────────────────────────
 *
 * Original Firebase implementation (commented out for mock mode):
 *
 * export function OnboardingCheck({ children }: { children: React.ReactNode }) {
 *   const { user, isUserLoading } = useUser();
 *   const db = useFirestore();
 *   const pathname = usePathname();
 *   const router = useRouter();
 *   const profileRef = useMemoFirebase(() => {
 *     if (!user || !db) return null;
 *     return doc(db, 'users', user.uid);
 *   }, [user, db]);
 *   const { data: profile, isLoading: isProfileLoading } = useDoc<UserProfile>(profileRef);
 *   useEffect(() => {
 *     if (isUserLoading || isProfileLoading) return;
 *     if (user && profile && !profile.onboardingComplete && pathname !== '/onboarding') {
 *       router.push('/onboarding');
 *     }
 *   }, [user, profile, isUserLoading, isProfileLoading, pathname, router]);
 *   if (isUserLoading || isProfileLoading) {
 *     return (
 *       <div className="h-screen w-full flex items-center justify-center bg-background">
 *         <Loader2 className="animate-spin text-primary" size={32} />
 *       </div>
 *     );
 *   }
 *   return <>{children}</>;
 * }
 */
export function OnboardingCheck({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
