import { HeroStats } from "@/components/dashboard/hero-stats";
import { SpotlightCard } from "@/components/shared/spotlight-card";
import { Zap, TrendingUp, AlertCircle, ArrowUpRight, ArrowDownRight } from "lucide-react";
import { ConfidencePill } from "@/components/shared/confidence-pill";
import { mockActiveSignals } from "@/data/mock-signals";

export default function Dashboard() {
  return (
    <div className="p-8 space-y-8 pb-20">
      <header className="space-y-1">
        <h1 className="text-3xl font-black tracking-tight uppercase">Intelligence Dashboard</h1>
        <p className="text-muted-foreground text-sm">Real-time algorithmic signals and portfolio tracking.</p>
      </header>

      <HeroStats />

      <div className="grid grid-cols-12 gap-6">
        {/* Market Overview */}
        <SpotlightCard className="col-span-12 lg:col-span-4 p-6">
          <h3 className="text-sm font-bold uppercase text-text-muted mb-4">Market Overview</h3>
          <div className="space-y-4">
            {[
              { asset: "BTCUSDT", price: 68420.50, change: 2.4, status: "up" },
              { asset: "ETHUSDT", price: 3450.25, change: -1.2, status: "down" },
              { asset: "SOLUSDT", price: 142.30, change: 5.8, status: "up" },
            ].map((market) => (
              <div key={market.asset} className="flex items-center justify-between p-3 rounded-lg bg-elevated/50 border border-border-subtle">
                <div className="font-bold text-sm">{market.asset}</div>
                <div className="text-right">
                  <div className="text-sm font-mono">${market.price.toLocaleString()}</div>
                  <div className={cn("text-[10px] font-bold flex items-center justify-end gap-0.5", market.status === "up" ? "text-green" : "text-red")}>
                    {market.status === "up" ? <ArrowUpRight size={10} /> : <ArrowDownRight size={10} />}
                    {market.change}%
                  </div>
                </div>
              </div>
            ))}
          </div>
          <button className="w-full mt-4 text-[10px] font-black uppercase text-primary hover:underline">View Intelligence →</button>
        </SpotlightCard>

        {/* Active Signals */}
        <SpotlightCard className="col-span-12 lg:col-span-4 p-6" variant="accent">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-bold uppercase text-text-muted">Active Signals</h3>
            <div className="px-2 py-0.5 rounded bg-primary/20 text-primary text-[10px] font-bold">LIVE</div>
          </div>
          <div className="space-y-3">
            {mockActiveSignals.slice(0, 3).map((signal) => (
              <div key={signal.id} className="p-3 rounded-lg border border-border-subtle bg-surface hover:border-primary/50 transition-colors group cursor-pointer">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span className={cn("text-[10px] font-black px-1.5 py-0.5 rounded", signal.direction === "LONG" ? "bg-green/10 text-green" : "bg-red/10 text-red")}>
                      {signal.direction}
                    </span>
                    <span className="text-sm font-bold">{signal.asset}</span>
                  </div>
                  <ConfidencePill score={signal.confidence} />
                </div>
                <div className="text-[10px] text-text-muted flex justify-between">
                  <span>Strategy: {signal.strategy}</span>
                  <span>2h ago</span>
                </div>
              </div>
            ))}
          </div>
          <button className="w-full mt-4 text-[10px] font-black uppercase text-primary hover:underline">View Feed →</button>
        </SpotlightCard>

        {/* Sentiment */}
        <SpotlightCard className="col-span-12 lg:col-span-4 p-6 flex flex-col items-center justify-center text-center">
          <h3 className="text-sm font-bold uppercase text-text-muted mb-6">Market Sentiment</h3>
          <div className="relative w-32 h-32 flex items-center justify-center">
             <svg className="w-full h-full rotate-[-90deg]">
                <circle cx="64" cy="64" r="58" stroke="currentColor" strokeWidth="12" fill="transparent" className="text-border-subtle" />
                <circle cx="64" cy="64" r="58" stroke="currentColor" strokeWidth="12" fill="transparent" className="text-primary" strokeDasharray="364.4" strokeDashoffset="138.5" strokeLinecap="round" />
             </svg>
             <div className="absolute inset-0 flex flex-col items-center justify-center">
                <span className="text-3xl font-black">62</span>
                <span className="text-[10px] font-bold uppercase text-primary">Greed</span>
             </div>
          </div>
          <p className="mt-4 text-xs text-text-muted max-w-[200px]">Market participants are displaying moderate greed. Volatility expected to increase.</p>
        </SpotlightCard>

        {/* Performance Graph Placeholder */}
        <SpotlightCard className="col-span-12 lg:col-span-8 p-6 flex flex-col">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-sm font-bold uppercase text-text-muted">Portfolio Equity Curve</h3>
            <div className="flex gap-2">
              <span className="px-2 py-1 rounded bg-elevated text-[10px] font-bold">30D</span>
              <span className="px-2 py-1 rounded text-[10px] font-bold text-text-muted hover:bg-elevated cursor-pointer">90D</span>
            </div>
          </div>
          <div className="flex-1 flex items-end gap-1 min-h-[160px]">
            {/* Simple CSS bar chart representation */}
            {[40, 45, 38, 52, 60, 58, 65, 72, 68, 75, 82, 80, 85, 95, 90, 100].map((h, i) => (
              <div 
                key={i} 
                className="flex-1 bg-primary/20 hover:bg-primary transition-colors rounded-t-sm" 
                style={{ height: `${h}%` }}
              />
            ))}
          </div>
        </SpotlightCard>

        {/* System Health */}
        <SpotlightCard className="col-span-12 lg:col-span-4 p-6">
          <h3 className="text-sm font-bold uppercase text-text-muted mb-4">Quick Alerts</h3>
          <div className="space-y-4">
            <div className="flex gap-3">
              <div className="w-8 h-8 rounded bg-red/10 flex items-center justify-center text-red shrink-0">
                <AlertCircle size={16} />
              </div>
              <div>
                <div className="text-xs font-bold">Drawdown Alert</div>
                <div className="text-[10px] text-text-muted">Strategy "Momentum Breakout" reached 4% DD.</div>
              </div>
            </div>
            <div className="flex gap-3">
              <div className="w-8 h-8 rounded bg-primary/10 flex items-center justify-center text-primary shrink-0">
                <Zap size={16} />
              </div>
              <div>
                <div className="text-xs font-bold">Model Retrained</div>
                <div className="text-[10px] text-text-muted">ETH/USDT prediction model updated successfully.</div>
              </div>
            </div>
            <div className="flex gap-3">
              <div className="w-8 h-8 rounded bg-green/10 flex items-center justify-center text-green shrink-0">
                <TrendingUp size={16} />
              </div>
              <div>
                <div className="text-xs font-bold">New ATH</div>
                <div className="text-[10px] text-text-muted">Portfolio equity reached new high: $127.4k.</div>
              </div>
            </div>
          </div>
        </SpotlightCard>
      </div>
    </div>
  );
}

function cn(...inputs: any[]) {
  return inputs.filter(Boolean).join(" ");
}
