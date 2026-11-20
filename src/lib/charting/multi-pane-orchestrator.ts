import {
  createChart,
  IChartApi,
  ISeriesApi,
  LogicalRange,
  MouseEventParams,
  ColorType,
  UTCTimestamp,
  PriceScaleMode,
} from 'lightweight-charts';
import { toChartTimestamp, EpochMillis } from '@/lib/charting/time-adapter';
import { OHLCVBar, ChartStyleType } from '@/lib/charting/types';

export interface MultiPaneInitOptions {
  mainContainer: HTMLElement;
  rsiContainer?: HTMLElement;
  chartStyle?: ChartStyleType;
  theme?: 'dark' | 'light';
  onCrosshairMove?: (bar: OHLCVBar | null, rsi?: number) => void;
}

export class SuperchartMultiPaneOrchestrator {
  private mainChart: IChartApi;
  private rsiChart: IChartApi | null = null;
  private mainSeries: ISeriesApi<any>;
  private volumeSeries: ISeriesApi<'Histogram'>;
  private volumeMaSeries: ISeriesApi<'Line'>;
  private rsiSeries: ISeriesApi<'Line'> | null = null;

  private boundMainRangeHandler: (range: LogicalRange | null) => void;
  private boundRsiRangeHandler: ((range: LogicalRange | null) => void) | null = null;
  private boundMainCrosshairHandler: (param: MouseEventParams) => void;
  private boundRsiCrosshairHandler: ((param: MouseEventParams) => void) | null = null;

  private isBroadcastingRange = false;
  private currentBars: OHLCVBar[] = [];
  private rsiDataMap: Map<number, number> = new Map();
  private onCrosshairMoveCallback?: (bar: OHLCVBar | null, rsi?: number) => void;

  constructor(options: MultiPaneInitOptions) {
    this.onCrosshairMoveCallback = options.onCrosshairMove;
    const isDark = options.theme !== 'light';
    const bg = isDark ? '#131722' : '#ffffff';
    const textColor = isDark ? '#d1d4dc' : '#131722';
    const gridColor = isDark ? 'rgba(42, 46, 57, 0.4)' : 'rgba(230, 230, 230, 0.4)';

    // 1. Initialize Main Canvas
    this.mainChart = createChart(options.mainContainer, {
      width: options.mainContainer.clientWidth || 800,
      height: options.mainContainer.clientHeight || 480,
      layout: {
        background: { type: ColorType.Solid, color: bg },
        textColor: textColor,
        fontFamily: "-apple-system, BlinkMacSystemFont, 'Trebuchet MS', Roboto, Ubuntu, sans-serif",
      },
      grid: {
        vertLines: { color: gridColor },
        horzLines: { color: gridColor },
      },
      timeScale: {
        visible: !options.rsiContainer,
        timeVisible: true,
        secondsVisible: false,
        borderColor: '#2a2e39',
      },
      rightPriceScale: {
        borderColor: '#2a2e39',
        autoScale: true,
      },
      crosshair: {
        vertLine: { color: isDark ? '#758696' : '#9B9B9B', width: 1, style: 3 },
        horzLine: { color: isDark ? '#758696' : '#9B9B9B', width: 1, style: 3 },
      },
    });

    // 2. Setup Primary Price Series
    this.mainSeries = this.createPriceSeries(options.chartStyle || 'candlestick');

    // 3. Setup Volume Histogram overlaid on separate price scale with 20MA
    this.volumeSeries = this.mainChart.addHistogramSeries({
      color: '#26a69a',
      priceFormat: { type: 'volume' },
      priceScaleId: 'volume',
    });
    this.mainChart.priceScale('volume').applyOptions({
      scaleMargins: {
        top: 0.8, // Takes bottom 20%
        bottom: 0,
      },
    });

    this.volumeMaSeries = this.mainChart.addLineSeries({
      color: '#2962ff',
      lineWidth: 1,
      priceScaleId: 'volume',
    });

    // 4. Setup RSI Sub-Pane
    if (options.rsiContainer) {
      this.rsiChart = createChart(options.rsiContainer, {
        width: options.rsiContainer.clientWidth || 800,
        height: options.rsiContainer.clientHeight || 150,
        layout: {
          background: { type: ColorType.Solid, color: bg },
          textColor: textColor,
          fontFamily: "-apple-system, BlinkMacSystemFont, 'Trebuchet MS', Roboto, Ubuntu, sans-serif",
        },
        grid: {
          vertLines: { color: gridColor },
          horzLines: { color: gridColor },
        },
        timeScale: {
          visible: true,
          timeVisible: true,
          secondsVisible: false,
          borderColor: '#2a2e39',
        },
        rightPriceScale: {
          borderColor: '#2a2e39',
          autoScale: true,
        },
      });

      this.rsiSeries = this.rsiChart.addLineSeries({
        color: '#7e57c2',
        lineWidth: 2,
        priceFormat: { type: 'price', precision: 1, minMove: 0.1 },
      });
    }

    // 5. Crosshair and Range Listeners
    this.boundMainRangeHandler = (range: LogicalRange | null) => {
      if (!range || this.isBroadcastingRange || !this.rsiChart) return;
      this.isBroadcastingRange = true;
      try {
        this.rsiChart.timeScale().setVisibleLogicalRange(range);
      } finally {
        this.isBroadcastingRange = false;
      }
    };

    this.boundMainCrosshairHandler = (param: MouseEventParams) => {
      if (!param.point || !param.time) {
        if (this.rsiChart) this.rsiChart.clearCrosshairPosition();
        if (this.onCrosshairMoveCallback) this.onCrosshairMoveCallback(null);
        return;
      }
      const timeSeconds = param.time as number;
      const targetVal = this.rsiDataMap.get(timeSeconds);
      if (this.rsiChart && this.rsiSeries) {
        if (targetVal !== undefined) {
          this.rsiChart.setCrosshairPosition(targetVal, param.time, this.rsiSeries);
        } else {
          this.rsiChart.clearCrosshairPosition();
        }
      }

      if (this.onCrosshairMoveCallback) {
        const found = this.currentBars.find(b => toChartTimestamp(b.time) === timeSeconds);
        this.onCrosshairMoveCallback(found || null, targetVal);
      }
    };

    this.mainChart.timeScale().subscribeVisibleLogicalRangeChange(this.boundMainRangeHandler);
    this.mainChart.subscribeCrosshairMove(this.boundMainCrosshairHandler);

    if (this.rsiChart) {
      this.boundRsiRangeHandler = (range: LogicalRange | null) => {
        if (!range || this.isBroadcastingRange) return;
        this.isBroadcastingRange = true;
        try {
          this.mainChart.timeScale().setVisibleLogicalRange(range);
        } finally {
          this.isBroadcastingRange = false;
        }
      };

      this.boundRsiCrosshairHandler = (param: MouseEventParams) => {
        if (!param.point || !param.time) {
          this.mainChart.clearCrosshairPosition();
          return;
        }
        const timeSeconds = param.time as number;
        const candle = this.currentBars.find(b => toChartTimestamp(b.time) === timeSeconds);
        if (candle) {
          this.mainChart.setCrosshairPosition(candle.close, param.time, this.mainSeries);
        } else {
          this.mainChart.clearCrosshairPosition();
        }
      };

      this.rsiChart.timeScale().subscribeVisibleLogicalRangeChange(this.boundRsiRangeHandler);
      this.rsiChart.subscribeCrosshairMove(this.boundRsiCrosshairHandler);
    }
  }

  private createPriceSeries(style: ChartStyleType) {
    if (style === 'area') {
      return this.mainChart.addAreaSeries({
        topColor: 'rgba(41, 98, 255, 0.5)',
        bottomColor: 'rgba(41, 98, 255, 0.0)',
        lineColor: '#2962ff',
        lineWidth: 2,
      });
    }
    if (style === 'line') {
      return this.mainChart.addLineSeries({
        color: '#2962ff',
        lineWidth: 2,
      });
    }
    if (style === 'bar') {
      return this.mainChart.addBarSeries({
        upColor: '#089981',
        downColor: '#f23645',
      });
    }
    return this.mainChart.addCandlestickSeries({
      upColor: '#089981',
      downColor: '#f23645',
      borderUpColor: '#089981',
      borderDownColor: '#f23645',
      wickUpColor: '#089981',
      wickDownColor: '#f23645',
    });
  }

  public setData(bars: OHLCVBar[]) {
    this.currentBars = bars;
    const priceData = bars.map(b => ({
      time: toChartTimestamp(b.time),
      open: b.open,
      high: b.high,
      low: b.low,
      close: b.close,
      value: b.close,
    }));

    const volData = bars.map(b => ({
      time: toChartTimestamp(b.time),
      value: b.volume,
      color: b.close >= b.open ? 'rgba(8, 153, 129, 0.6)' : 'rgba(242, 54, 69, 0.6)',
    }));

    // Calculate 20-period volume SMA
    const volMaData: { time: UTCTimestamp; value: number }[] = [];
    let volSum = 0;
    const period = 20;
    for (let i = 0; i < bars.length; i++) {
      volSum += bars[i].volume;
      if (i >= period) volSum -= bars[i - period].volume;
      const count = Math.min(i + 1, period);
      volMaData.push({
        time: toChartTimestamp(bars[i].time),
        value: volSum / count,
      });
    }

    this.mainSeries.setData(priceData);
    this.volumeSeries.setData(volData);
    this.volumeMaSeries.setData(volMaData);

    if (this.rsiSeries) {
      const rsiResults = this.computeRSI(bars, 14);
      this.rsiDataMap.clear();
      rsiResults.forEach(r => this.rsiDataMap.set(r.time as number, r.value));
      this.rsiSeries.setData(rsiResults);
    }
  }

  public update(bar: OHLCVBar) {
    const chartTime = toChartTimestamp(bar.time);
    this.mainSeries.update({
      time: chartTime,
      open: bar.open,
      high: bar.high,
      low: bar.low,
      close: bar.close,
      value: bar.close,
    });

    this.volumeSeries.update({
      time: chartTime,
      value: bar.volume,
      color: bar.close >= bar.open ? 'rgba(8, 153, 129, 0.6)' : 'rgba(242, 54, 69, 0.6)',
    });
  }

  public setVisibleRange(from: UTCTimestamp, to: UTCTimestamp) {
    this.mainChart.timeScale().setVisibleRange({ from, to });
    if (this.rsiChart) {
      this.rsiChart.timeScale().setVisibleRange({ from, to });
    }
  }

  public setPriceScaleMode(mode: 'normal' | 'log' | 'percentage') {
    const pMode =
      mode === 'log'
        ? PriceScaleMode.Logarithmic
        : mode === 'percentage'
        ? PriceScaleMode.Percentage
        : PriceScaleMode.Normal;

    this.mainChart.priceScale('right').applyOptions({ mode: pMode });
  }

  public getChartApi(): IChartApi {
    return this.mainChart;
  }

  public getMainSeries(): ISeriesApi<any> {
    return this.mainSeries;
  }

  public resize(width: number, height: number, rsiHeight = 140) {
    if (this.rsiChart) {
      const mainHeight = Math.max(200, height - rsiHeight);
      this.mainChart.applyOptions({ width, height: mainHeight });
      this.rsiChart.applyOptions({ width, height: rsiHeight });
    } else {
      this.mainChart.applyOptions({ width, height });
    }
  }

  private computeRSI(candles: OHLCVBar[], period = 14): { time: UTCTimestamp; value: number }[] {
    if (candles.length <= period) return [];
    const results: { time: UTCTimestamp; value: number }[] = [];

    let gains = 0;
    let losses = 0;

    for (let i = 1; i <= period; i++) {
      const diff = candles[i].close - candles[i - 1].close;
      if (diff >= 0) gains += diff;
      else losses -= diff;
    }

    let avgGain = gains / period;
    let avgLoss = losses / period;

    const firstRS = avgLoss === 0 ? 100 : avgGain / avgLoss;
    const firstRSI = avgLoss === 0 ? 100 : 100 - (100 / (1 + firstRS));
    results.push({ time: toChartTimestamp(candles[period].time), value: firstRSI });

    for (let i = period + 1; i < candles.length; i++) {
      const diff = candles[i].close - candles[i - 1].close;
      const gain = diff > 0 ? diff : 0;
      const loss = diff < 0 ? -diff : 0;

      avgGain = (avgGain * (period - 1) + gain) / period;
      avgLoss = (avgLoss * (period - 1) + loss) / period;

      const rs = avgLoss === 0 ? 100 : avgGain / avgLoss;
      const rsi = avgLoss === 0 ? 100 : 100 - (100 / (1 + rs));
      results.push({ time: toChartTimestamp(candles[i].time), value: rsi });
    }

    return results;
  }

  public destroy(): void {
    this.mainChart.timeScale().unsubscribeVisibleLogicalRangeChange(this.boundMainRangeHandler);
    this.mainChart.unsubscribeCrosshairMove(this.boundMainCrosshairHandler);

    if (this.rsiChart && this.boundRsiRangeHandler && this.boundRsiCrosshairHandler) {
      this.rsiChart.timeScale().unsubscribeVisibleLogicalRangeChange(this.boundRsiRangeHandler);
      this.rsiChart.unsubscribeCrosshairMove(this.boundRsiCrosshairHandler);
      this.rsiChart.remove();
      this.rsiChart = null;
    }

    this.mainChart.remove();
  }
}
