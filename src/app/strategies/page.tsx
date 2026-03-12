'use client';

import { useState, useEffect } from 'react';
import { useUser } from '@/firebase';
// Firebase hooks removed in MVP mock mode:
// import { useFirestore, useCollection, useMemoFirebase } from '@/firebase';
// import { collection, query, orderBy } from 'firebase/firestore';
import { api } from '@/lib/api';
import { SpotlightCard } from '@/components/shared/spotlight-card';
import { StrategyDetailPanel } from '@/components/strategies/strategy-detail-panel';
import { StrategyGrid } from '@/components/strategies/strategy-grid';
import { Strategy } from '@/lib/types';

export default function StrategiesPage() {
  const { user } = useUser();
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedStrategy, setSelectedStrategy] = useState<Strategy | null>(null);

  useEffect(() => {
    api.strategies.getUserStrategies(user?.uid || 'mock-user-001').then(data => {
      setStrategies(data);
      setIsLoading(false);
    });
  }, [user]);

  if (!user) {
    return (
      <div className="h-full flex items-center justify-center p-8">
        <SpotlightCard className="max-w-md p-10 text-center space-y-6">
          <h2 className="text-2xl font-black uppercase">Strategies Restricted</h2>
          <p className="text-sm text-text-muted">Please connect your session to browse proprietary algorithmic engines.</p>
        </SpotlightCard>
      </div>
    );
  }

  return (
    <div className="p-8 space-y-8 pb-20 animate-page">
      <header className="space-y-1">
        <h1 className="text-3xl font-black tracking-tight uppercase">Core Strategies</h1>
        <p className="text-muted-foreground text-sm">Proprietary algorithmic engines driving AlphaForge intelligence.</p>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
        <StrategyGrid 
          strategies={strategies || []} 
          onSelectStrategy={setSelectedStrategy}
          selectedId={selectedStrategy?.id}
          isLoading={isLoading}
        />
      </div>

      {/* Strategy Detail Panel */}
      <StrategyDetailPanel 
        strategy={selectedStrategy} 
        onDismiss={() => setSelectedStrategy(null)}
        onSubscribe={(strategy) => {
          // Subscribe logic here
          setSelectedStrategy(null);
        }}
      />
    </div>
  );
}
