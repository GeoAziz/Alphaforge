'use client';

import { useState, useEffect } from 'react';
import { useUser } from '@/firebase';
import { api } from '@/lib/api';
import { SpotlightCard } from '@/components/shared/spotlight-card';
import { Users, Loader2, AlertCircle, Heart, MessageCircle, TrendingUp, Trophy, Star } from 'lucide-react';
import { Badge } from '@/components/ui/badge';

interface UserProfile {
  user_id: string;
  display_name: string;
  bio: string;
  avatar_url?: string;
  total_followers: number;
  total_following: number;
  win_rate: number;
  total_pnl: number;
  average_rr: number;
  verified: boolean;
  created_at: string;
  achievements: string[];
}

interface LeaderboardEntry {
  rank: number;
  user_id: string;
  display_name: string;
  metric_value: number;
  win_rate: number;
  total_trades: number;
}

export default function CommunityPage() {
  const { user } = useUser();
  const [activeTab, setActiveTab] = useState<'leaderboard' | 'profile' | 'discover'>('leaderboard');
  const [leaderboard, setLeaderboard] = useState<LeaderboardEntry[]>([]);
  const [metric, setMetric] = useState<'pnl' | 'sharpe' | 'win_rate'>('pnl');
  const [selectedProfile, setSelectedProfile] = useState<UserProfile | null>(null);
  const [profileLoading, setProfileLoading] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const metricLabels = {
    pnl: 'Profit & Loss',
    sharpe: 'Sharpe Ratio',
    win_rate: 'Win Rate'
  };

  const achievementEmojis: Record<string, string> = {
    first_signal: '⚡',
    first_trade: '💰',
    win_streak_5: '🔥',
    win_streak_10: '🌟',
    profit_1k: '💵',
    profit_10k: '💎',
    popular_strategy: '🏆',
    creator_tier_1: '👑',
    creator_tier_5: '👑👑',
    community_helper: '🤝',
  };

  useEffect(() => {
    api.community?.getLeaderboard?.(metric).then((res) => {
      if (res?.leaderboard) {
        setLeaderboard(res.leaderboard);
      }
      setIsLoading(false);
    }).catch(err => {
      setError(err.message || 'Failed to load leaderboard');
      setIsLoading(false);
    });
  }, [metric]);

  const handleViewProfile = async (userId: string) => {
    setProfileLoading(true);
    try {
      const res = await api.community?.getProfile?.(userId);
      if (res?.profile) {
        setSelectedProfile(res.profile);
        setActiveTab('profile');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load profile');
    } finally {
      setProfileLoading(false);
    }
  };

  if (!user) {
    return (
      <div className="h-full flex items-center justify-center p-8">
        <SpotlightCard className="max-w-md p-10 text-center space-y-6">
          <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center mx-auto text-primary">
            <Users size={32} />
          </div>
          <h2 className="text-2xl font-black uppercase tracking-tighter">Sign In Required</h2>
          <p className="text-sm text-text-muted leading-relaxed">Sign in to join the community.</p>
        </SpotlightCard>
      </div>
    );
  }

  return (
    <div className="p-8 space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-black tracking-tight uppercase leading-none">Community</h1>
          <p className="text-sm text-text-muted mt-2">Connect with traders, view leaderboards, and see top performers.</p>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl border border-red/30 bg-red/5 flex items-center gap-3">
          <AlertCircle size={16} className="text-red shrink-0" />
          <span className="text-xs font-bold text-red">{error}</span>
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-2 border-b border-border">
        <button
          onClick={() => setActiveTab('leaderboard')}
          className={`px-4 py-3 font-black text-xs uppercase tracking-widest transition-all border-b-2 ${
            activeTab === 'leaderboard'
              ? 'border-primary text-primary'
              : 'border-transparent text-text-muted hover:text-text-secondary'
          }`}
        >
          <TrendingUp className="inline mr-2" size={14} />
          Leaderboard
        </button>
        <button
          onClick={() => setActiveTab('profile')}
          className={`px-4 py-3 font-black text-xs uppercase tracking-widest transition-all border-b-2 ${
            activeTab === 'profile'
              ? 'border-primary text-primary'
              : 'border-transparent text-text-muted hover:text-text-secondary'
          }`}
          disabled={!selectedProfile}
        >
          <Users className="inline mr-2" size={14} />
          Profile
        </button>
      </div>

      {/* Leaderboard Tab */}
      {activeTab === 'leaderboard' && (
        <div className="space-y-4">
          <div className="flex gap-2">
            {(Object.entries(metricLabels) as [keyof typeof metricLabels, string][]).map(([key, label]) => (
              <button
                key={key}
                onClick={() => setMetric(key)}
                className={`px-3 py-1 text-xs font-bold rounded-lg uppercase tracking-widest transition-all ${
                  metric === key
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-surface border border-border hover:border-primary/50'
                }`}
              >
                {label}
              </button>
            ))}
          </div>

          {isLoading ? (
            <div className="flex items-center justify-center h-64">
              <Loader2 className="animate-spin text-primary" size={32} />
            </div>
          ) : leaderboard.length === 0 ? (
            <div className="h-64 flex flex-col items-center justify-center text-center space-y-4 rounded-3xl border border-dashed border-border-subtle bg-surface/30">
              <TrendingUp size={40} className="text-text-muted opacity-20" />
              <p className="text-xs font-bold text-text-muted uppercase tracking-widest">No leaderboard data</p>
            </div>
          ) : (
            <div className="grid gap-3">
              {leaderboard.map((entry, idx) => (
                <SpotlightCard
                  key={entry.rank}
                  className="p-4 flex items-center justify-between cursor-pointer hover:bg-elevated/50 transition-all"
                  onClick={() => handleViewProfile(entry.user_id)}
                >
                  <div className="flex items-center gap-4">
                    <div className="font-black text-xl text-primary min-w-[40px] text-center">
                      #{entry.rank}
                    </div>
                    <div>
                      <div className="font-black text-sm">{entry.display_name}</div>
                      <div className="text-xs text-text-muted">
                        {entry.total_trades} trades • WR: {(entry.win_rate * 100).toFixed(1)}%
                      </div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className={`text-sm font-black ${entry.metric_value >= 0 ? 'text-green' : 'text-red'}`}>
                      {entry.metric_value >= 0 ? '+' : ''}{entry.metric_value.toFixed(2)}
                      {metric === 'pnl' ? '%' : ''}
                    </div>
                  </div>
                </SpotlightCard>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Profile Tab */}
      {activeTab === 'profile' && selectedProfile && (
        <SpotlightCard className="p-8 space-y-6">
          <div className="flex items-start justify-between">
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-2xl font-black uppercase tracking-tight">{selectedProfile.display_name}</h2>
                {selectedProfile.verified && <Badge variant="outline">Verified Creator</Badge>}
              </div>
              <p className="text-sm text-text-muted mt-2">{selectedProfile.bio}</p>
            </div>
          </div>

          <div className="grid grid-cols-4 gap-4">
            <div className="p-4 rounded-lg bg-surface border border-border">
              <div className="text-[10px] font-bold text-text-muted uppercase tracking-widest">Followers</div>
              <div className="text-2xl font-black text-primary mt-1">{selectedProfile.total_followers}</div>
            </div>
            <div className="p-4 rounded-lg bg-surface border border-border">
              <div className="text-[10px] font-bold text-text-muted uppercase tracking-widest">Following</div>
              <div className="text-2xl font-black text-primary mt-1">{selectedProfile.total_following}</div>
            </div>
            <div className="p-4 rounded-lg bg-surface border border-border">
              <div className="text-[10px] font-bold text-text-muted uppercase tracking-widest">Win Rate</div>
              <div className="text-2xl font-black text-green mt-1">{(selectedProfile.win_rate * 100).toFixed(1)}%</div>
            </div>
            <div className="p-4 rounded-lg bg-surface border border-border">
              <div className="text-[10px] font-bold text-text-muted uppercase tracking-widest">Total PnL</div>
              <div className={`text-2xl font-black mt-1 ${selectedProfile.total_pnl >= 0 ? 'text-green' : 'text-red'}`}>
                {selectedProfile.total_pnl >= 0 ? '+' : ''}{selectedProfile.total_pnl.toFixed(2)}%
              </div>
            </div>
          </div>

          {selectedProfile.achievements && selectedProfile.achievements.length > 0 && (
            <div className="space-y-3">
              <h3 className="font-black text-sm uppercase tracking-tight">Achievements</h3>
              <div className="flex flex-wrap gap-2">
                {selectedProfile.achievements.map((achievement) => (
                  <div key={achievement} className="flex items-center gap-2 px-3 py-1 rounded-lg bg-primary/10 border border-primary/20">
                    <span className="text-lg">{achievementEmojis[achievement] || '🏆'}</span>
                    <span className="text-xs font-bold uppercase tracking-widest text-primary capitalize">
                      {achievement.replace(/_/g, ' ')}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {user?.uid === selectedProfile.user_id && (
            <button className="w-full px-4 py-2 rounded-lg bg-primary text-primary-foreground text-xs font-black uppercase tracking-widest hover:bg-primary/90">
              Edit Profile
            </button>
          )}
        </SpotlightCard>
      )}
    </div>
  );
}
