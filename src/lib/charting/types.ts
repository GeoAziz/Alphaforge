import { UTCTimestamp } from 'lightweight-charts';
import { EpochMillis } from '@/lib/charting/time-adapter';

export type ChartStyleType = 'candlestick' | 'bar' | 'area' | 'line' | 'baseline' | 'heikin_ashi';
export type FeedClassification = 'live' | 'delayed_15m' | 'indicative' | 'stale';

export interface ChartInstrument {
  symbol: string;
  ticker: string;
  name: string;
  exchange: string;
  type: 'crypto' | 'stock' | 'index' | 'forex' | 'futures';
  pricePrecision: number;
  minMove: number;
  feedClassification: FeedClassification;
  sector?: string;
  currency?: string;
}

export interface OHLCVBar {
  time: EpochMillis;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface WatchlistSymbol {
  symbol: string;
  name: string;
  category: 'INDICES' | 'STOCKS' | 'CRYPTO' | 'FUTURES';
  price: number;
  change24h: number;
  change24hPct: number;
  volume24h: number;
  isUp: boolean;
  preMarketPrice?: number;
  preMarketChangePct?: number;
  avgVolume30D?: number;
  range52wLow?: number;
  range52wHigh?: number;
  keyFacts?: string;
}

export type DrawingToolType =
  // Cursor
  | 'cursor_crosshair' | 'cursor_dot' | 'cursor_arrow' | 'cursor_eraser'
  // Lines & Rays
  | 'trendline' | 'info_line' | 'trend_angle' | 'horizontal_line' | 'horizontal_ray' | 'vertical_line' | 'parallel_channel'
  // Gann & Fib
  | 'fib_retracement' | 'fib_extension' | 'fib_channel' | 'fib_timezone'
  // Shapes
  | 'brush' | 'highlighter' | 'rectangle' | 'ellipse' | 'path' | 'curve'
  // Text
  | 'text' | 'anchored_text' | 'callout' | 'price_label'
  // Patterns
  | 'head_and_shoulders' | 'elliott_wave_15' | 'triangle_pattern'
  // Prediction & Measurement
  | 'long_position' | 'short_position' | 'price_range_ruler' | 'date_range_ruler';

export interface ChartDrawingAnchor {
  time: UTCTimestamp; // in seconds for Lightweight Charts
  price: number;
}

export interface ChartDrawingEntity {
  id: string;
  type: DrawingToolType;
  instrument: string;
  anchors: ChartDrawingAnchor[];
  properties: {
    color: string;
    lineWidth: number;
    lineStyle: 'solid' | 'dashed' | 'dotted';
    fillColor?: string;
    opacity?: number;
    fontSize?: number;
    showPrices?: boolean;
    showPercentages?: boolean;
    extendLeft?: boolean;
    extendRight?: boolean;
    customParams?: Record<string, any>;
  };
  locked: boolean;
  visible: boolean;
  zIndex: number;
  createdAt: number;
  updatedAt: number;
}

export interface IndicatorInstance {
  id: string;
  name: string;
  type: 'RSI' | 'MACD' | 'EMA' | 'BB' | 'SMA' | 'VWAP';
  params: Record<string, number>;
  visible: boolean;
  paneIndex: number;
}
