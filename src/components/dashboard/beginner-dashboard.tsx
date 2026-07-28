'use client';

import React, { useState, useEffect } from 'react';
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { TrendingUp, AlertCircle, Zap, Target, DollarSign, Activity } from 'lucide-react';
import { api } from '@/lib/api';
import { PortfolioSummary } from '@/lib/types';
import { cn } from '@/lib/utils';

interface BeginnerDashboardProps {
  userId: string;
  isLoading?: boolean;
}

export function BeginnerDashboard({ userId, isLoading = false }: BeginnerDashboardProps) {
  const [summary, setSummary] = useState<PortfolioSummary | null>(null);
  const [topSignals, setTopSignals] = useState<any[]>([]);
  const [portfolioMetrics, setPortfolioMetrics] = useState<any>(null);
  const [loading, setLoading] = useState(isLoading);

  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        const [summaryData, signalsData, metricsData] = await Promise.all([
          api.portfolio.getSummary(userId),
          api.signals.getTopSignals(5),
          api.portfolio.getMetrics(userId),
        ]);
        setSummary(summaryData);
        setTopSignals(signalsData || []);
        setPortfolioMetrics(metricsData);
      } catch (error) {
        console.error('Failed to load beginner dashboard data:', error);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [userId]);

  if (loading) {
    return (
      <div className="space-y-6 animate-pulse">
        <div className="h-32 bg-neutral-800 rounded-lg" />
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-24 bg-neutral-800 rounded-lg" />
          ))}
        </div>
      </div>
    );
  }

  const portfolioValue = summary?.portfolio_value || 10000;
  const totalReturn = summary?.total_return || 0;
  const returnPercentage = summary?.return_percentage || 0;
  const winRate = portfolioMetrics?.win_rate || 0;

  return (
    <div className="space-y-6">
      {/* Welcome Header */}
      <div className="bg-gradient-to-r from-blue-600/10 to-purple-600/10 border border-blue-600/20 rounded-xl p-6">
        <h1 className="text-3xl font-bold text-white mb-2">Welcome to AlphaForge</h1>
        <p className="text-neutral-400">Your AI-powered trading intelligence platform</p>
      </div>

      {/* Key Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Portfolio Value */}
        <div className="bg-neutral-900 border border-neutral-800 rounded-lg p-4">
          <div className="flex items-center justify-between mb-3">
            <span className="text-neutral-400 text-sm font-medium">Portfolio Value</span>
            <DollarSign size={16} className="text-blue-500" />
          </div>
          <p className="text-2xl font-bold text-white">${(portfolioValue / 1000).toFixed(1)}K</p>
          <p className="text-xs text-neutral-500 mt-1">Tracked balance</p>
        </div>

        {/* Total Return */}
        <div className="bg-neutral-900 border border-neutral-800 rounded-lg p-4">
          <div className="flex items-center justify-between mb-3">
            <span className="text-neutral-400 text-sm font-medium">Total Return</span>
            <TrendingUp size={16} className={returnPercentage >= 0 ? 'text-green-500' : 'text-red-500'} />
          </div>
          <p className={`text-2xl font-bold ${returnPercentage >= 0 ? 'text-green-500' : 'text-red-500'}`}>
            {returnPercentage >= 0 ? '+' : ''}{returnPercentage.toFixed(2)}%
          </p>
          <p className="text-xs text-neutral-500 mt-1">${totalReturn > 0 ? '+' : ''}${Math.abs(totalReturn).toFixed(0)}</p>
        </div>

        {/* Win Rate */}
        <div className="bg-neutral-900 border border-neutral-800 rounded-lg p-4">
          <div className="flex items-center justify-between mb-3">
            <span className="text-neutral-400 text-sm font-medium">Win Rate</span>
            <Target size={16} className="text-purple-500" />
          </div>
          <p className="text-2xl font-bold text-white">{(winRate * 100).toFixed(1)}%</p>
          <p className="text-xs text-neutral-500 mt-1">Profitable trades</p>
        </div>

        {/* Active Signals */}
        <div className="bg-neutral-900 border border-neutral-800 rounded-lg p-4">
          <div className="flex items-center justify-between mb-3">
            <span className="text-neutral-400 text-sm font-medium">Active Signals</span>
            <Zap size={16} className="text-yellow-500" />
          </div>
          <p className="text-2xl font-bold text-white">{topSignals.length}</p>
          <p className="text-xs text-neutral-500 mt-1">Trading opportunities</p>
        </div>
      </div>

      {/* Top Trading Signals */}
      <div className="bg-neutral-900 border border-neutral-800 rounded-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-bold text-white">🎯 Top Trading Signals</h2>
          <span className="text-xs font-medium text-neutral-400">Highest Confidence</span>
        </div>

        {topSignals.length > 0 ? (
          <div className="space-y-3">
            {topSignals.map((signal, index) => (
              <div key={signal.id || index} className="flex items-center justify-between p-3 bg-neutral-800/50 rounded-lg border border-neutral-700">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-semibold text-white text-sm">{signal.symbol || 'BTC/USD'}</span>
                    <span className={`text-xs font-bold px-2 py-1 rounded ${
                      signal.signal_type === 'BUY' ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'
                    }`}>
                      {signal.signal_type || 'BUY'}
                    </span>
                  </div>
                  <p className="text-xs text-neutral-400">{signal.reason || 'Strong momentum detected'}</p>
                </div>
                <div className="text-right">
                  <p className={`font-bold ${signal.confidence >= 0.7 ? 'text-green-400' : 'text-yellow-400'}`}>
                    {(signal.confidence * 100 || 75).toFixed(0)}%
                  </p>
                  <p className="text-xs text-neutral-500">confidence</p>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8 text-neutral-400">
            <Activity size={32} className="mx-auto mb-2 opacity-50" />
            <p>No active signals at the moment</p>
          </div>
        )}

        <button className="w-full mt-4 bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-4 rounded-lg transition-colors">
          View All Signals →
        </button>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Recent Performance */}
        <div className="bg-neutral-900 border border-neutral-800 rounded-lg p-6">
          <h3 className="text-lg font-bold text-white mb-4">7-Day Performance</h3>
          <ResponsiveContainer width="100%" height={150}>
            <LineChart data={[
              { day: 'Mon', value: 10000 },
              { day: 'Tue', value: 10150 },
              { day: 'Wed', value: 10100 },
              { day: 'Thu', value: 10300 },
              { day: 'Fri', value: 10250 },
              { day: 'Sat', value: 10400 },
              { day: 'Sun', value: 10500 },
            ]}>
              <CartesianGrid strokeDasharray="3 3" stroke="#333" />
              <XAxis dataKey="day" stroke="#666" style={{ fontSize: '12px' }} />
              <YAxis stroke="#666" style={{ fontSize: '12px' }} />
              <Tooltip contentStyle={{ background: '#1a1a1a', border: '1px solid #333' }} />
              <Line type="monotone" dataKey="value" stroke="#3b82f6" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Asset Allocation */}
        <div className="bg-neutral-900 border border-neutral-800 rounded-lg p-6">
          <h3 className="text-lg font-bold text-white mb-4">Asset Allocation</h3>
          <ResponsiveContainer width="100%" height={150}>
            <PieChart>
              <Pie data={[
                { name: 'BTC', value: 40 },
                { name: 'ETH', value: 30 },
                { name: 'Alts', value: 20 },
                { name: 'Stablecoins', value: 10 },
              ]} cx="50%" cy="50%" innerRadius={40} outerRadius={60} dataKey="value">
                <Cell fill="#3b82f6" />
                <Cell fill="#8b5cf6" />
                <Cell fill="#ec4899" />
                <Cell fill="#14b8a6" />
              </Pie>
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Call-to-Action */}
      <div className="bg-gradient-to-r from-green-600/10 to-blue-600/10 border border-green-600/20 rounded-lg p-6 text-center">
        <h3 className="text-lg font-bold text-white mb-2">Ready to Start Trading?</h3>
        <p className="text-neutral-400 mb-4">Test strategies risk-free with our Paper Trading simulator</p>
        <button className="bg-green-600 hover:bg-green-700 text-white font-semibold py-2 px-6 rounded-lg transition-colors">
          Launch Paper Trading
        </button>
      </div>
    </div>
  );
}
