'use client';

import React, { useState } from 'react';
import { ArrowUpRight, ArrowDownLeft, X, AlertCircle, CheckCircle } from 'lucide-react';
import { cn } from '@/lib/utils';

interface OrderForm {
  pair: string;
  side: 'BUY' | 'SELL';
  type: 'MARKET' | 'LIMIT' | 'STOP';
  quantity: number;
  price?: number;
  stopPrice?: number;
  takeProfit?: number;
  stopLoss?: number;
}

interface ExecutedTrade {
  id: string;
  pair: string;
  side: 'BUY' | 'SELL';
  quantity: number;
  entryPrice: number;
  currentPrice: number;
  pnl: number;
  pnlPercent: number;
  timestamp: string;
  status: 'OPEN' | 'CLOSED';
}

interface LiveTradingPanelProps {
  onExecuteTrade?: (order: OrderForm) => Promise<void>;
  onClosePosition?: (tradeId: string) => Promise<void>;
  activeTrades?: ExecutedTrade[];
  availableBalance?: number;
  className?: string;
}

export function LiveTradingPanel({
  onExecuteTrade,
  onClosePosition,
  activeTrades = [],
  availableBalance = 10000,
  className = '',
}: LiveTradingPanelProps) {
  const [tab, setTab] = useState<'order' | 'positions'>('order');
  const [orderForm, setOrderForm] = useState<OrderForm>({
    pair: 'BTC/USD',
    side: 'BUY',
    type: 'MARKET',
    quantity: 0.1,
  });
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const handleExecute = async () => {
    if (!orderForm.quantity || orderForm.quantity <= 0) {
      setMessage({ type: 'error', text: 'Quantity must be greater than 0' });
      return;
    }

    if (orderForm.type === 'LIMIT' && !orderForm.price) {
      setMessage({ type: 'error', text: 'Limit price required' });
      return;
    }

    try {
      setLoading(true);
      if (onExecuteTrade) {
        await onExecuteTrade(orderForm);
      }
      setMessage({ type: 'success', text: 'Order executed successfully!' });
      setOrderForm({ ...orderForm, quantity: 0 });
      setTimeout(() => setMessage(null), 3000);
    } catch (error) {
      setMessage({
        type: 'error',
        text: error instanceof Error ? error.message : 'Execution failed',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleClosePosition = async (tradeId: string) => {
    try {
      if (onClosePosition) {
        await onClosePosition(tradeId);
      }
      setMessage({ type: 'success', text: 'Position closed' });
      setTimeout(() => setMessage(null), 3000);
    } catch (error) {
      setMessage({
        type: 'error',
        text: error instanceof Error ? error.message : 'Failed to close position',
      });
    }
  };

  const orderCost = orderForm.quantity * (orderForm.price || 50000);
  const canExecute = orderCost > 0 && orderCost <= availableBalance;

  return (
    <div className={cn('bg-neutral-900 border border-neutral-800 rounded-lg', className)}>
      {/* Header */}
      <div className="flex border-b border-neutral-800">
        <button
          onClick={() => setTab('order')}
          className={cn(
            'flex-1 py-3 font-semibold transition-colors',
            tab === 'order'
              ? 'text-white border-b-2 border-blue-500'
              : 'text-neutral-400 hover:text-white'
          )}
        >
          Place Order
        </button>
        <button
          onClick={() => setTab('positions')}
          className={cn(
            'flex-1 py-3 font-semibold transition-colors relative',
            tab === 'positions'
              ? 'text-white border-b-2 border-blue-500'
              : 'text-neutral-400 hover:text-white'
          )}
        >
          Positions {activeTrades.length > 0 && <span className="ml-1 text-xs">({activeTrades.length})</span>}
        </button>
      </div>

      {/* Messages */}
      {message && (
        <div
          className={cn(
            'p-3 flex items-center gap-2 border-b',
            message.type === 'success'
              ? 'bg-green-500/10 border-green-500/20 text-green-400'
              : 'bg-red-500/10 border-red-500/20 text-red-400'
          )}
        >
          {message.type === 'success' ? (
            <CheckCircle size={16} />
          ) : (
            <AlertCircle size={16} />
          )}
          <span className="text-sm font-medium">{message.text}</span>
        </div>
      )}

      {/* Content */}
      <div className="p-6">
        {tab === 'order' && (
          <div className="space-y-4">
            {/* Pair Selection */}
            <div>
              <label className="block text-sm font-semibold text-white mb-2">Trading Pair</label>
              <select
                value={orderForm.pair}
                onChange={(e) => setOrderForm({ ...orderForm, pair: e.target.value })}
                className="w-full bg-neutral-800 border border-neutral-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-500"
              >
                <option>BTC/USD</option>
                <option>ETH/USD</option>
                <option>EUR/USD</option>
                <option>GBP/USD</option>
              </select>
            </div>

            {/* Side Selection */}
            <div className="grid grid-cols-2 gap-3">
              <button
                onClick={() => setOrderForm({ ...orderForm, side: 'BUY' })}
                className={cn(
                  'py-2 px-4 rounded-lg font-semibold transition-colors flex items-center justify-center gap-2',
                  orderForm.side === 'BUY'
                    ? 'bg-green-500/20 border border-green-500 text-green-400'
                    : 'bg-neutral-800 border border-neutral-700 text-neutral-400 hover:text-white'
                )}
              >
                <ArrowUpRight size={16} />
                BUY
              </button>
              <button
                onClick={() => setOrderForm({ ...orderForm, side: 'SELL' })}
                className={cn(
                  'py-2 px-4 rounded-lg font-semibold transition-colors flex items-center justify-center gap-2',
                  orderForm.side === 'SELL'
                    ? 'bg-red-500/20 border border-red-500 text-red-400'
                    : 'bg-neutral-800 border border-neutral-700 text-neutral-400 hover:text-white'
                )}
              >
                <ArrowDownLeft size={16} />
                SELL
              </button>
            </div>

            {/* Order Type */}
            <div>
              <label className="block text-sm font-semibold text-white mb-2">Order Type</label>
              <div className="grid grid-cols-3 gap-2">
                {['MARKET', 'LIMIT', 'STOP'].map((type) => (
                  <button
                    key={type}
                    onClick={() => setOrderForm({ ...orderForm, type: type as any })}
                    className={cn(
                      'py-2 px-3 rounded-lg text-sm font-semibold transition-colors',
                      orderForm.type === type
                        ? 'bg-blue-600 text-white'
                        : 'bg-neutral-800 text-neutral-400 hover:text-white'
                    )}
                  >
                    {type}
                  </button>
                ))}
              </div>
            </div>

            {/* Quantity */}
            <div>
              <label className="block text-sm font-semibold text-white mb-2">Quantity</label>
              <input
                type="number"
                value={orderForm.quantity}
                onChange={(e) => setOrderForm({ ...orderForm, quantity: parseFloat(e.target.value) })}
                className="w-full bg-neutral-800 border border-neutral-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                placeholder="0.1"
                step="0.01"
              />
            </div>

            {/* Price (if LIMIT) */}
            {orderForm.type === 'LIMIT' && (
              <div>
                <label className="block text-sm font-semibold text-white mb-2">Limit Price</label>
                <input
                  type="number"
                  value={orderForm.price || ''}
                  onChange={(e) => setOrderForm({ ...orderForm, price: parseFloat(e.target.value) })}
                  className="w-full bg-neutral-800 border border-neutral-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                  placeholder="0.00"
                  step="0.01"
                />
              </div>
            )}

            {/* Take Profit & Stop Loss */}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-sm font-semibold text-white mb-2">Take Profit</label>
                <input
                  type="number"
                  value={orderForm.takeProfit || ''}
                  onChange={(e) => setOrderForm({ ...orderForm, takeProfit: parseFloat(e.target.value) })}
                  className="w-full bg-neutral-800 border border-neutral-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-500 text-sm"
                  placeholder="0.00"
                  step="0.01"
                />
              </div>
              <div>
                <label className="block text-sm font-semibold text-white mb-2">Stop Loss</label>
                <input
                  type="number"
                  value={orderForm.stopLoss || ''}
                  onChange={(e) => setOrderForm({ ...orderForm, stopLoss: parseFloat(e.target.value) })}
                  className="w-full bg-neutral-800 border border-neutral-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-500 text-sm"
                  placeholder="0.00"
                  step="0.01"
                />
              </div>
            </div>

            {/* Order Summary */}
            <div className="bg-neutral-800/50 rounded-lg p-3 space-y-1">
              <div className="flex justify-between text-xs">
                <span className="text-neutral-400">Order Cost:</span>
                <span className="text-white font-semibold">${orderCost.toFixed(2)}</span>
              </div>
              <div className="flex justify-between text-xs">
                <span className="text-neutral-400">Available Balance:</span>
                <span className={cn(
                  'font-semibold',
                  canExecute ? 'text-green-400' : 'text-red-400'
                )}>
                  ${availableBalance.toFixed(2)}
                </span>
              </div>
            </div>

            {/* Execute Button */}
            <button
              onClick={handleExecute}
              disabled={loading || !canExecute}
              className={cn(
                'w-full py-3 px-4 rounded-lg font-bold transition-colors',
                canExecute
                  ? `${orderForm.side === 'BUY' ? 'bg-green-600 hover:bg-green-700' : 'bg-red-600 hover:bg-red-700'} text-white`
                  : 'bg-neutral-700 text-neutral-400 cursor-not-allowed'
              )}
            >
              {loading ? 'Executing...' : `Execute ${orderForm.side}`}
            </button>
          </div>
        )}

        {tab === 'positions' && (
          <div className="space-y-3">
            {activeTrades.length > 0 ? (
              activeTrades.map((trade) => (
                <div key={trade.id} className="bg-neutral-800/50 rounded-lg p-4 border border-neutral-700">
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <p className="font-semibold text-white">{trade.pair}</p>
                      <p className={cn(
                        'text-xs font-bold',
                        trade.side === 'BUY' ? 'text-green-400' : 'text-red-400'
                      )}>
                        {trade.side === 'BUY' ? '↑ LONG' : '↓ SHORT'} {trade.quantity}
                      </p>
                    </div>
                    <div className={cn(
                      'text-right',
                      trade.pnlPercent >= 0 ? 'text-green-400' : 'text-red-400'
                    )}>
                      <p className="font-bold">${trade.pnl.toFixed(2)}</p>
                      <p className="text-xs">{trade.pnlPercent >= 0 ? '+' : ''}{trade.pnlPercent.toFixed(2)}%</p>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-2 text-xs mb-3 text-neutral-400">
                    <div>Entry: ${trade.entryPrice.toFixed(2)}</div>
                    <div>Current: ${trade.currentPrice.toFixed(2)}</div>
                  </div>

                  <button
                    onClick={() => handleClosePosition(trade.id)}
                    className="w-full bg-orange-600 hover:bg-orange-700 text-white font-semibold py-2 px-3 rounded transition-colors text-sm"
                  >
                    Close Position
                  </button>
                </div>
              ))
            ) : (
              <div className="text-center py-8 text-neutral-400">
                <p>No open positions</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
