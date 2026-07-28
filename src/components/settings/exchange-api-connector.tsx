'use client';

import React, { useState } from 'react';
import { Lock, Eye, EyeOff, AlertCircle, CheckCircle, Trash2 } from 'lucide-react';
import { cn } from '@/lib/utils';

interface Exchange {
  id: string;
  name: string;
  logo: string;
  description: string;
}

interface ConnectedExchange {
  id: string;
  exchange: string;
  status: 'connected' | 'disconnected' | 'error';
  lastSync: string;
  apiKey: string;
  secretKey: string;
}

const EXCHANGES: Exchange[] = [
  {
    id: 'binance',
    name: 'Binance',
    logo: '₿',
    description: 'Connect to Binance for live trading',
  },
  {
    id: 'okx',
    name: 'OKX',
    logo: '◊',
    description: 'Access OKX exchange markets',
  },
  {
    id: 'bybit',
    name: 'Bybit',
    logo: '⬘',
    description: 'Trade on Bybit perpetuals',
  },
  {
    id: 'kraken',
    name: 'Kraken',
    logo: 'K',
    description: 'Connect to Kraken Pro',
  },
];

interface ExchangeAPIConnectorProps {
  onConnect?: (exchange: string, apiKey: string, secretKey: string) => Promise<void>;
  onDisconnect?: (exchangeId: string) => Promise<void>;
  connectedExchanges?: ConnectedExchange[];
  className?: string;
}

export function ExchangeAPIConnector({
  onConnect,
  onDisconnect,
  connectedExchanges = [],
  className = '',
}: ExchangeAPIConnectorProps) {
  const [selectedExchange, setSelectedExchange] = useState<string | null>(null);
  const [apiKey, setApiKey] = useState('');
  const [secretKey, setSecretKey] = useState('');
  const [showSecret, setShowSecret] = useState(false);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const handleConnect = async () => {
    if (!selectedExchange || !apiKey || !secretKey) {
      setMessage({ type: 'error', text: 'Please fill in all fields' });
      return;
    }

    try {
      setLoading(true);
      if (onConnect) {
        await onConnect(selectedExchange, apiKey, secretKey);
      }
      setMessage({ type: 'success', text: 'Exchange connected successfully!' });
      setApiKey('');
      setSecretKey('');
      setSelectedExchange(null);
      setTimeout(() => setMessage(null), 3000);
    } catch (error) {
      setMessage({
        type: 'error',
        text: error instanceof Error ? error.message : 'Connection failed',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleDisconnect = async (exchangeId: string) => {
    if (onDisconnect) {
      try {
        await onDisconnect(exchangeId);
        setMessage({ type: 'success', text: 'Disconnected successfully' });
        setTimeout(() => setMessage(null), 3000);
      } catch (error) {
        setMessage({
          type: 'error',
          text: error instanceof Error ? error.message : 'Disconnection failed',
        });
      }
    }
  };

  return (
    <div className={cn('space-y-6', className)}>
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-white flex items-center gap-2">
          <Lock size={24} className="text-blue-400" />
          Exchange Connections
        </h2>
        <p className="text-neutral-400 text-sm mt-1">Connect your exchange accounts to enable live trading</p>
      </div>

      {/* Messages */}
      {message && (
        <div
          className={cn(
            'p-4 rounded-lg flex items-center gap-3 border',
            message.type === 'success'
              ? 'bg-green-500/10 border-green-500/20 text-green-400'
              : 'bg-red-500/10 border-red-500/20 text-red-400'
          )}
        >
          {message.type === 'success' ? (
            <CheckCircle size={16} className="shrink-0" />
          ) : (
            <AlertCircle size={16} className="shrink-0" />
          )}
          <span className="text-sm font-medium">{message.text}</span>
        </div>
      )}

      {/* Connected Exchanges */}
      {connectedExchanges.length > 0 && (
        <div className="bg-neutral-900 border border-neutral-800 rounded-lg p-6">
          <h3 className="text-lg font-bold text-white mb-4">Connected Exchanges</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {connectedExchanges.map((exchange) => (
              <div
                key={exchange.id}
                className="bg-neutral-800/50 rounded-lg p-4 border border-neutral-700"
              >
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <p className="font-semibold text-white capitalize">{exchange.exchange}</p>
                    <p className={cn(
                      'text-xs font-bold mt-1',
                      exchange.status === 'connected' ? 'text-green-400' : 'text-orange-400'
                    )}>
                      {exchange.status === 'connected' ? '● Connected' : '● Disconnected'}
                    </p>
                  </div>
                  <button
                    onClick={() => handleDisconnect(exchange.id)}
                    className="text-red-400 hover:text-red-300 transition-colors"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>

                <div className="space-y-2 text-xs text-neutral-400 mb-3">
                  <p>API Key: {exchange.apiKey.slice(0, 8)}...{exchange.apiKey.slice(-4)}</p>
                  <p>Last synced: {new Date(exchange.lastSync).toLocaleString()}</p>
                </div>

                <button className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-3 rounded transition-colors text-sm">
                  Verify Connection
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Add New Exchange */}
      <div className="bg-neutral-900 border border-neutral-800 rounded-lg p-6">
        <h3 className="text-lg font-bold text-white mb-4">Add Exchange</h3>

        {!selectedExchange ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {EXCHANGES.filter(
              (ex) => !connectedExchanges.some((c) => c.exchange.toLowerCase() === ex.id)
            ).map((exchange) => (
              <button
                key={exchange.id}
                onClick={() => setSelectedExchange(exchange.id)}
                className="bg-neutral-800/50 hover:bg-neutral-700 border border-neutral-700 rounded-lg p-4 transition-colors text-left"
              >
                <div className="text-3xl mb-2">{exchange.logo}</div>
                <p className="font-semibold text-white">{exchange.name}</p>
                <p className="text-xs text-neutral-400 mt-1">{exchange.description}</p>
              </button>
            ))}
          </div>
        ) : (
          <div className="space-y-4">
            {/* Back Button */}
            <button
              onClick={() => setSelectedExchange(null)}
              className="text-sm text-blue-400 hover:text-blue-300"
            >
              ← Back
            </button>

            {/* API Key Form */}
            <div>
              <label className="block text-sm font-semibold text-white mb-2">API Key</label>
              <input
                type="password"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                placeholder="Enter your API key"
                className="w-full bg-neutral-800 border border-neutral-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-500"
              />
              <p className="text-xs text-neutral-400 mt-1">🔒 Your key is encrypted and never stored in plain text</p>
            </div>

            {/* Secret Key Form */}
            <div>
              <label className="block text-sm font-semibold text-white mb-2">Secret Key</label>
              <div className="relative">
                <input
                  type={showSecret ? 'text' : 'password'}
                  value={secretKey}
                  onChange={(e) => setSecretKey(e.target.value)}
                  placeholder="Enter your secret key"
                  className="w-full bg-neutral-800 border border-neutral-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-500 pr-10"
                />
                <button
                  onClick={() => setShowSecret(!showSecret)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-neutral-400 hover:text-white"
                >
                  {showSecret ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>

            {/* Permissions Info */}
            <div className="bg-yellow-500/10 border border-yellow-500/20 rounded-lg p-3">
              <p className="text-xs text-yellow-600 font-semibold">⚠️ Required Permissions:</p>
              <ul className="text-xs text-yellow-600 mt-2 space-y-1">
                <li>✓ Read account data</li>
                <li>✓ Read trading history</li>
                <li>✓ Place/cancel orders</li>
                <li>✗ Withdraw funds (not needed)</li>
              </ul>
            </div>

            {/* Buttons */}
            <div className="grid grid-cols-2 gap-3">
              <button
                onClick={() => setSelectedExchange(null)}
                className="bg-neutral-700 hover:bg-neutral-600 text-white font-semibold py-2 px-4 rounded transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleConnect}
                disabled={loading}
                className="bg-blue-600 hover:bg-blue-700 disabled:bg-neutral-700 text-white font-semibold py-2 px-4 rounded transition-colors"
              >
                {loading ? 'Connecting...' : 'Connect'}
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Security Info */}
      <div className="bg-blue-500/10 border border-blue-500/20 rounded-lg p-4">
        <p className="text-sm text-blue-300 font-semibold mb-2">🔐 Security Note</p>
        <ul className="text-xs text-blue-300 space-y-1">
          <li>• We recommend using API keys with read-only or limited trading permissions</li>
          <li>• Enable IP whitelisting on your exchange for added security</li>
          <li>• Never share your API keys or secret keys with anyone</li>
          <li>• Regularly rotate your keys (at least every 90 days)</li>
        </ul>
      </div>
    </div>
  );
}
