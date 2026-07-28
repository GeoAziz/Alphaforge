'use client';

import React, { useState, useEffect } from 'react';
import {
  LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Legend, Cell, ComposedChart, Area, AreaChart
} from 'recharts';
import { TrendingUp, Percent, Award, Calendar, Activity, ArrowUpRight } from 'lucide-react';
import { api } from '@/lib/api';
import { cn } from '@/lib/utils';

interface PerformanceMetrics {
  total_return: number;
  annual_return: number;
  monthly_return: number;
  sharpe_ratio: number;
  sortino_ratio: number;
  max_drawdown: number;
  win_rate: number;
  profit_factor: number;
  trades_count: number;
  equity_curve: { date: string; value: number }[];
  monthly_returns: { month: string; return: number }[];
  daily_returns: { date: string; return: number; cumulativeReturn: number }[];
  performance_by_asset: { asset: string; return: number; trades: number }[];
  drawdown_distribution: { bucket: string; count: number }[];
}

interface PerformanceAnalyticsProps {
  userId: string;
  timeframe?: 'all' | '1y' | '6m' | '3m' | '1m';
  className?: string;
}

export function PerformanceAnalytics({
  userId,
  timeframe = 'all',
  className = '',
}: PerformanceAnalyticsProps) {
  const [metrics, setMetrics] = useState<PerformanceMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedTimeframe, setSelectedTimeframe] = useState(timeframe);
  const [activeTab, setActiveTab] = useState<'equity' | 'returns' | 'assets' | 'distribution'>('equity');

  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        const data = await api.portfolio.getPerformanceAnalytics(userId, selectedTimeframe);
        setMetrics(data);
      } catch (error) {
        console.error('Failed to load performance analytics:', error);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [userId, selectedTimeframe]);

  if (loading) {
    return (
      <div className={cn('space-y-4 animate-pulse', className)}>
        <div className="h-64 bg-neutral-800 rounded-lg" />
        <div className="h-96 bg-neutral-800 rounded-lg" />
      </div>
    );
  }

  if (!metrics) {
    return (
      <div className={cn('text-center py-8 text-neutral-400', className)}>
        <Activity size={32} className="mx-auto mb-2 opacity-50" />
        <p>Unable to load performance analytics</p>
      </div>
    );
  }

  const timeframeOptions = [
    { label: 'All Time', value: 'all' },
    { label: '1 Year', value: '1y' },
    { label: '6 Months', value: '6m' },
    { label: '3 Months', value: '3m' },
    { label: '1 Month', value: '1m' },
  ];

  return (
    <div className={cn('space-y-6', className)}>
      {/* Header with Timeframe Selector */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <h2 className="text-2xl font-bold text-white flex items-center gap-2">
          <TrendingUp size={24} className="text-blue-400" />
          Performance Analytics
        </h2>
        <div className="flex gap-2 flex-wrap">
          {timeframeOptions.map((option) => (
            <button
              key={option.value}
              onClick={() => setSelectedTimeframe(option.value as any)}
              className={cn(
                'px-3 py-1 rounded-lg text-sm font-medium transition-colors',
                selectedTimeframe === option.value
                  ? 'bg-blue-600 text-white'
                  : 'bg-neutral-800 text-neutral-400 hover:bg-neutral-700'
              )}
            >
              {option.label}
            </button>
          ))}
        </div>
      </div>

      {/* Key Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Return */}
        <div className="bg-neutral-900 border border-neutral-800 rounded-lg p-4">
          <div className="flex items-center justify-between mb-3">
            <span className="text-neutral-400 text-sm font-medium">Total Return</span>
            <ArrowUpRight size={16} className="text-green-500" />
          </div>
          <p className={`text-2xl font-bold ${metrics.total_return >= 0 ? 'text-green-400' : 'text-red-400'}`}>
            {metrics.total_return >= 0 ? '+' : ''}{(metrics.total_return * 100).toFixed(2)}%
          </p>
          <p className="text-xs text-neutral-500 mt-1">All time performance</p>
        </div>

        {/* Annual Return */}
        <div className="bg-neutral-900 border border-neutral-800 rounded-lg p-4">
          <div className="flex items-center justify-between mb-3">
            <span className="text-neutral-400 text-sm font-medium">Annual Return</span>
            <Calendar size={16} className="text-blue-500" />
          </div>
          <p className={`text-2xl font-bold ${metrics.annual_return >= 0 ? 'text-green-400' : 'text-red-400'}`}>
            {metrics.annual_return >= 0 ? '+' : ''}{(metrics.annual_return * 100).toFixed(2)}%
          </p>
          <p className="text-xs text-neutral-500 mt-1">Annualized return</p>
        </div>

        {/* Sharpe Ratio */}
        <div className="bg-neutral-900 border border-neutral-800 rounded-lg p-4">
          <div className="flex items-center justify-between mb-3">
            <span className="text-neutral-400 text-sm font-medium">Sharpe Ratio</span>
            <Award size={16} className="text-purple-500" />
          </div>
          <p className="text-2xl font-bold text-white">{metrics.sharpe_ratio.toFixed(2)}</p>
          <p className="text-xs text-neutral-500 mt-1">Risk-adjusted returns</p>
        </div>

        {/* Win Rate */}
        <div className="bg-neutral-900 border border-neutral-800 rounded-lg p-4">
          <div className="flex items-center justify-between mb-3">
            <span className="text-neutral-400 text-sm font-medium">Win Rate</span>
            <Percent size={16} className="text-yellow-500" />
          </div>
          <p className="text-2xl font-bold text-white">{(metrics.win_rate * 100).toFixed(1)}%</p>
          <p className="text-xs text-neutral-500 mt-1">{metrics.trades_count} total trades</p>
        </div>
      </div>

      {/* Chart Tabs */}
      <div className="bg-neutral-900 border border-neutral-800 rounded-lg">
        {/* Tab Navigation */}
        <div className="flex border-b border-neutral-800">
          {(['equity', 'returns', 'assets', 'distribution'] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={cn(
                'flex-1 py-3 text-sm font-medium transition-colors border-b-2 -mb-1',
                activeTab === tab
                  ? 'text-blue-400 border-blue-500'
                  : 'text-neutral-400 border-transparent hover:text-neutral-300'
              )}
            >
              {tab === 'equity' && 'Equity Curve'}
              {tab === 'returns' && 'Returns'}
              {tab === 'assets' && 'By Asset'}
              {tab === 'distribution' && 'Drawdown'}
            </button>
          ))}
        </div>

        {/* Tab Content */}
        <div className="p-6">
          {/* Equity Curve */}
          {activeTab === 'equity' && (
            <div>
              <p className="text-sm text-neutral-400 mb-4">Cumulative portfolio equity over time</p>
              <ResponsiveContainer width="100%" height={350}>
                <AreaChart data={metrics.equity_curve}>
                  <defs>
                    <linearGradient id="colorEquity" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                  <XAxis dataKey="date" stroke="#666" style={{ fontSize: '12px' }} />
                  <YAxis stroke="#666" style={{ fontSize: '12px' }} />
                  <Tooltip contentStyle={{ background: '#1a1a1a', border: '1px solid #333' }} />
                  <Area
                    type="monotone"
                    dataKey="value"
                    stroke="#3b82f6"
                    fillOpacity={1}
                    fill="url(#colorEquity)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Monthly Returns */}
          {activeTab === 'returns' && (
            <div>
              <p className="text-sm text-neutral-400 mb-4">Monthly return distribution</p>
              <ResponsiveContainer width="100%" height={350}>
                <BarChart data={metrics.monthly_returns}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                  <XAxis dataKey="month" stroke="#666" style={{ fontSize: '12px' }} />
                  <YAxis stroke="#666" style={{ fontSize: '12px' }} />
                  <Tooltip contentStyle={{ background: '#1a1a1a', border: '1px solid #333' }} />
                  <Bar dataKey="return" fill="#3b82f6" radius={[8, 8, 0, 0]}>
                    {metrics.monthly_returns.map((entry, index) => (
                      <Cell
                        key={`cell-${index}`}
                        fill={entry.return >= 0 ? '#10b981' : '#ef4444'}
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Performance by Asset */}
          {activeTab === 'assets' && (
            <div>
              <p className="text-sm text-neutral-400 mb-4">Return by asset class</p>
              <ResponsiveContainer width="100%" height={350}>
                <ComposedChart data={metrics.performance_by_asset}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                  <XAxis dataKey="asset" stroke="#666" style={{ fontSize: '12px' }} />
                  <YAxis yAxisId="left" stroke="#666" style={{ fontSize: '12px' }} />
                  <YAxis yAxisId="right" orientation="right" stroke="#666" style={{ fontSize: '12px' }} />
                  <Tooltip contentStyle={{ background: '#1a1a1a', border: '1px solid #333' }} />
                  <Legend />
                  <Bar yAxisId="left" dataKey="return" fill="#3b82f6" radius={[8, 8, 0, 0]} />
                  <Line yAxisId="right" type="monotone" dataKey="trades" stroke="#8b5cf6" strokeWidth={2} />
                </ComposedChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Drawdown Distribution */}
          {activeTab === 'distribution' && (
            <div>
              <p className="text-sm text-neutral-400 mb-4">Frequency of drawdown levels</p>
              <ResponsiveContainer width="100%" height={350}>
                <BarChart data={metrics.drawdown_distribution}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                  <XAxis dataKey="bucket" stroke="#666" style={{ fontSize: '12px' }} />
                  <YAxis stroke="#666" style={{ fontSize: '12px' }} />
                  <Tooltip contentStyle={{ background: '#1a1a1a', border: '1px solid #333' }} />
                  <Bar dataKey="count" fill="#ef4444" radius={[8, 8, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>
      </div>

      {/* Additional Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Sortino Ratio */}
        <div className="bg-neutral-900 border border-neutral-800 rounded-lg p-4">
          <h3 className="text-sm font-semibold text-neutral-400 mb-3">Sortino Ratio</h3>
          <p className="text-2xl font-bold text-white mb-1">{metrics.sortino_ratio.toFixed(2)}</p>
          <p className="text-xs text-neutral-500">Downside risk adjusted returns</p>
        </div>

        {/* Profit Factor */}
        <div className="bg-neutral-900 border border-neutral-800 rounded-lg p-4">
          <h3 className="text-sm font-semibold text-neutral-400 mb-3">Profit Factor</h3>
          <p className={`text-2xl font-bold mb-1 ${metrics.profit_factor > 1 ? 'text-green-400' : 'text-red-400'}`}>
            {metrics.profit_factor.toFixed(2)}
          </p>
          <p className="text-xs text-neutral-500">Gross profit / gross loss</p>
        </div>

        {/* Monthly Return */}
        <div className="bg-neutral-900 border border-neutral-800 rounded-lg p-4">
          <h3 className="text-sm font-semibold text-neutral-400 mb-3">This Month</h3>
          <p className={`text-2xl font-bold mb-1 ${metrics.monthly_return >= 0 ? 'text-green-400' : 'text-red-400'}`}>
            {metrics.monthly_return >= 0 ? '+' : ''}{(metrics.monthly_return * 100).toFixed(2)}%
          </p>
          <p className="text-xs text-neutral-500">Month-to-date return</p>
        </div>
      </div>

      {/* Detailed Metrics Table */}
      <div className="bg-neutral-900 border border-neutral-800 rounded-lg p-6">
        <h3 className="text-lg font-bold text-white mb-4">Detailed Metrics</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[
            { label: 'Total Trades', value: metrics.trades_count },
            { label: 'Winning Trades', value: Math.round(metrics.trades_count * metrics.win_rate) },
            { label: 'Losing Trades', value: Math.round(metrics.trades_count * (1 - metrics.win_rate)) },
            { label: 'Max Drawdown', value: `${(metrics.max_drawdown * 100).toFixed(2)}%` },
            { label: 'Best Month', value: `${Math.max(...metrics.monthly_returns.map((m) => m.return * 100)).toFixed(2)}%` },
            { label: 'Worst Month', value: `${Math.min(...metrics.monthly_returns.map((m) => m.return * 100)).toFixed(2)}%` },
          ].map((metric, i) => (
            <div key={i} className="bg-neutral-800/50 rounded-lg p-3">
              <p className="text-neutral-400 text-xs font-semibold mb-1">{metric.label}</p>
              <p className="text-lg font-bold text-white">{metric.value}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
