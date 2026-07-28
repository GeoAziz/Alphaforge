'use client';

import React, { useState, useEffect } from 'react';
import {
  BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis,
  PolarRadiusAxis, Radar, Legend, Cell
} from 'recharts';
import { ChevronDown, Brain, TrendingUp, AlertCircle, Check, X } from 'lucide-react';
import { api } from '@/lib/api';
import { cn } from '@/lib/utils';

interface SignalDriver {
  name: string;
  weight: number;
  value: number;
  impact: 'positive' | 'negative';
}

interface TechnicalIndicator {
  name: string;
  value: number;
  threshold: number;
  status: 'bullish' | 'bearish' | 'neutral';
}

interface SignalExplainability {
  signal_id: string;
  symbol: string;
  confidence: number;
  feature_importance: SignalDriver[];
  technical_indicators: TechnicalIndicator[];
  sentiment_components: {
    twitter_score: number;
    news_score: number;
    onchain_score: number;
  };
  reasoning_chain: string[];
  ml_model_version: string;
  backtest_performance: {
    win_rate: number;
    avg_return: number;
    sharpe_ratio: number;
  };
}

interface SignalExplainabilityPanelProps {
  signalId: string;
  className?: string;
}

export function SignalExplainabilityPanel({ signalId, className = '' }: SignalExplainabilityPanelProps) {
  const [data, setData] = useState<SignalExplainability | null>(null);
  const [loading, setLoading] = useState(true);
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({
    features: true,
    technicals: true,
    sentiment: true,
    reasoning: false,
  });

  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        const response = await api.signals.getExplainability(signalId);
        setData(response);
      } catch (error) {
        console.error('Failed to load signal explainability:', error);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [signalId]);

  if (loading) {
    return (
      <div className={cn('space-y-4 animate-pulse', className)}>
        <div className="h-12 bg-neutral-800 rounded-lg" />
        <div className="h-64 bg-neutral-800 rounded-lg" />
      </div>
    );
  }

  if (!data) {
    return (
      <div className={cn('text-center py-8 text-neutral-400', className)}>
        <Brain size={32} className="mx-auto mb-2 opacity-50" />
        <p>Unable to load signal explanation</p>
      </div>
    );
  }

  const toggleSection = (section: string) => {
    setExpandedSections((prev) => ({
      ...prev,
      [section]: !prev[section],
    }));
  };

  // Prepare feature importance data for chart
  const featureData = data.feature_importance.map((f) => ({
    name: f.name,
    value: Math.abs(f.weight * 100),
    fill: f.impact === 'positive' ? '#10b981' : '#ef4444',
  }));

  // Prepare sentiment data
  const sentimentData = [
    { subject: 'Twitter', value: Math.round(data.sentiment_components.twitter_score * 100) },
    { subject: 'News', value: Math.round(data.sentiment_components.news_score * 100) },
    { subject: 'On-chain', value: Math.round(data.sentiment_components.onchain_score * 100) },
  ];

  return (
    <div className={cn('space-y-4', className)}>
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600/10 to-purple-600/10 border border-blue-600/20 rounded-lg p-4">
        <div className="flex items-center justify-between mb-2">
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <Brain size={20} className="text-blue-400" />
            Why was this signal generated?
          </h2>
          <span className={cn(
            'text-sm font-bold px-3 py-1 rounded',
            data.confidence >= 0.8 ? 'bg-green-500/20 text-green-400' :
            data.confidence >= 0.6 ? 'bg-yellow-500/20 text-yellow-400' :
            'bg-orange-500/20 text-orange-400'
          )}>
            {(data.confidence * 100).toFixed(0)}% Confidence
          </span>
        </div>
        <p className="text-sm text-neutral-400">
          AI analysis of {data.symbol} signal from {data.ml_model_version}
        </p>
      </div>

      {/* Feature Importance Section */}
      <div className="bg-neutral-900 border border-neutral-800 rounded-lg overflow-hidden">
        <button
          onClick={() => toggleSection('features')}
          className="w-full flex items-center justify-between p-4 hover:bg-neutral-800/50 transition-colors"
        >
          <h3 className="font-bold text-white flex items-center gap-2">
            <TrendingUp size={16} className="text-blue-400" />
            Feature Importance Analysis
          </h3>
          <ChevronDown
            size={20}
            className={cn('text-neutral-400 transition-transform', expandedSections.features && 'rotate-180')}
          />
        </button>

        {expandedSections.features && (
          <div className="p-4 border-t border-neutral-800 space-y-4">
            <ResponsiveContainer width="100%" height={250}>
              <BarChart
                data={featureData}
                layout="vertical"
                margin={{ top: 5, right: 30, left: 150, bottom: 5 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                <XAxis type="number" stroke="#666" style={{ fontSize: '12px' }} />
                <YAxis
                  dataKey="name"
                  type="category"
                  stroke="#666"
                  style={{ fontSize: '11px' }}
                  width={140}
                />
                <Tooltip contentStyle={{ background: '#1a1a1a', border: '1px solid #333' }} />
                <Bar dataKey="value" fill="#3b82f6" radius={[0, 8, 8, 0]} />
              </BarChart>
            </ResponsiveContainer>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {data.feature_importance.map((feature) => (
                <div key={feature.name} className="bg-neutral-800/50 rounded-lg p-3">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm font-semibold text-white">{feature.name}</span>
                    <span className={cn(
                      'text-xs font-bold px-2 py-1 rounded',
                      feature.impact === 'positive'
                        ? 'bg-green-500/20 text-green-400'
                        : 'bg-red-500/20 text-red-400'
                    )}>
                      {feature.impact === 'positive' ? '+' : '−'}{(Math.abs(feature.weight) * 100).toFixed(1)}%
                    </span>
                  </div>
                  <p className="text-xs text-neutral-400">
                    Current value: {feature.value.toFixed(2)}
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Technical Indicators Section */}
      <div className="bg-neutral-900 border border-neutral-800 rounded-lg overflow-hidden">
        <button
          onClick={() => toggleSection('technicals')}
          className="w-full flex items-center justify-between p-4 hover:bg-neutral-800/50 transition-colors"
        >
          <h3 className="font-bold text-white flex items-center gap-2">
            <AlertCircle size={16} className="text-purple-400" />
            Technical Indicators
          </h3>
          <ChevronDown
            size={20}
            className={cn('text-neutral-400 transition-transform', expandedSections.technicals && 'rotate-180')}
          />
        </button>

        {expandedSections.technicals && (
          <div className="p-4 border-t border-neutral-800 space-y-3">
            {data.technical_indicators.map((indicator) => (
              <div key={indicator.name} className="bg-neutral-800/50 rounded-lg p-3">
                <div className="flex items-center justify-between mb-2">
                  <span className="font-semibold text-white text-sm">{indicator.name}</span>
                  <span className={cn(
                    'text-xs font-bold px-2 py-1 rounded flex items-center gap-1',
                    indicator.status === 'bullish' ? 'bg-green-500/20 text-green-400' :
                    indicator.status === 'bearish' ? 'bg-red-500/20 text-red-400' :
                    'bg-neutral-600/50 text-neutral-300'
                  )}>
                    {indicator.status === 'bullish' ? <Check size={12} /> :
                     indicator.status === 'bearish' ? <X size={12} /> : null}
                    {indicator.status.charAt(0).toUpperCase() + indicator.status.slice(1)}
                  </span>
                </div>
                <div className="flex items-center gap-2 text-xs text-neutral-400">
                  <span>Value: {indicator.value.toFixed(2)}</span>
                  <span>|</span>
                  <span>Threshold: {indicator.threshold.toFixed(2)}</span>
                </div>
                <div className="mt-2 h-1 bg-neutral-700 rounded-full overflow-hidden">
                  <div
                    className={cn(
                      'h-full transition-all',
                      indicator.status === 'bullish' ? 'bg-green-500' :
                      indicator.status === 'bearish' ? 'bg-red-500' :
                      'bg-neutral-500'
                    )}
                    style={{
                      width: `${Math.min((indicator.value / indicator.threshold) * 100, 100)}%`,
                    }}
                  />
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Sentiment Analysis Section */}
      <div className="bg-neutral-900 border border-neutral-800 rounded-lg overflow-hidden">
        <button
          onClick={() => toggleSection('sentiment')}
          className="w-full flex items-center justify-between p-4 hover:bg-neutral-800/50 transition-colors"
        >
          <h3 className="font-bold text-white">Sentiment Components</h3>
          <ChevronDown
            size={20}
            className={cn('text-neutral-400 transition-transform', expandedSections.sentiment && 'rotate-180')}
          />
        </button>

        {expandedSections.sentiment && (
          <div className="p-4 border-t border-neutral-800">
            <ResponsiveContainer width="100%" height={200}>
              <RadarChart data={sentimentData}>
                <PolarGrid stroke="#333" />
                <PolarAngleAxis dataKey="subject" stroke="#666" style={{ fontSize: '12px' }} />
                <PolarRadiusAxis angle={90} domain={[0, 100]} stroke="#666" style={{ fontSize: '12px' }} />
                <Radar
                  name="Sentiment Score"
                  dataKey="value"
                  stroke="#3b82f6"
                  fill="#3b82f6"
                  fillOpacity={0.5}
                />
                <Legend />
                <Tooltip contentStyle={{ background: '#1a1a1a', border: '1px solid #333' }} />
              </RadarChart>
            </ResponsiveContainer>

            <div className="grid grid-cols-3 gap-3 mt-4">
              <div className="text-center">
                <p className="text-2xl font-bold text-blue-400">
                  {Math.round(data.sentiment_components.twitter_score * 100)}%
                </p>
                <p className="text-xs text-neutral-400">Twitter</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-purple-400">
                  {Math.round(data.sentiment_components.news_score * 100)}%
                </p>
                <p className="text-xs text-neutral-400">News</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-green-400">
                  {Math.round(data.sentiment_components.onchain_score * 100)}%
                </p>
                <p className="text-xs text-neutral-400">On-chain</p>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* AI Reasoning Chain */}
      <div className="bg-neutral-900 border border-neutral-800 rounded-lg overflow-hidden">
        <button
          onClick={() => toggleSection('reasoning')}
          className="w-full flex items-center justify-between p-4 hover:bg-neutral-800/50 transition-colors"
        >
          <h3 className="font-bold text-white">AI Reasoning Chain</h3>
          <ChevronDown
            size={20}
            className={cn('text-neutral-400 transition-transform', expandedSections.reasoning && 'rotate-180')}
          />
        </button>

        {expandedSections.reasoning && (
          <div className="p-4 border-t border-neutral-800 space-y-2">
            {data.reasoning_chain.map((reason, index) => (
              <div key={index} className="flex gap-3">
                <span className="text-xs font-bold text-blue-400 shrink-0">{index + 1}.</span>
                <p className="text-sm text-neutral-400">{reason}</p>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Backtest Performance */}
      {data.backtest_performance && (
        <div className="bg-green-500/5 border border-green-500/20 rounded-lg p-4">
          <h3 className="font-bold text-white mb-3 flex items-center gap-2">
            <Check size={16} className="text-green-400" />
            Historical Signal Performance
          </h3>
          <div className="grid grid-cols-3 gap-3">
            <div>
              <p className="text-xs text-neutral-400 mb-1">Win Rate</p>
              <p className="text-xl font-bold text-green-400">
                {(data.backtest_performance.win_rate * 100).toFixed(1)}%
              </p>
            </div>
            <div>
              <p className="text-xs text-neutral-400 mb-1">Avg Return</p>
              <p className="text-xl font-bold text-blue-400">
                {(data.backtest_performance.avg_return * 100).toFixed(2)}%
              </p>
            </div>
            <div>
              <p className="text-xs text-neutral-400 mb-1">Sharpe Ratio</p>
              <p className="text-xl font-bold text-purple-400">
                {data.backtest_performance.sharpe_ratio.toFixed(2)}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
