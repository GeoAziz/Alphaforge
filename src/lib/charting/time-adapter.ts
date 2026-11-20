import { UTCTimestamp } from 'lightweight-charts';

/**
 * Canonical Branded Timestamp Utilities for AlphaForge Supercharts
 * Internal representation: UTC Epoch Milliseconds (int64 integer)
 * Chart representation: UTCTimestamp (seconds integer)
 */

declare const BrandEpochMillis: unique symbol;
export type EpochMillis = number & { readonly [BrandEpochMillis]: true };

declare const BrandChartSeconds: unique symbol;
export type ChartSeconds = number & { readonly [BrandChartSeconds]: true };

/**
 * Validates and brands an integer as UTC Epoch Milliseconds
 */
export function asEpochMillis(val: number): EpochMillis {
  if (!Number.isSafeInteger(val) || val <= 0) {
    throw new Error(`[ChartTimeAdapter] Invalid EpochMillis (must be positive safe integer): ${val}`);
  }
  return val as EpochMillis;
}

/**
 * Validates and brands an integer as Chart UTCTimestamp (seconds)
 */
export function asChartSeconds(val: number): ChartSeconds {
  if (!Number.isSafeInteger(val) || val <= 0) {
    throw new Error(`[ChartTimeAdapter] Invalid ChartSeconds (must be positive safe integer): ${val}`);
  }
  return val as ChartSeconds;
}

/**
 * Converts internal UTC epoch milliseconds to Lightweight Charts UTCTimestamp seconds.
 * Sub-second aggregation policy:
 * Ticks occurring within the same second are aggregated by the candle builder into the active candle bar.
 */
export function toChartTimestamp(epochMillis: EpochMillis): UTCTimestamp {
  return asChartSeconds(Math.floor(epochMillis / 1000)) as unknown as UTCTimestamp;
}

/**
 * Converts Lightweight Charts UTCTimestamp seconds back to internal UTC epoch milliseconds.
 */
export function fromChartTimestamp(chartTime: UTCTimestamp): EpochMillis {
  return asEpochMillis((chartTime as number) * 1000);
}
