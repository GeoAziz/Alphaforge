'use client';

import { useState, useEffect } from 'react';
import { useUser } from '@/firebase';
import { api } from '@/lib/api';
import { SpotlightCard } from '@/components/shared/spotlight-card';
import { Trophy, Loader2, AlertCircle, Users, Calendar, TrendingUp } from 'lucide-react';
import { Badge } from '@/components/ui/badge';

interface Tournament {
  id: string;
  name: string;
  status: string;
  start_time: string;
  end_time: string;
  description?: string;
  total_entries?: number;
  prize_pool?: string;
}

interface LeaderboardEntry {
  rank: number;
  user_id: string;
  display_name: string;
  final_pnl: number;
  final_sharpe: number;
  final_win_rate: number;
}

export default function TournamentsPage() {
  const { user } = useUser();
  const [tournaments, setTournaments] = useState<Tournament[]>([]);
  const [selectedTournament, setSelectedTournament] = useState<Tournament | null>(null);
  const [leaderboard, setLeaderboard] = useState<LeaderboardEntry[]>([]);
  const [sortBy, setSortBy] = useState<'final_pnl' | 'final_sharpe' | 'final_win_rate'>('final_pnl');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isJoining, setIsJoining] = useState(false);
  const [userJoined, setUserJoined] = useState(false);

  useEffect(() => {
    api.tournaments?.listTournaments?.().then((res) => {
      if (res?.tournaments) {
        setTournaments(res.tournaments);
        if (res.tournaments.length > 0) {
          setSelectedTournament(res.tournaments[0]);
        }
      }
      setIsLoading(false);
    }).catch(err => {
      setError(err.message || 'Failed to load tournaments');
      setIsLoading(false);
    });
  }, [user]);

  useEffect(() => {
    if (selectedTournament && user?.uid) {
      api.tournaments?.getLeaderboard?.(selectedTournament.id, sortBy).then((res) => {
        if (res?.leaderboard) {
          setLeaderboard(res.leaderboard);
        }
      }).catch(console.error);

      api.tournaments?.getMyStatus?.(selectedTournament.id, user.uid).then((res) => {
        setUserJoined(res?.success === true);
      }).catch(() => setUserJoined(false));
    }
  }, [selectedTournament, sortBy, user?.uid]);

  async function handleJoinTournament() {
    if (!user?.uid || !selectedTournament) return;
    setIsJoining(true);
    try {
      await api.tournaments?.joinTournament?.(selectedTournament.id, user.uid);
      setUserJoined(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to join tournament');
    } finally {
      setIsJoining(false);
    }
  }

  if (!user) {
    return (
      <div className="h-full flex items-center justify-center p-8">
        <SpotlightCard className="max-w-md p-10 text-center space-y-6">
          <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center mx-auto text-primary">
            <Trophy size={32} />
          </div>
          <h2 className="text-2xl font-black uppercase tracking-tighter">Sign In Required</h2>
          <p className="text-sm text-text-muted leading-relaxed">Sign in to compete in tournaments.</p>
        </SpotlightCard>
      </div>
    );
  }

  return (
    <div className="p-8 space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-black tracking-tight uppercase leading-none">Tournaments</h1>
          <p className="text-sm text-text-muted mt-2">Monthly trading competitions with real leaderboards.</p>
        </div>
        <div className="text-right">
          <div className="text-2xl font-black text-primary">{tournaments.length}</div>
          <div className="text-[10px] font-bold text-text-muted uppercase tracking-widest">Active</div>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl border border-red/30 bg-red/5 flex items-center gap-3">
          <AlertCircle size={16} className="text-red shrink-0" />
          <span className="text-xs font-bold text-red">{error}</span>
        </div>
      )}

      {isLoading ? (
        <div className="flex items-center justify-center h-64">
          <Loader2 className="animate-spin text-primary" size={32} />
        </div>
      ) : tournaments.length === 0 ? (
        <div className="h-64 flex flex-col items-center justify-center text-center space-y-4 rounded-3xl border border-dashed border-border-subtle bg-surface/30">
          <Trophy size={40} className="text-text-muted opacity-20" />
          <p className="text-xs font-bold text-text-muted uppercase tracking-widest">No tournaments active</p>
        </div>
      ) : selectedTournament ? (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-1 space-y-4">
            <div className="space-y-2">
              {tournaments.map((t) => (
                <button
                  key={t.id}
                  onClick={() => setSelectedTournament(t)}
                  className={`w-full text-left p-4 rounded-xl border transition-all ${
                    selectedTournament.id === t.id
                      ? 'border-primary bg-primary/5'
                      : 'border-border hover:border-primary/50'
                  }`}
                >
                  <div className="font-black uppercase text-sm tracking-tight">{t.name}</div>
                  <div className="text-[10px] text-text-muted uppercase tracking-widest mt-1">
                    <Badge variant="outline" className="text-[8px]">{t.status.toLowerCase()}</Badge>
                  </div>
                </button>
              ))}
            </div>
          </div>

          <div className="lg:col-span-2 space-y-6">
            <SpotlightCard className="p-6 space-y-4">
              <div className="flex items-start justify-between">
                <div>
                  <h2 className="text-2xl font-black uppercase tracking-tight">{selectedTournament.name}</h2>
                  <p className="text-xs text-text-muted mt-1">{selectedTournament.description || 'Monthly trading tournament'}</p>
                </div>
                <Badge variant="outline">{selectedTournament.status}</Badge>
              </div>

              <div className="grid grid-cols-3 gap-4">
                <div className="flex items-center gap-2">
                  <Calendar size={16} className="text-primary" />
                  <div>
                    <div className="text-[10px] font-bold text-text-muted uppercase">Starts</div>
                    <div className="text-xs font-black">{new Date(selectedTournament.start_time).toLocaleDateString()}</div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Users size={16} className="text-primary" />
                  <div>
                    <div className="text-[10px] font-bold text-text-muted uppercase">Entries</div>
                    <div className="text-xs font-black">{selectedTournament.total_entries || 0}</div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <TrendingUp size={16} className="text-primary" />
                  <div>
                    <div className="text-[10px] font-bold text-text-muted uppercase">Prize Pool</div>
                    <div className="text-xs font-black">{selectedTournament.prize_pool || 'TBD'}</div>
                  </div>
                </div>
              </div>

              {userJoined ? (
                <div className="px-4 py-2 rounded-lg bg-green/10 border border-green/30 text-xs font-bold text-green uppercase">
                  ✓ You're in this tournament
                </div>
              ) : (
                <button
                  onClick={handleJoinTournament}
                  disabled={isJoining}
                  className="w-full px-4 py-2 rounded-xl bg-primary text-primary-foreground text-xs font-black uppercase tracking-widest hover:bg-primary/90 disabled:opacity-50"
                >
                  {isJoining ? 'Joining...' : 'Join Tournament'}
                </button>
              )}
            </SpotlightCard>

            <SpotlightCard className="p-6 space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="font-black uppercase text-sm tracking-tight">Leaderboard</h3>
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value as any)}
                  className="text-[10px] font-bold px-2 py-1 rounded-lg bg-surface border border-border uppercase"
                >
                  <option value="final_pnl">PnL</option>
                  <option value="final_sharpe">Sharpe</option>
                  <option value="final_win_rate">Win Rate</option>
                </select>
              </div>

              <div className="space-y-2">
                {leaderboard.length === 0 ? (
                  <div className="text-center py-8 text-xs text-text-muted">No entries yet</div>
                ) : (
                  leaderboard.map((entry) => (
                    <div key={entry.rank} className="flex items-center justify-between p-3 rounded-lg bg-surface/30 border border-border">
                      <div className="flex items-center gap-3">
                        <div className="font-black text-primary min-w-[24px]">#{entry.rank}</div>
                        <div>
                          <div className="text-xs font-black">{entry.display_name}</div>
                          <div className="text-[10px] text-text-muted">Sharpe: {entry.final_sharpe.toFixed(2)}</div>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className={`text-xs font-black ${entry.final_pnl >= 0 ? 'text-green' : 'text-red'}`}>
                          {entry.final_pnl >= 0 ? '+' : ''}{entry.final_pnl.toFixed(2)}%
                        </div>
                        <div className="text-[10px] text-text-muted">WR: {(entry.final_win_rate * 100).toFixed(1)}%</div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </SpotlightCard>
          </div>
        </div>
      ) : null}
    </div>
  );
}
