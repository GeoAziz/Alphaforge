'use client';

import React, { useState, useEffect } from 'react';
import { TrendingUp, TrendingDown, AlertTriangle, CheckCircle, Zap, Clock } from 'lucide-react';
import { api } from '@/lib/api';
import { cn } from '@/lib/utils';

interface HighConfidenceSignal {
  id: string;
  symbol: string;
  signal_type: 'BUY' | 'SELL';
  confidence: number;
  entry_price: number;
  target_price: number;
  stop_loss: number;
  risk_reward_ratio: number;
  created_at: string;
  technical_drivers: string[];
  sentiment_score: number;
  ml_score: number;
  time_horizon: string;
}

interface HighConfidenceSignalsProps {
  limit?: number;
  className?: string;
}

export function HighConfidenceSignals({ limit = 10, className = '' }: HighConfidenceSignalsProps) {
  const [signals, setSignals] = useState<HighConfidenceSignal[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedSignal, setSelectedSignal] = useState<HighConfidenceSignal | null>(null);
  const [sortBy, setSortBy] = useState<'confidence' | 'risk-reward' | 'recent'>('confidence');

  useEffect(() => {
    const loadSignals = async () => {
      try {
        setLoading(true);
        const data = await api.signals.getTopSignals(limit);
        setSignals(Array.isArray(data) ? data : []);
      } catch (error) {
        console.error('Failed to load high-confidence signals:', error);
      } finally {
        setLoading(false);
      }
    };

    loadSignals();
    const interval = setInterval(loadSignals, 30000);
    return () => clearInterval(interval);
  }, [limit]);

  const sortedSignals = [...signals].sort((a, b) => {
    if (sortBy === 'confidence') return b.confidence - a.confidence;
    if (sortBy === 'risk-reward') return (b.risk_reward_ratio || 0) - (a.risk_reward_ratio || 0);
    return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
  });

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.85) return 'text-green-400 bg-green-400/10';
    if (confidence >= 0.70) return 'text-yellow-400 bg-yellow-400/10';
    return 'text-orange-400 bg-orange-400/10';
  };

  const getRRColor = (ratio: number) => {
    if (ratio >= 3) return 'text-green-400';
    if (ratio >= 2) return 'text-yellow-400';
    return 'text-orange-400';
  };

  if (loading) {
    return (
      <div className={cn('space-y-3 animate-pulse', className)}>
        {[1, 2, 3].map((i) => (
          <div key={i} className="h-20 bg-neutral-800 rounded-lg" />
        ))}
      </div>
    );
  }

  return (
    <div className={cn('space-y-4', className)}>
      {/* Header with Controls */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Zap size={20} className="text-yellow-500" />
          <h2 className="text-xl font-bold text-white">Top Trading Signals</h2>
          <span className="text-xs font-bold text-neutral-400 bg-neutral-800 px-2 py-1 rounded">
            {signals.length} Active
          </span>
        </div>
        <select
          value={sortBy}
          onChange={(e) => setSortBy(e.target.value as any)}
          className="text-xs font-medium bg-neutral-800 text-white px-2 py-1 rounded border border-neutral-700 hover:border-neutral-600 transition-colors"
        >
          <option value="confidence">Highest Confidence</option>
          <option value="risk-reward">Best Risk/Reward</option>
          <option value="recent">Most Recent</option>
        </select>
      </div>

      {/* Signals List */}
      {sortedSignals.length > 0 ? (
        <div className="grid grid-cols-1 gap-3">
          {sortedSignals.map((signal) => (
            <div
              key={signal.id}
              onClick={() => setSelectedSignal(signal)}
              className={cn(
                'p-4 rounded-lg border cursor-pointer transition-all hover:border-blue-500/50',
                signal.signal_type === 'BUY'
                  ? 'bg-green-500/5 border-green-500/20 hover:bg-green-500/10'
                  : 'bg-red-500/5 border-red-500/20 hover:bg-red-500/10'
              )}
            >
              {/* Row 1: Symbol, Type, Confidence */}
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-3">
                  <div className="flex items-center gap-2">
                    <span className="text-lg font-bold text-white">{signal.symbol}</span>
                    <span
                      className={cn(
                        'flex items-center gap-1 text-xs font-bold px-2 py-1 rounded',
                        signal.signal_type === 'BUY'
                          ? 'bg-green-500/20 text-green-400'
                          : 'bg-red-500/20 text-red-400'
                      )}
                    >
                      {signal.signal_type === 'BUY' ? (
                        <TrendingUp size={12} />
                      ) : (
                        <TrendingDown size={12} />
                      )}
                      {signal.signal_type}
                    </span>
                  </div>
                </div>
                <div className={cn('text-right', getConfidenceColor(signal.confidence))}>
                  <div className="text-sm font-bold">{(signal.confidence * 100).toFixed(0)}%</div>
                  <div className="text-xs">Confidence</div>
                </div>
              </div>

              {/* Row 2: Prices and Metrics */}
              <div className="grid grid-cols-3 gap-3 mb-3 text-xs">
                <div className="bg-neutral-800/50 rounded p-2">
                  <div className="text-neutral-400 text-[10px] uppercase font-semibold">Entry</div>
                  <div className="text-white font-bold">${signal.entry_price?.toFixed(2) || 'N/A'}</div>
                </div>
                <div className="bg-neutral-800/50 rounded p-2">
                  <div className="text-neutral-400 text-[10px] uppercase font-semibold">Target</div>
                  <div className="text-green-400 font-bold">${signal.target_price?.toFixed(2) || 'N/A'}</div>
                </div>
                <div className="bg-neutral-800/50 rounded p-2">
                  <div className="text-neutral-400 text-[10px] uppercase font-semibold">Stop</div>
                  <div className="text-red-400 font-bold">${signal.stop_loss?.toFixed(2) || 'N/A'}</div>
                </div>
              </div>

              {/* Row 3: Risk/Reward and Drivers */}
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="flex items-center gap-1">
                    <AlertTriangle size={14} className="text-orange-400" />
                    <span className={cn('text-sm font-bold', getRRColor(signal.risk_reward_ratio || 0))}>
                      R:R {(signal.risk_reward_ratio || 0).toFixed(1)}:1
                    </span>
                  </div>
                  <div className="flex items-center gap-1 text-neutral-500">
                    <Clock size={12} />
                    <span className="text-xs">{signal.time_horizon || '4H'}</span>
                  </div>
                </div>
                <div className="flex items-center gap-1">
                  {signal.confidence >= 0.75 && (
                    <CheckCircle size={16} className="text-green-400" />
                  )}
                </div>
              </div>

              {/* Technical Drivers Tags */}
              {signal.technical_drivers && signal.technical_drivers.length > 0 && (
                <div className="mt-3 pt-3 border-t border-neutral-700">
                  <div className="flex flex-wrap gap-2">
                    {signal.technical_drivers.slice(0, 3).map((driver, i) => (
                      <span
                        key={i}
                        className="text-xs bg-neutral-700 text-neutral-300 px-2 py-1 rounded"
                      >
                        {driver}
                      </span>
                    ))}
                    {signal.technical_drivers.length > 3 && (
                      <span className="text-xs text-neutral-500">
                        +{signal.technical_drivers.length - 3} more
                      </span>
                    )}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-12 text-neutral-500">
          <Zap size={32} className="mx-auto mb-2 opacity-50" />
          <p>No high-confidence signals available</p>
        </div>
      )}

      {/* Detail Panel */}
      {selectedSignal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-neutral-900 rounded-lg border border-neutral-800 max-w-md w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6 space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-xl font-bold text-white">{selectedSignal.symbol}</h3>
                <button
                  onClick={() => setSelectedSignal(null)}
                  className="text-neutral-500 hover:text-white transition-colors"
                >
                  ✕
                </button>
              </div>

              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="text-neutral-400 text-xs font-semibold mb-1">ML Score</p>
                  <p className="font-bold text-blue-400">{(selectedSignal.ml_score * 100).toFixed(0)}%</p>
                </div>
                <div>
                  <p className="text-neutral-400 text-xs font-semibold mb-1">Sentiment</p>
                  <p className={`font-bold ${selectedSignal.sentiment_score > 0 ? 'text-green-400' : 'text-red-400'}`}>
                    {selectedSignal.sentiment_score > 0 ? '📈 Bullish' : '📉 Bearish'}
                  </p>
                </div>
              </div>

              <button className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-lg transition-colors">
                View Full Analysis
              </button>
              <button className="w-full bg-green-600 hover:bg-green-700 text-white font-bold py-2 px-4 rounded-lg transition-colors">
                Execute Trade
              </button>
              <button
                onClick={() => setSelectedSignal(null)}
                className="w-full bg-neutral-700 hover:bg-neutral-600 text-white font-bold py-2 px-4 rounded-lg transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
