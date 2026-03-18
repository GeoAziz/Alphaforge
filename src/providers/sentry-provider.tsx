'use client';

import { useEffect } from 'react';
import * as Sentry from '@sentry/nextjs';

/**
 * Initialize Sentry error tracking for frontend.
 * 
 * Call this once in your app layout or main provider.
 * 
 * Environment variables required:
 *   NEXT_PUBLIC_SENTRY_DSN: Sentry project DSN
 *   NEXT_PUBLIC_SENTRY_ENVIRONMENT: Environment name
 */
export function initSentry() {
  const dsn = process.env.NEXT_PUBLIC_SENTRY_DSN;
  if (!dsn) {
    console.warn('[Sentry] NEXT_PUBLIC_SENTRY_DSN not set, error tracking disabled');
    return;
  }

  Sentry.init({
    dsn,
    environment: process.env.NEXT_PUBLIC_SENTRY_ENVIRONMENT || 'development',
    tracesSampleRate:
      process.env.NODE_ENV === 'production' ? 0.1 : 1.0,
    release: process.env.NEXT_PUBLIC_APP_VERSION,

    // Session replay
    integrations: [
      new Sentry.Replay({
        maskAllText: true,
        blockAllMedia: true,
      }),
    ],
    replaysSessionSampleRate: 0.1,
    replaysOnErrorSampleRate: 1.0,

    // Ignore certain errors
    beforeSend(event, hint) {
      // Ignore network errors (they're usually not actionable)
      if (event.exception) {
        const error = hint.originalException;
        if (error instanceof TypeError && /fetch|network/i.test(error.message)) {
          return null;
        }
      }
      return event;
    },
  });

  console.log('[Sentry] Initialized');
}

/**
 * Sentry Provider Component
 * 
 * Wrap your app with this to enable error boundaries and error tracking.
 */
export function SentryProvider({ children }: { children: React.ReactNode }) {
  useEffect(() => {
    initSentry();
  }, []);

  return <>{children}</>;
}

/**
 * Error Boundary Component
 * 
 * Usage:
 *   <ErrorBoundary>
 *     <YourComponent />
 *   </ErrorBoundary>
 */
export const ErrorBoundary = Sentry.ErrorBoundary;

/**
 * Utility functions for manual error tracking
 */

export const errorTracking = {
  /**
   * Capture an exception
   */
  captureException: (error: Error, context?: Record<string, any>) => {
    Sentry.withScope((scope) => {
      if (context) {
        Object.entries(context).forEach(([key, value]) => {
          scope.setContext(key, { value });
        });
      }
      Sentry.captureException(error);
    });
  },

  /**
   * Capture a message
   */
  captureMessage: (message: string, level: 'fatal' | 'error' | 'warning' | 'info' = 'info') => {
    Sentry.captureMessage(message, level);
  },

  /**
   * Add breadcrumb (for tracking events leading to error)
   */
  addBreadcrumb: (
    message: string,
    category?: string,
    level?: 'fatal' | 'error' | 'warning' | 'info' | 'debug'
  ) => {
    Sentry.addBreadcrumb({
      message,
      category: category || 'user-action',
      level: level || 'info',
    });
  },

  /**
   * Set user context
   */
  setUser: (userId: string, email?: string, username?: string) => {
    Sentry.setUser({
      id: userId,
      email,
      username,
    });
  },

  /**
   * Clear user context
   */
  clearUser: () => {
    Sentry.setUser(null);
  },

  /**
   * Set custom tag
   */
  setTag: (key: string, value: string | number | boolean) => {
    Sentry.setTag(key, value);
  },

  /**
   * Set context data
   */
  setContext: (key: string, value: Record<string, any>) => {
    Sentry.setContext(key, value);
  },

  /**
   * Start a transaction (for performance monitoring)
   */
  startTransaction: (name: string, op?: string) => {
    return Sentry.startTransaction({
      name,
      op: op || 'http.request',
    });
  },
};

/**
 * Hook to use error tracking in components
 */
export function useErrorTracking() {
  return errorTracking;
}

/**
 * Hook to wrap async functions with error tracking
 */
export function useAsyncWithErrorTracking() {
  return (
    asyncFn: () => Promise<void>,
    context?: Record<string, any>
  ) => {
    return async () => {
      try {
        await asyncFn();
      } catch (error) {
        errorTracking.captureException(error as Error, context);
        throw error;
      }
    };
  };
}
