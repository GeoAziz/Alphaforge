'use client';

import { useState, useEffect } from 'react';
import { useUser } from '@/firebase';
import { api } from '@/lib/api';
import { EducationContent } from '@/lib/types';
import { SpotlightCard } from '@/components/shared/spotlight-card';
import { GraduationCap, AlertCircle, CheckCircle2, Loader2 } from 'lucide-react';
import { Badge } from '@/components/ui/badge';

export default function AcademyPage() {
  const { user } = useUser();
  const [content, setContent] = useState<EducationContent[]>([]);
  const [completedIds, setCompletedIds] = useState<Set<string>>(new Set());
  const [completionPct, setCompletionPct] = useState(0);
  const [selected, setSelected] = useState<EducationContent | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.academy.listContent().then(async (res) => {
      setContent(res.content);
      if (user?.uid) {
        const progress = await api.academy.getProgress(user.uid).catch(() => null);
        if (progress?.success) {
          setCompletedIds(new Set(progress.progress.filter(p => p.completed).map(p => p.content_id)));
          setCompletionPct(progress.completion_pct);
        }
      }
      setIsLoading(false);
    }).catch(err => {
      setError(err.message || 'Failed to load academy content');
      setIsLoading(false);
    });
  }, [user]);

  async function handleMarkComplete(contentId: string) {
    if (!user?.uid) return;
    try {
      await api.academy.markCompleted(user.uid, contentId);
      setCompletedIds(prev => new Set(prev).add(contentId));
    } catch (err) {
      console.error('Failed to mark content complete:', err);
    }
  }

  if (!user) {
    return (
      <div className="h-full flex items-center justify-center p-8">
        <SpotlightCard className="max-w-md p-10 text-center space-y-6">
          <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center mx-auto text-primary">
            <GraduationCap size={32} />
          </div>
          <h2 className="text-2xl font-black uppercase tracking-tighter">Handshake Restricted</h2>
          <p className="text-sm text-text-muted leading-relaxed">Sign in to access AlphaAcademy.</p>
        </SpotlightCard>
      </div>
    );
  }

  return (
    <div className="p-8 space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-black tracking-tight uppercase leading-none">AlphaAcademy</h1>
          <p className="text-sm text-text-muted mt-2">Signal patterns, strategy guides, and quant basics.</p>
        </div>
        {user && (
          <div className="text-right">
            <div className="text-2xl font-black text-primary">{completionPct}%</div>
            <div className="text-[10px] font-bold text-text-muted uppercase tracking-widest">Complete</div>
          </div>
        )}
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
      ) : content.length === 0 ? (
        <div className="h-64 flex flex-col items-center justify-center text-center space-y-4 rounded-3xl border border-dashed border-border-subtle bg-surface/30">
          <GraduationCap size={40} className="text-text-muted opacity-20" />
          <p className="text-xs font-bold text-text-muted uppercase tracking-widest">No content published yet</p>
        </div>
      ) : selected ? (
        <SpotlightCard className="p-8 space-y-6">
          <button onClick={() => setSelected(null)} className="text-[10px] font-black uppercase text-primary hover:text-primary/80">
            &larr; Back to library
          </button>
          <div className="flex items-center gap-3">
            <h2 className="text-xl font-black uppercase tracking-tight">{selected.title}</h2>
            <Badge variant="outline">{selected.difficulty}</Badge>
            <Badge variant="outline">{selected.category}</Badge>
          </div>
          <div className="text-sm text-text-secondary leading-relaxed whitespace-pre-wrap">{selected.content}</div>
          {completedIds.has(selected.content_id) ? (
            <div className="flex items-center gap-2 text-green">
              <CheckCircle2 size={16} />
              <span className="text-xs font-bold uppercase">Completed</span>
            </div>
          ) : (
            <button
              onClick={() => handleMarkComplete(selected.content_id)}
              className="px-4 py-2 rounded-xl bg-primary text-primary-foreground text-xs font-black uppercase tracking-widest hover:bg-primary/90"
            >
              Mark as Complete
            </button>
          )}
        </SpotlightCard>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {content.map((c) => (
            <SpotlightCard key={c.content_id} className="p-6 space-y-4 cursor-pointer" onClick={() => setSelected(c)}>
              <div className="flex items-center justify-between">
                <Badge variant="outline">{c.difficulty}</Badge>
                {completedIds.has(c.content_id) && <CheckCircle2 size={16} className="text-green" />}
              </div>
              <h3 className="font-black uppercase tracking-tight">{c.title}</h3>
              <p className="text-[10px] font-bold text-text-muted uppercase tracking-widest">{c.category}</p>
            </SpotlightCard>
          ))}
        </div>
      )}
    </div>
  );
}
