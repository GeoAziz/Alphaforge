'use client';

import { useEffect } from 'react';
import posthog from 'posthog-js';

/**
 * PostHog Provider Component
 * 
 * Initializes PostHog analytics library. User identification is handled
 * by a separate nested component to avoid SSR initialization issues.
 * 
 * Usage in layout.tsx:
 *   export default function RootLayout({children}: {children: React.ReactNode}) {
 *     return (
 *       <PostHogProvider>
 *         {children}
 *       </PostHogProvider>
 *     );
 *   }
 */
export function PostHogProvider({ children }: { children: React.ReactNode }) {
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const apiKey = process.env.NEXT_PUBLIC_POSTHOG_KEY;
      const apiHost = process.env.NEXT_PUBLIC_POSTHOG_HOST || 'https://us.i.posthog.com';

      if (!apiKey) {
        console.warn('[PostHog] NEXT_PUBLIC_POSTHOG_KEY not set, analytics disabled');
        return;
      }

      try {
        posthog.init(apiKey, {
          api_host: apiHost,
          loaded: (ph) => {
            if (process.env.NODE_ENV === 'development') {
              ph.opt_out_capturing();
              console.log('[PostHog] Debug mode enabled (opt-out in development)');
            }
          },
          capture_pageview: true,
          capture_api_calls: false,
          persistence: 'localStorage+cookie',
        });

        console.log('[PostHog] Initialized');

        // Track page view manually for consistency
        if (typeof window !== 'undefined') {
          const handleLocationChange = () => {
            posthog.capture('$pageview', {
              pathname: window.location.pathname,
              hostname: window.location.hostname,
            });
          };

          // Initial page view
          handleLocationChange();

          // Listen for popstate (back/forward)
          window.addEventListener('popstate', handleLocationChange);
          return () => window.removeEventListener('popstate', handleLocationChange);
        }
      } catch (e) {
        console.error('[PostHog] Initialization failed:', e);
      }
    }
  }, []);

  return (
    <>
      {children}
    </>
  );
}

/**
 * Utility functions for tracking events
 */

export const analytics = {
  /**
   * Track page view
   */
  pageView: (pathname: string) => {
    posthog.capture('$pageview', { pathname });
  },

  /**
   * Track feature usage
   */
  featureUsed: (feature: string, properties?: Record<string, any>) => {
    posthog.capture('feature_used', {
      feature,
      ...properties,
    });
  },

  /**
   * Track user action
   */
  action: (action: string, properties?: Record<string, any>) => {
    posthog.capture(action, properties);
  },

  /**
   * Track trade execution
   */
  tradeExecuted: (trade: {
    asset: string;
    quantity: number;
    direction: 'buy' | 'sell';
    type?: string;
    price?: number;
  }) => {
    posthog.capture('trade_executed', {
      asset: trade.asset,
      quantity: trade.quantity,
      direction: trade.direction,
      type: trade.type || 'market',
      price: trade.price,
    });
  },

  /**
   * Track strategy interaction
   */
  strategyInteraction: (
    action: 'viewed' | 'subscribed' | 'unsubscribed' | 'backtested',
    strategyId: string,
    strategyName?: string
  ) => {
    posthog.capture(`strategy_${action}`, {
      strategy_id: strategyId,
      strategy_name: strategyName,
    });
  },

  /**
   * Track signal interaction
   */
  signalInteraction: (
    action: 'viewed' | 'copied' | 'acted_on',
    signalId: string,
    signalType?: string
  ) => {
    posthog.capture(`signal_${action}`, {
      signal_id: signalId,
      signal_type: signalType,
    });
  },

  /**
   * Track portfolio action
   */
  portfolioAction: (
    action: 'viewed' | 'rebalanced' | 'exported',
    properties?: Record<string, any>
  ) => {
    posthog.capture(`portfolio_${action}`, properties);
  },

  /**
   * Track error
   */
  error: (error: Error, context?: Record<string, any>) => {
    posthog.capture('error_occurred', {
      error_message: error.message,
      error_stack: error.stack,
      ...context,
    });
  },

  /**
   * Track form submission
   */
  formSubmitted: (formName: string, success: boolean, properties?: Record<string, any>) => {
    posthog.capture('form_submitted', {
      form_name: formName,
      success,
      ...properties,
    });
  },

  /**
   * Track timing metric
   */
  timing: (metric: string, value: number, unit: string = 'ms') => {
    posthog.capture('timing_metric', {
      metric,
      value,
      unit,
    });
  },
};

/**
 * Hook to use analytics in components
 */
export function useAnalytics() {
  return analytics;
}
