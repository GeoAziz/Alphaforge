'use client';

import { ShieldCheck, Lock, KeyRound, Server, AlertOctagon, CheckCircle2 } from 'lucide-react';

export function SecurityArchitecture() {
  const securityPillars = [
    {
      title: 'Non-Custodial Design',
      desc: 'AlphaForge never holds, deposits, or pools client funds. Capital stays directly in your personal exchange account.',
      icon: ShieldCheck,
    },
    {
      title: 'Zero Withdrawal Permissions',
      desc: 'API connections strictly require "Trading Enabled" and "Withdrawals Disabled". Verification rejects keys with withdrawal rights.',
      icon: AlertOctagon,
    },
    {
      title: 'KMS AES-256 Encryption',
      desc: 'Exchange credentials are encrypted at rest using envelope encryption (AES-256) via isolated Key Management Services.',
      icon: Lock,
    },
    {
      title: 'Automated IP Whitelisting',
      desc: 'Orders route exclusively through dedicated static IP ranges whitelisted on your exchange matching account.',
      icon: Server,
    },
  ];

  return (
    <section className="py-24 border-t border-border/40 relative">
      <div className="max-w-7xl mx-auto px-6">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <div className="inline-flex items-center gap-2 text-xs font-black uppercase tracking-widest text-primary mb-2">
            <Lock size={14} /> Security Architecture
          </div>
          <h2 className="text-3xl sm:text-5xl font-black uppercase tracking-tight text-foreground">
            Zero-Trust Execution Security
          </h2>
          <p className="text-muted-foreground text-sm font-medium mt-3 leading-relaxed">
            Engineered from day one with institutional safety guardrails. Your assets never leave your exchange.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {securityPillars.map((pillar, idx) => {
            const Icon = pillar.icon;
            return (
              <div
                key={idx}
                className="p-8 rounded-3xl border border-border/60 bg-surface/50 hover:bg-surface/80 transition-all duration-300 flex flex-col justify-between"
              >
                <div>
                  <div className="w-12 h-12 rounded-2xl bg-primary/10 flex items-center justify-center text-primary mb-6 border border-primary/20">
                    <Icon size={22} />
                  </div>
                  <h3 className="text-lg font-black text-foreground uppercase tracking-tight">{pillar.title}</h3>
                  <p className="text-muted-foreground text-xs font-medium leading-relaxed mt-3">{pillar.desc}</p>
                </div>

                <div className="mt-8 pt-4 border-t border-border/40 flex items-center gap-2 text-[11px] font-bold text-green font-mono">
                  <CheckCircle2 size={14} /> Enforced by Gate 1 & 4
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
