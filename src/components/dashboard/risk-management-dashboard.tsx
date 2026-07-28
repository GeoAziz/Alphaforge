'use client';

import React, { useState, useEffect } from 'react';
import {
  LineChart, Line, AreaChart, Area, BarChart, Bar, XAxis, YAxis,
  CartesianGrid, Tooltip, ResponsiveContainer, Legend, Cell
} from 'recharts';
import { AlertTriangle, TrendingDown, Shield, Zap, Activity, Target } from 'lucide-react';
import { api } from '@/lib/api';
import { cn } from '@/lib/utils';

interface RiskMetrics {
  portfolio_value: number;
  max_drawdown: number;
  current_drawdown: number;
  var_95: number;
  sharpe_ratio: number;
  daily_loss_limit: number;
  daily_loss_used: number;
  position_risk: {
    symbol: string;
    exposure: number;
    max_allocation: number;
    risk_per_trade: number;
  }[];
  drawdown_history: { date: string; value: number }[];
}

interface RiskManagementDashboardProps {
  userId: string;
  className?: string;
}

export function RiskManagementDashboard({ userId, className = '' }: RiskManagementDashboardProps) {
  const [metrics, setMetrics] = useState<RiskMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [alerts, setAlerts] = useState<Array<{ severity: string; message: string }>>([]);

  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        const data = await api.portfolio.getRiskMetrics(userId);
        setMetrics(data);

        // Generate alerts based on thresholds
        const newAlerts = [];
        if (data.max_drawdown < -0.2) {
          newAlerts.push({ severity: 'critical', message: 'Portfolio drawdown exceeds 20% threshold' });
        }
        if (data.current_drawdown < -0.1) {
          newAlerts.push({ severity: 'warning', message: 'Current drawdown at 10%' });
        }
        if (data.daily_loss_used / data.daily_loss_limit > 0.8) {
          newAlerts.push({ severity: 'warning', message: 'Daily loss limit 80% consumed' });
        }
        setAlerts(newAlerts);
      } catch (error) {
        console.error('Failed to load risk metrics:', error);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [userId]);

  if (loading) {
    return (
      <div className={cn('space-y-4 animate-pulse', className)}>
        <div className="h-12 bg-neutral-800 rounded-lg" />
        <div className="grid grid-cols-2 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-24 bg-neutral-800 rounded-lg" />
          ))}
        </div>
      </div>
    );
  }

  if (!metrics) {
    return (
      <div className={cn('text-center py-8 text-neutral-400', className)}>
        <Shield size={32} className="mx-auto mb-2 opacity-50" />
        <p>Unable to load risk metrics</p>
      </div>
    );
  }

  const riskScore = Math.min(
    Math.max(10 - Math.abs(metrics.sharpe_ratio) * 2, 0),
    10
  );
  const drawdownPercentage = Math.abs(metrics.current_drawdown) * 100;
  const dailyLimitUsedPercent = (metrics.daily_loss_used / metrics.daily_loss_limit) * 100;

  return (
    <div className={cn('space-y-6', className)}>
      {/* Risk Alerts */}
      {alerts.length > 0 && (
        <div className="space-y-2">
          {alerts.map((alert, i) => (
            <div
              key={i}
              className={cn(
                'flex items-center gap-3 p-3 rounded-lg border',
                alert.severity === 'critical'
                  ? 'bg-red-500/10 border-red-500/20 text-red-400'
                  : 'bg-yellow-500/10 border-yellow-500/20 text-yellow-400'
              )}
            >
              <AlertTriangle size={16} className="shrink-0" />
              <span className="text-sm font-medium">{alert.message}</span>
            </div>
          ))}
        </div>
      )}

      {/* Risk Score Card */}
      <div className="bg-gradient-to-r from-red-600/10 to-orange-600/10 border border-red-600/20 rounded-lg p-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-bold text-white mb-2">Portfolio Risk Score</h2>
            <p className="text-neutral-400 text-sm">Composite measure of portfolio volatility & drawdown</p>
          </div>
          <div className="text-center">
            <div className="text-5xl font-bold text-orange-400 mb-1">
              {riskScore.toFixed(1)}/10
            </div>
            <p className="text-xs text-neutral-400">
              {riskScore < 3 ? 'Conservative' : riskScore < 6 ? 'Moderate' : 'Aggressive'}
            </p>
          </div>
        </div>
      </div>

      {/* Key Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Sharpe Ratio */}
        <div className="bg-neutral-900 border border-neutral-800 rounded-lg p-4">
          <div className="flex items-center justify-between mb-3">
            <span className="text-neutral-400 text-sm font-medium">Sharpe Ratio</span>
            <Activity size={16} className="text-blue-500" />
          </div>
          <p className="text-2xl font-bold text-white">{metrics.sharpe_ratio.toFixed(2)}</p>
          <p className="text-xs text-neutral-500 mt-1">Risk-adjusted returns</p>
        </div>

        {/* Max Drawdown */}
        <div className="bg-neutral-900 border border-neutral-800 rounded-lg p-4">
          <div className="flex items-center justify-between mb-3">
            <span className="text-neutral-400 text-sm font-medium">Max Drawdown</span>
            <TrendingDown size={16} className="text-red-500" />
          </div>
          <p className="text-2xl font-bold text-red-400">{(Math.abs(metrics.max_drawdown) * 100).toFixed(1)}%</p>
          <p className="text-xs text-neutral-500 mt-1">Peak-to-trough decline</p>
        </div>

        {/* VaR 95% */}
        <div className="bg-neutral-900 border border-neutral-800 rounded-lg p-4">
          <div className="flex items-center justify-between mb-3">
            <span className="text-neutral-400 text-sm font-medium">Value at Risk</span>
            <Shield size={16} className="text-purple-500" />
          </div>
          <p className="text-2xl font-bold text-white">${Math.abs(metrics.var_95).toFixed(0)}</p>
          <p className="text-xs text-neutral-500 mt-1">95% confidence level</p>
        </div>

        {/* Daily Loss Limit */}
        <div className="bg-neutral-900 border border-neutral-800 rounded-lg p-4">
          <div className="flex items-center justify-between mb-3">
            <span className="text-neutral-400 text-sm font-medium">Daily Limit</span>
            <Zap size={16} className="text-yellow-500" />
          </div>
          <p className="text-2xl font-bold text-white">${metrics.daily_loss_limit.toFixed(0)}</p>
          <p className="text-xs text-neutral-500 mt-1">${metrics.daily_loss_used.toFixed(0)} used today</p>
        </div>
      </div>

      {/* Drawdown Visualization */}
      <div className="bg-neutral-900 border border-neutral-800 rounded-lg p-6">
        <h3 className="text-lg font-bold text-white mb-4">Drawdown History</h3>
        <ResponsiveContainer width="100%" height={250}>
          <AreaChart data={metrics.drawdown_history}>
            <defs>
              <linearGradient id="colorDrawdown" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#333" />
            <XAxis dataKey="date" stroke="#666" style={{ fontSize: '12px' }} />
            <YAxis stroke="#666" style={{ fontSize: '12px' }} />
            <Tooltip contentStyle={{ background: '#1a1a1a', border: '1px solid #333' }} />
            <Area
              type="monotone"
              dataKey="value"
              stroke="#ef4444"
              fillOpacity={1}
              fill="url(#colorDrawdown)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Position Risk Breakdown */}
      <div className="bg-neutral-900 border border-neutral-800 rounded-lg p-6">
        <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
          <Target size={16} className="text-purple-400" />
          Position Risk Breakdown
        </h3>

        {metrics.position_risk.length > 0 ? (
          <div className="space-y-3">
            {metrics.position_risk.map((position, index) => (
              <div key={index} className="bg-neutral-800/50 rounded-lg p-4">
                <div className="flex items-center justify-between mb-3">
                  <span className="font-semibold text-white">{position.symbol}</span>
                  <span className="text-sm text-neutral-400">
                    {(position.exposure * 100).toFixed(1)}% of portfolio
                  </span>
                </div>

                {/* Exposure Bar */}
                <div className="mb-2">
                  <div className="flex items-center justify-between text-xs text-neutral-500 mb-1">
                    <span>Exposure</span>
                    <span>{(position.exposure * 100).toFixed(1)}%</span>
                  </div>
                  <div className="h-2 bg-neutral-700 rounded-full overflow-hidden">
                    <div
                      className={cn(
                        'h-full transition-all',
                        position.exposure > position.max_allocation
                          ? 'bg-red-500'
                          : position.exposure > position.max_allocation * 0.8
                          ? 'bg-yellow-500'
                          : 'bg-green-500'
                      )}
                      style={{
                        width: `${Math.min((position.exposure / position.max_allocation) * 100, 100)}%`,
                      }}
                    />
                  </div>
                  <div className="flex items-center justify-between text-xs text-neutral-500 mt-1">
                    <span>Max</span>
                    <span>{(position.max_allocation * 100).toFixed(1)}%</span>
                  </div>
                </div>

                {/* Risk Per Trade */}
                <div className="flex items-center justify-between text-xs">
                  <span className="text-neutral-400">Risk per trade:</span>
                  <span className="font-semibold text-white">
                    ${Math.abs(position.risk_per_trade).toFixed(2)}
                  </span>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-center text-neutral-400 py-8">No active positions</p>
        )}
      </div>

      {/* Daily Loss Usage */}
      <div className="bg-neutral-900 border border-neutral-800 rounded-lg p-6">
        <h3 className="text-lg font-bold text-white mb-4">Daily Loss Limit Usage</h3>
        <div className="space-y-4">
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-neutral-400">Available Budget</span>
              <span className="text-sm font-semibold text-white">
                ${(metrics.daily_loss_limit - metrics.daily_loss_used).toFixed(2)}
              </span>
            </div>
            <div className="h-3 bg-neutral-700 rounded-full overflow-hidden">
              <div
                className={cn(
                  'h-full transition-all',
                  dailyLimitUsedPercent > 80
                    ? 'bg-red-500'
                    : dailyLimitUsedPercent > 50
                    ? 'bg-yellow-500'
                    : 'bg-green-500'
                )}
                style={{ width: `${Math.min(dailyLimitUsedPercent, 100)}%` }}
              />
            </div>
          </div>

          <div className="grid grid-cols-3 gap-2 text-xs">
            <div className="text-center">
              <p className="text-neutral-400 mb-1">Limit</p>
              <p className="font-bold text-white">${metrics.daily_loss_limit.toFixed(0)}</p>
            </div>
            <div className="text-center">
              <p className="text-neutral-400 mb-1">Used</p>
              <p className="font-bold text-orange-400">${metrics.daily_loss_used.toFixed(0)}</p>
            </div>
            <div className="text-center">
              <p className="text-neutral-400 mb-1">Remaining</p>
              <p className={`font-bold ${dailyLimitUsedPercent > 80 ? 'text-red-400' : 'text-green-400'}`}>
                {(100 - dailyLimitUsedPercent).toFixed(0)}%
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Risk Settings CTA */}
      <button className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-4 rounded-lg transition-colors">
        Configure Risk Parameters →
      </button>
    </div>
  );
}
