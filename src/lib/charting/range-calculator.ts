import { UTCTimestamp } from 'lightweight-charts';

export type RangePreset = '1D' | '5D' | '1M' | '3M' | '6M' | 'YTD' | '1Y' | '5Y' | 'All';

export interface RangeBoundaries {
  from: UTCTimestamp;
  to: UTCTimestamp;
}

/**
 * Calculates session-aware visible ranges for equities, crypto, and forex.
 */
export class CalendarRangeCalculator {
  public static calculateRange(
    preset: RangePreset,
    assetType: 'crypto' | 'stock' | 'index' | 'forex' | 'futures',
    currentBarsTime: { first: number; last: number }
  ): RangeBoundaries {
    const now = Math.floor(Date.now() / 1000);
    const to = (currentBarsTime.last || now) as UTCTimestamp;

    switch (preset) {
      case '1D': {
        if (assetType === 'crypto') {
          // 24 hours back
          return { from: (to - 86400) as UTCTimestamp, to };
        }
        // Equities/Index: 1 session (approx 24h of chart time window)
        return { from: (to - 86400) as UTCTimestamp, to };
      }
      case '5D': {
        const days = assetType === 'stock' || assetType === 'index' ? 7 : 5;
        return { from: (to - days * 86400) as UTCTimestamp, to };
      }
      case '1M': {
        return { from: (to - 30 * 86400) as UTCTimestamp, to };
      }
      case '3M': {
        return { from: (to - 90 * 86400) as UTCTimestamp, to };
      }
      case '6M': {
        return { from: (to - 180 * 86400) as UTCTimestamp, to };
      }
      case 'YTD': {
        const currentYear = new Date().getUTCFullYear();
        const startOfYear = Math.floor(Date.UTC(currentYear, 0, 1) / 1000);
        return { from: Math.max(startOfYear, currentBarsTime.first) as UTCTimestamp, to };
      }
      case '1Y': {
        return { from: (to - 365 * 86400) as UTCTimestamp, to };
      }
      case '5Y': {
        return { from: (to - 5 * 365 * 86400) as UTCTimestamp, to };
      }
      case 'All':
      default: {
        return { from: currentBarsTime.first as UTCTimestamp, to };
      }
    }
  }
}
