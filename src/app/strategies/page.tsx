'use client';

import { useState } from 'react';
import { useFirestore, useCollection, useMemoFirebase, useUser } from '@/firebase';
import { collection, query, orderBy } from 'firebase/firestore';
import { SpotlightCard } from '@/components/shared/spotlight-card';
import { StrategyCard } from '@/components/strategies/strategy-card';
import { StrategyDetailPanel } from '@/components/strategies/strategy-detail-panel';
import { StrategyGrid } from '@/components/strategies/strategy-grid';
import { Strategy } from '@/lib/types';
import { ShieldAlert } from 'lucide-react';

export default function StrategiesPage() {
  const { user } = useUser();
  const db = useFirestore();
  const [selectedStrategy, setSelectedStrategy] = useState<Strategy | null>(null);

  const strategiesQuery = useMemoFirebase(() => {
    if (!db || !user) return null;
    return query(collection(db, 'users', user.uid, 'strategies'), orderBy('winRate', 'desc'));
  }, [db, user]);

  const { data: strategies, isLoading } = useCollection<Strategy>(strategiesQuery);

  if (!user) {
    return (
      <div className="h-full flex items-center justify-center p-8">
        <SpotlightCard className="max-w-md p-10 text-center space-y-6">
          <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center mx-auto text-primary">
            <ShieldAlert size={32} />
          </div>
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
