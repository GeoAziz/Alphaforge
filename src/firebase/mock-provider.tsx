'use client';

import React, { ReactNode } from 'react';
import { FirebaseContext } from '@/firebase/provider';

/**
 * MOCK_USER - Simulated institutional node user for MVP mock mode.
 * Replace with real Firebase Auth user when upgrading to Blaze plan.
 */
export const MOCK_USER = {
  uid: 'mock-user-001',
  email: 'trader@alphaforge.ai',
  displayName: 'Institutional Node 01',
  emailVerified: true,
  isAnonymous: false,
  phoneNumber: null,
  photoURL: null,
  metadata: {
    creationTime: new Date().toISOString(),
    lastSignInTime: new Date().toISOString(),
  },
  providerData: [],
  providerId: 'mock',
  refreshToken: '',
  tenantId: null,
  delete: async () => {},
  getIdToken: async () => 'mock-token',
  getIdTokenResult: async () => ({} as any),
  reload: async () => {},
  toJSON: () => ({}),
} as any;

interface MockClientProviderProps {
  children: ReactNode;
}

/**
 * MockClientProvider - MVP mock mode context provider.
 *
 * Provides a simulated Firebase context with a mock user and no real Firebase
 * services. All data is served from the mock API layer (@/lib/api).
 *
 * ─────────────────────────────────────────────────────────
 *  TO SWITCH TO FIREBASE (Blaze plan):
 *  1. In src/app/layout.tsx, swap <MockClientProvider> back to <FirebaseClientProvider>
 *  2. Remove this file or keep it for testing
 * ─────────────────────────────────────────────────────────
 */
export function MockClientProvider({ children }: MockClientProviderProps) {
  return (
    <FirebaseContext.Provider
      value={{
        areServicesAvailable: false,
        firebaseApp: null,
        firestore: null,
        auth: null,
        user: MOCK_USER,
        isUserLoading: false,
        userError: null,
      }}
    >
      {children}
    </FirebaseContext.Provider>
  );
}
