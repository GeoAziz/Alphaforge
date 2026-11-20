'use client';

import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Check, ArrowRight, Zap, ShieldCheck } from 'lucide-react';
import Link from 'next/link';
import { cn } from '@/lib/utils';

export function PricingMatrix() {
  const tiers = [
    {
      name: 'Free Explorer',
      price: '$0',
      period: 'forever',
      desc: 'Manual market analytics, historical backtesting exploration, and public cryptographic proof inspection.',
      features: [
        '1 Connected Exchange (Read-Only)',
        'Live Multi-Source Market Data',
        '0 Automated Live Signals/Week',
        'Public Proof Registry Access',
        'Manual Technical Analytics',
        'Standard Community Discord',
      ],
      cta: 'Get Started Free',
      href: '/login',
      highlighted: false,
    },
    {
      name: 'Basic',
      price: '$39',
      period: 'per month',
      desc: 'Ideal for retail traders seeking verified automated signal triggers and full paper simulation capabilities.',
      features: [
        '2 Connected Live Exchanges',
        '6 Verified Automated Signals/Week',
        'Up to 2.0x Margin Leverage',
        'Full 28-Day Paper Trading Simulator',
        '6 Pre-Trade Risk Enforcement Gates',
        'Standard AlphaAI Assistant Chat',
        '7-Day Free Trial Included',
      ],
      cta: 'Start 7-Day Trial',
      href: '/login?tier=basic',
      highlighted: true,
      badge: 'Most Popular',
    },
    {
      name: 'Pro Quant',
      price: '$99',
      period: 'per month',
      desc: 'Advanced algorithmic intelligence with priority execution routing and unlimited conversational quant copilot.',
      features: [
        '4 Connected Live Exchanges',
        '10 Verified Automated Signals/Week',
        'Up to 5.0x Margin Leverage (Global Limit)',
        'Priority Sub-2s ML Signal Routing',
        'Unlimited Streaming AlphaAI Copilot',
        'TradingView Webhook Integration',
        'Creator Marketplace Strategy Following',
      ],
      cta: 'Upgrade to Pro Quant',
      href: '/login?tier=pro',
      highlighted: false,
    },
    {
      name: 'VIP / Institutional',
      price: '$199',
      period: 'per month',
      desc: 'Maximum throughput and API keys for prop traders, quantitative builders, and high-frequency execution.',
      features: [
        '10 Connected Live Exchanges',
        'Unlimited Verified Signals/Week',
        '5.0x Live Leverage (10x Simulation)',
        'Direct REST & WebSocket API Keys',
        'Whitelisted IP Execution Cluster',
        'Custom Risk Engine Parameter Tuning',
        'Dedicated 1-on-1 Quant Architect Support',
      ],
      cta: 'Contact Institutional',
      href: '/login?tier=vip',
      highlighted: false,
    },
  ];

  return (
    <section id="pricing" className="py-24 border-t border-border/40 bg-surface/20 relative">
      <div className="max-w-7xl mx-auto px-6">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <div className="inline-flex items-center gap-2 text-xs font-black uppercase tracking-widest text-primary mb-2">
            <Zap size={14} /> Transparent Subscriptions
          </div>
          <h2 className="text-3xl sm:text-5xl font-black uppercase tracking-tight text-foreground">
            Institutional Alpha. Retail Access.
          </h2>
          <p className="text-muted-foreground text-sm font-medium mt-3 leading-relaxed">
            No hidden commissions or volume markups. Choose the algorithmic power tier matching your portfolio scale.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {tiers.map((tier, idx) => (
            <div
              key={idx}
              className={cn(
                "p-8 rounded-3xl border flex flex-col justify-between transition-all duration-300 relative",
                tier.highlighted
                  ? "border-primary bg-surface/80 shadow-2xl shadow-primary/10 ring-1 ring-primary/40 scale-105 z-10"
                  : "border-border/60 bg-surface/40 hover:bg-surface/70"
              )}
            >
              {tier.badge && (
                <Badge className="absolute -top-3 left-1/2 -translate-x-1/2 bg-primary text-primary-foreground text-[10px] uppercase font-black tracking-widest px-3 py-1 shadow-md">
                  {tier.badge}
                </Badge>
              )}

              <div>
                <h3 className="text-xl font-black text-foreground uppercase tracking-tight">{tier.name}</h3>
                <p className="text-muted-foreground text-xs font-medium mt-2 leading-relaxed h-12">{tier.desc}</p>

                <div className="flex items-baseline gap-1 mt-6">
                  <span className="text-4xl font-black font-mono text-foreground">{tier.price}</span>
                  <span className="text-xs text-muted-foreground font-bold">/{tier.period}</span>
                </div>

                <div className="mt-8 space-y-3.5 border-t border-border/40 pt-6">
                  {tier.features.map((feat, fIdx) => (
                    <div key={fIdx} className="flex items-start gap-2.5 text-xs">
                      <Check size={14} className="text-primary shrink-0 mt-0.5" />
                      <span className="text-foreground/90 font-medium">{feat}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="mt-8 pt-6 border-t border-border/40">
                <Link href={tier.href} className="w-full">
                  <Button
                    className={cn(
                      "w-full h-12 uppercase text-xs font-black tracking-wider gap-2",
                      tier.highlighted
                        ? "bg-primary hover:bg-primary/90 text-primary-foreground shadow-lg shadow-primary/25"
                        : "bg-surface hover:bg-elevated text-foreground border border-border/80"
                    )}
                  >
                    {tier.cta} <ArrowRight size={14} />
                  </Button>
                </Link>
              </div>
            </div>
          ))}
        </div>

        {/* Leverage & Risk Clarification Notice */}
        <div className="mt-12 text-center text-[11px] text-muted-foreground font-mono max-w-2xl mx-auto">
          * Effective Leverage Rule: Live margin execution is strictly capped at the 5.0x global platform limit across all tiers. Higher leverage ratios (10.0x) are strictly restricted to isolated paper trading simulations.
        </div>
      </div>
    </section>
  );
}
