'use client';

import { useEffect, useRef, useState, useCallback } from 'react';
import { SuperchartMultiPaneOrchestrator } from '@/lib/charting/multi-pane-orchestrator';
import { CanvasDrawingEngine } from '@/lib/charting/drawing-engine';
import { CalendarRangeCalculator, RangePreset } from '@/lib/charting/range-calculator';
import { 
  OHLCVBar, 
  ChartStyleType, 
  ChartInstrument, 
  WatchlistSymbol, 
  DrawingToolType, 
  ChartDrawingEntity 
} from '@/lib/charting/types';
import { asEpochMillis } from '@/lib/charting/time-adapter';

// Workstation Subcomponents
import { TopToolbar } from '@/components/supercharts/top-toolbar';
import { DrawingToolbar } from '@/components/supercharts/drawing-toolbar';
import { BottomTimeBar } from '@/components/supercharts/bottom-time-bar';
import { InChartLegend } from '@/components/supercharts/in-chart-legend';
import { QuickExecutionWidget } from '@/components/supercharts/quick-execution-widget';
import { RightDock } from '@/components/supercharts/right-dock/right-dock';

const INSTRUMENTS: ChartInstrument[] = [
  { symbol: 'AAPL', ticker: 'AAPL', name: 'Apple Inc.', exchange: 'NASDAQ', type: 'stock', pricePrecision: 2, minMove: 0.01, feedClassification: 'live', sector: 'Electronic Technology' },
  { symbol: 'BTCUSDT', ticker: 'BTC/USDT', name: 'Bitcoin / TetherUS', exchange: 'Binance', type: 'crypto', pricePrecision: 2, minMove: 0.01, feedClassification: 'live' },
  { symbol: 'ETHUSDT', ticker: 'ETH/USDT', name: 'Ethereum / TetherUS', exchange: 'Binance', type: 'crypto', pricePrecision: 2, minMove: 0.01, feedClassification: 'live' },
  { symbol: 'SOLUSDT', ticker: 'SOL/USDT', name: 'Solana / TetherUS', exchange: 'Binance', type: 'crypto', pricePrecision: 2, minMove: 0.01, feedClassification: 'live' },
  { symbol: 'NVDA', ticker: 'NVDA', name: 'NVIDIA Corporation', exchange: 'NASDAQ', type: 'stock', pricePrecision: 2, minMove: 0.01, feedClassification: 'delayed_15m', sector: 'Semiconductors' },
  { symbol: 'SPX', ticker: 'SPX', name: 'S&P 500 Index Proxy', exchange: 'US Markets', type: 'index', pricePrecision: 2, minMove: 0.1, feedClassification: 'indicative' },
];

const WATCHLIST_ITEMS: WatchlistSymbol[] = [
  { symbol: 'AAPL', name: 'Apple Inc', category: 'STOCKS', price: 349.21, change24h: -3.24, change24hPct: -0.92, volume24h: 40910230, isUp: false, preMarketPrice: 350.43, preMarketChangePct: 0.35, avgVolume30D: 45320000, keyFacts: 'Apple reported its highest fiscal quarter records for services and iPhone revenue with strong gross margins.' },
  { symbol: 'BTCUSDT', name: 'Bitcoin', category: 'CRYPTO', price: 68450.20, change24h: 2260.40, change24hPct: 3.42, volume24h: 34120000, isUp: true, keyFacts: 'Bitcoin network hash rate reached an all-time high amid institutional ETF inflows.' },
  { symbol: 'ETHUSDT', name: 'Ethereum', category: 'CRYPTO', price: 3540.80, change24h: -41.20, change24hPct: -1.15, volume24h: 18240000, isUp: false, keyFacts: 'Ethereum Layer 2 gas throughput surges following recent network blob space optimization.' },
  { symbol: 'SOLUSDT', name: 'Solana', category: 'CRYPTO', price: 184.60, change24h: 10.15, change24hPct: 5.82, volume24h: 9410000, isUp: true, keyFacts: 'Solana decentralized exchange trading volume surpasses major peers for the third consecutive week.' },
  { symbol: 'NVDA', name: 'NVIDIA Corp', category: 'STOCKS', price: 142.80, change24h: 3.05, change24hPct: 2.18, volume24h: 52100000, isUp: true, keyFacts: 'Data center AI chip architecture demand maintains robust momentum across hyperscalers.' },
  { symbol: 'SPX', name: 'S&P 500 Proxy', category: 'INDICES', price: 5885.20, change24h: 25.80, change24hPct: 0.44, volume24h: 421000000, isUp: true, keyFacts: 'Broad market benchmark approaches record highs led by technology and consumer discretionary.' },
];

export function SuperchartsWorkstation() {
  const mainContainerRef = useRef<HTMLDivElement>(null);
  const rsiContainerRef = useRef<HTMLDivElement>(null);
  const drawingCanvasRef = useRef<HTMLCanvasElement>(null);

  const orchestratorRef = useRef<SuperchartMultiPaneOrchestrator | null>(null);
  const drawingEngineRef = useRef<CanvasDrawingEngine | null>(null);

  const [activeInstrument, setActiveInstrument] = useState<ChartInstrument>(INSTRUMENTS[0]);
  const [activeInterval, setActiveInterval] = useState('1D');
  const [activeStyle, setActiveStyle] = useState<ChartStyleType>('candlestick');
  const [activeRange, setActiveRange] = useState<RangePreset>('1Y');
  const [scaleMode, setScaleMode] = useState<'normal' | 'log' | 'percentage'>('normal');
  const [activeTool, setActiveTool] = useState<DrawingToolType>('cursor_crosshair');
  const [magnetMode, setMagnetMode] = useState<'off' | 'weak' | 'strong'>('off');

  const [showRSI, setShowRSI] = useState(false);
  const [hoveredBar, setHoveredBar] = useState<OHLCVBar | null>(null);
  const [hoveredRsi, setHoveredRsi] = useState<number | undefined>(undefined);
  const [lastBar, setLastBar] = useState<OHLCVBar | null>(null);

  // Generate historical baseline
  const generateHistoricalBars = useCallback((basePrice: number, count = 180): OHLCVBar[] => {
    const bars: OHLCVBar[] = [];
    let current = basePrice;
    const now = Date.now();
    const intervalMs = 86400000;

    for (let i = count; i >= 0; i--) {
      const time = asEpochMillis(now - i * intervalMs);
      const delta = (Math.random() - 0.48) * (current * 0.025);
      const open = current;
      const close = current + delta;
      const high = Math.max(open, close) + Math.random() * (current * 0.015);
      const low = Math.min(open, close) - Math.random() * (current * 0.015);
      const volume = Math.floor(Math.random() * 8000 + 1200);
      current = close;

      bars.push({ time, open, high, low, close, volume });
    }
    return bars;
  }, []);

  // Initialize Orchestrator & Drawing Engine
  useEffect(() => {
    if (!mainContainerRef.current) return;

    const orchestrator = new SuperchartMultiPaneOrchestrator({
      mainContainer: mainContainerRef.current,
      rsiContainer: showRSI && rsiContainerRef.current ? rsiContainerRef.current : undefined,
      chartStyle: activeStyle,
      theme: 'dark',
      onCrosshairMove: (bar, rsi) => {
        setHoveredBar(bar);
        setHoveredRsi(rsi);
      },
    });
    orchestratorRef.current = orchestrator;

    const initialBars = generateHistoricalBars(activeInstrument.symbol === 'AAPL' ? 349.21 : 68450.20, 220);
    orchestrator.setData(initialBars);
    setLastBar(initialBars[initialBars.length - 1]);

    // Initialize Drawing Engine Canvas
    if (drawingCanvasRef.current) {
      drawingEngineRef.current = new CanvasDrawingEngine(
        drawingCanvasRef.current,
        orchestrator.getChartApi(),
        orchestrator.getMainSeries()
      );
    }

    const handleResize = () => {
      if (mainContainerRef.current && orchestratorRef.current) {
        const width = mainContainerRef.current.clientWidth;
        const totalHeight = mainContainerRef.current.parentElement?.clientHeight || 600;
        const rsiH = showRSI ? 140 : 0;
        orchestratorRef.current.resize(width, totalHeight, rsiH);

        if (drawingCanvasRef.current && drawingEngineRef.current) {
          const mainH = Math.max(200, totalHeight - rsiH);
          drawingEngineRef.current.resize(width, mainH);
        }
      }
    };

    window.addEventListener('resize', handleResize);
    handleResize();

    // Live Streaming Simulator
    const interval = setInterval(() => {
      if (!orchestratorRef.current || !lastBar) return;
      const tickDelta = (Math.random() - 0.49) * (lastBar.close * 0.002);
      const newClose = Number((lastBar.close + tickDelta).toFixed(2));

      const updatedLiveBar: OHLCVBar = {
        time: asEpochMillis(Date.now()),
        open: lastBar.open,
        high: Math.max(lastBar.high, newClose),
        low: Math.min(lastBar.low, newClose),
        close: newClose,
        volume: lastBar.volume + Math.floor(Math.random() * 50),
      };
      setLastBar(updatedLiveBar);
      orchestratorRef.current.update(updatedLiveBar);
    }, 1500);

    return () => {
      clearInterval(interval);
      window.removeEventListener('resize', handleResize);
      orchestrator.destroy();
      orchestratorRef.current = null;
      drawingEngineRef.current = null;
    };
  }, [activeInstrument, activeStyle, showRSI, generateHistoricalBars]);

  // Handle Range Preset changes
  const handleSelectRange = (range: RangePreset) => {
    setActiveRange(range);
    if (!orchestratorRef.current || !lastBar) return;
    const boundaries = CalendarRangeCalculator.calculateRange(
      range,
      activeInstrument.type,
      { first: Math.floor(Date.now() / 1000) - 220 * 86400, last: Math.floor(Date.now() / 1000) }
    );
    orchestratorRef.current.setVisibleRange(boundaries.from, boundaries.to);
  };

  const handleToggleScale = (mode: 'normal' | 'log' | 'percentage') => {
    setScaleMode(mode);
    if (orchestratorRef.current) {
      orchestratorRef.current.setPriceScaleMode(mode);
    }
  };

  const handleSelectTool = (tool: DrawingToolType) => {
    setActiveTool(tool);
    if (drawingEngineRef.current) {
      drawingEngineRef.current.setActiveTool(tool);
    }
  };

  const handleToggleMagnet = () => {
    const next = magnetMode === 'off' ? 'weak' : magnetMode === 'weak' ? 'strong' : 'off';
    setMagnetMode(next);
    if (drawingEngineRef.current) {
      drawingEngineRef.current.setMagnetMode(next);
    }
  };

  return (
    <div className="flex flex-col h-screen w-full bg-[#131722] text-[#d1d4dc] select-none overflow-hidden font-[-apple-system,BlinkMacSystemFont,'Trebuchet_MS',Roboto,Ubuntu,sans-serif]">
      {/* 1. TOP INTERACTION & INTERVAL BAR */}
      <TopToolbar
        activeInstrument={activeInstrument}
        activeInterval={activeInterval}
        activeStyle={activeStyle}
        showRSI={showRSI}
        onSymbolClick={() => {
          const nextIdx = (INSTRUMENTS.findIndex(i => i.symbol === activeInstrument.symbol) + 1) % INSTRUMENTS.length;
          setActiveInstrument(INSTRUMENTS[nextIdx]);
        }}
        onIntervalChange={setActiveInterval}
        onStyleChange={setActiveStyle}
        onToggleRSI={() => setShowRSI(!showRSI)}
        onOpenAlertModal={() => alert(`Create alert for ${activeInstrument.ticker}`)}
        onToggleReplay={() => alert('Bar Replay mode activated: click on historical bar to truncate')}
        onOpenSettings={() => alert('Chart Properties & Theme Settings')}
        onFullscreen={() => {
          if (!document.fullscreenElement) document.documentElement.requestFullscreen();
          else document.exitFullscreen();
        }}
        onTakeScreenshot={() => alert('Screenshot captured & copied to clipboard!')}
      />

      {/* 2. MAIN WORKSPACE VIEWPORT */}
      <div className="flex-1 flex w-full relative overflow-hidden">
        {/* Left 28-Tool Drawing Palette */}
        <DrawingToolbar
          activeTool={activeTool}
          magnetMode={magnetMode}
          onSelectTool={handleSelectTool}
          onToggleMagnet={handleToggleMagnet}
          onDeleteSelected={() => drawingEngineRef.current?.deleteSelected()}
          onClearAll={() => drawingEngineRef.current?.clearAll()}
        />

        {/* Center Multi-Pane Canvas Container */}
        <div className="flex-1 flex flex-col h-full bg-[#131722] overflow-hidden relative">
          {/* Main Chart Pane with Overlays */}
          <div className="flex-1 w-full relative overflow-hidden">
            {/* IN-CHART LEGEND */}
            <InChartLegend
              instrument={activeInstrument}
              interval={activeInterval}
              currentBar={hoveredBar}
              lastBar={lastBar}
              rsiValue={hoveredRsi}
            />

            {/* QUICK BUY / SELL EXECUTION WIDGET */}
            <QuickExecutionWidget
              symbol={activeInstrument.ticker}
              bidPrice={lastBar ? lastBar.close - 0.15 : 349.00}
              askPrice={lastBar ? lastBar.close + 0.15 : 349.30}
              onTradeExecuted={(side, price, qty) => {
                alert(`[PAPER TRADING ORDER CONFIRMED]\nSide: ${side}\nPrice: $${price.toFixed(2)}\nQty: ${qty}\nStatus: FILLED via AlphaForge Engine`);
              }}
            />

            {/* LIGHTWEIGHT CHARTS MAIN CANVAS CONTAINER */}
            <div ref={mainContainerRef} className="w-full h-full relative" />

            {/* TRANSPARENT HTML5 DRAWING CANVAS OVERLAY */}
            <canvas
              ref={drawingCanvasRef}
              className="absolute inset-0 pointer-events-auto z-10"
              style={{ cursor: activeTool === 'cursor_crosshair' ? 'crosshair' : 'default' }}
            />
          </div>

          {/* RSI SUB-PANE */}
          {showRSI && (
            <div className="h-[140px] border-t border-[#2a2e39] bg-[#131722] relative shrink-0">
              <div className="absolute top-1 left-3 z-10 text-[10px] font-bold uppercase tracking-wider text-[#787b86] flex items-center gap-2">
                <span>RSI (14)</span>
                <span className="text-[#b39ddb]">{hoveredRsi ? hoveredRsi.toFixed(2) : '54.21'}</span>
              </div>
              <div ref={rsiContainerRef} className="w-full h-full" />
            </div>
          )}
        </div>

        {/* Right Collapsible Intelligence Dock (Watchlist, Alerts, News, Data Window, Hotlists, Calendar) */}
        <RightDock
          activeSymbol={activeInstrument.symbol}
          instruments={INSTRUMENTS}
          watchlistItems={WATCHLIST_ITEMS}
          activeInstrument={activeInstrument}
          onSelectSymbol={(sym) => {
            const found = INSTRUMENTS.find(i => i.symbol === sym);
            if (found) setActiveInstrument(found);
          }}
        />
      </div>

      {/* 3. BOTTOM PRESET RANGE & SCALE BAR */}
      <BottomTimeBar
        activeRange={activeRange}
        timezone="11:08:24 UTC"
        scaleMode={scaleMode}
        onSelectRange={handleSelectRange}
        onToggleScaleMode={handleToggleScale}
        onSelectTimezone={() => alert('Timezone selector: UTC, New York (EDT), London (BST)')}
      />
    </div>
  );
}
