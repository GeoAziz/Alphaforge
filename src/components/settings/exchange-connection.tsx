'use client';

import { SpotlightCard } from '@/components/shared/spotlight-card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { LinkIcon, Plus, Trash2, CheckCircle2, AlertCircle } from 'lucide-react';
import { useState } from 'react';

interface ExchangeConnection {
  id: string;
  name: string;
  connected: boolean;
  connectedAt?: string;
  apiKeyPreview?: string;
}

export function ExchangeConnection() {
  const [exchanges, setExchanges] = useState<ExchangeConnection[]>([
    { id: '1', name: 'Binance', connected: true, connectedAt: '2026-03-01', apiKeyPreview: '••••••••56a2' },
    { id: '2', name: 'Bybit', connected: false },
  ]);
  const [isAdding, setIsAdding] = useState(false);
  const [newExchange, setNewExchange] = useState('');
  const [apiKey, setApiKey] = useState('');
  const [apiSecret, setApiSecret] = useState('');

  return (
    <div className="space-y-6">
      <SpotlightCard className="p-8">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-black uppercase tracking-tight flex items-center gap-2 text-text-primary">
            <LinkIcon size={18} className="text-primary" />
            Exchange Integrations
          </h3>
        </div>

        <div className="space-y-4 mb-8">
          {exchanges.map((exchange) => (
            <div key={exchange.id} className="p-4 rounded-xl bg-elevated/20 border border-border-subtle flex items-center justify-between hover:bg-elevated/40 transition-all">
              <div className="flex items-center gap-4">
                <div className="flex-1">
                  <div className="text-sm font-bold text-text-primary">{exchange.name}</div>
                  {exchange.connected && (
                    <div className="text-[9px] text-text-muted mt-1">Connected since {exchange.connectedAt}</div>
                  )}
                </div>
                {exchange.connected && (
                  <Badge className="bg-green/10 text-green border-green/20 font-black">
                    <CheckCircle2 size={12} className="mr-1" /> Active
                  </Badge>
                )}
                {!exchange.connected && (
                  <Badge className="bg-amber/10 text-amber border-amber/20 font-black">
                    <AlertCircle size={12} className="mr-1" /> Pending
                  </Badge>
                )}
              </div>
              {exchange.connected && (
                <Button 
                  variant="ghost" 
                  size="sm"
                  onClick={() => setExchanges(exchanges.filter(e => e.id !== exchange.id))}
                  className="text-red hover:text-red"
                >
                  <Trash2 size={16} />
                </Button>
              )}
            </div>
          ))}
        </div>

        {isAdding ? (
          <div className="space-y-4 p-6 rounded-xl bg-elevated/20 border border-border-subtle">
            <div>
              <Label className="text-xs font-black uppercase">Exchange</Label>
              <select 
                value={newExchange}
                onChange={(e) => setNewExchange(e.target.value)}
                className="w-full mt-2 px-4 py-2 bg-surface border border-border rounded-lg text-text-primary font-mono text-sm"
              >
                <option value="">Select Exchange</option>
                <option value="binance">Binance</option>
                <option value="bybit">Bybit</option>
                <option value="okx">OKX</option>
                <option value="kraken">Kraken</option>
              </select>
            </div>
            <div>
              <Label className="text-xs font-black uppercase">API Key</Label>
              <Input 
                type="password"
                placeholder="your-api-key"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                className="mt-2 font-mono"
              />
            </div>
            <div>
              <Label className="text-xs font-black uppercase">API Secret</Label>
              <Input 
                type="password"
                placeholder="your-api-secret"
                value={apiSecret}
                onChange={(e) => setApiSecret(e.target.value)}
                className="mt-2 font-mono"
              />
            </div>
            <div className="flex gap-2">
              <Button className="flex-1 bg-primary text-primary-foreground font-black">Connect</Button>
              <Button 
                variant="outline"
                className="flex-1"
                onClick={() => setIsAdding(false)}
              >
                Cancel
              </Button>
            </div>
          </div>
        ) : (
          <Button 
            onClick={() => setIsAdding(true)}
            className="w-full bg-primary/10 text-primary border border-primary/20 hover:bg-primary/20 font-black uppercase"
          >
            <Plus size={16} className="mr-2" />
            Add Exchange
          </Button>
        )}
      </SpotlightCard>
    </div>
  );
}
