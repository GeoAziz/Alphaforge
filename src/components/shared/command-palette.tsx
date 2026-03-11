'use client';

import * as React from 'react';
import { useRouter } from 'next/navigation';
import { Command } from 'cmdk';
import { 
  Search, 
  Zap, 
  BarChart3, 
  Wallet, 
  Target, 
  FlaskConical, 
  Store, 
  TrendingUp, 
  Settings,
  LayoutDashboard,
  X
} from 'lucide-react';
import { Dialog, DialogContent } from '@/components/ui/dialog';
import { cn } from '@/lib/utils';

const NAV_ITEMS = [
  { name: "Dashboard", href: "/", icon: LayoutDashboard, keywords: "home main overview" },
  { name: "Signals", href: "/signals", icon: Zap, keywords: "alpha alerts trades long short" },
  { name: "Market Intel", href: "/market-intelligence", icon: BarChart3, keywords: "tickers sentiment data prices" },
  { name: "Portfolio", href: "/portfolio", icon: Wallet, keywords: "assets balance holding pnl" },
  { name: "Strategies", href: "/strategies", icon: Target, keywords: "algo logic performance" },
  { name: "Backtesting", href: "/backtesting", icon: FlaskConical, keywords: "simulation historical test" },
  { name: "Marketplace", href: "/marketplace", icon: Store, keywords: "subscribe provider shop" },
  { name: "Analytics", href: "/analytics", icon: TrendingUp, keywords: "metrics growth system" },
  { name: "Settings", href: "/settings", icon: Settings, keywords: "profile api keys risk config" },
];

export function CommandPalette() {
  const [open, setOpen] = React.useState(false);
  const router = useRouter();

  React.useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if (e.key === 'k' && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        setOpen((open) => !open);
      }
    };

    document.addEventListener('keydown', down);
    return () => document.removeEventListener('keydown', down);
  }, []);

  const onSelect = (href: string) => {
    setOpen(false);
    router.push(href);
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogContent className={cn(
        "p-0 border-none bg-transparent shadow-none max-w-2xl overflow-hidden z-[100]",
        "fixed inset-0 sm:inset-auto sm:top-[20%] sm:left-[50%] sm:translate-x-[-50%] sm:translate-y-0",
        "flex flex-col sm:block"
      )}>
        <Command className={cn(
          "glass flex-1 sm:flex-none sm:rounded-2xl overflow-hidden border border-white/10 shadow-[0_32px_64px_-12px_rgba(0,0,0,0.8)]",
          "animate-in fade-in slide-in-from-bottom sm:slide-in-from-top-4 sm:zoom-in-95 duration-500 ease-out-custom"
        )}>
          <div className="flex items-center border-b border-border-subtle px-4 relative">
            <Search className="w-5 h-5 text-text-muted shrink-0" />
            <Command.Input 
              placeholder="Traverse terminal nodes... (⌘K)" 
              className="flex h-16 w-full bg-transparent px-4 text-sm outline-none placeholder:text-text-muted font-black uppercase tracking-tighter text-text-primary"
            />
            <button 
              onClick={() => setOpen(false)}
              className="sm:hidden p-2 text-text-muted hover:text-text-primary"
            >
              <X size={20} />
            </button>
          </div>
          <Command.List className="flex-1 overflow-y-auto p-2 scrollbar-hide max-h-[calc(100vh-120px)] sm:max-h-[400px]">
            <Command.Empty className="py-12 text-center text-sm text-text-muted font-black uppercase tracking-widest opacity-50">
              No matching node identifiers.
            </Command.Empty>
            
            <Command.Group heading="Navigation Clusters" className="px-2 py-3 text-[10px] font-black uppercase text-text-muted tracking-widest">
              {NAV_ITEMS.map((item) => (
                <Command.Item
                  key={item.href}
                  value={item.name + " " + item.keywords}
                  onSelect={() => onSelect(item.href)}
                  className="flex items-center gap-3 px-3 py-3 rounded-xl cursor-pointer hover:bg-primary/10 hover:text-primary transition-all aria-selected:bg-primary/10 aria-selected:text-primary group"
                >
                  <div className="w-8 h-8 rounded-lg bg-elevated flex items-center justify-center text-text-muted group-aria-selected:text-primary group-aria-selected:shadow-[0_0_15px_rgba(96,165,250,0.3)] transition-all">
                    <item.icon className="w-4 h-4" />
                  </div>
                  <div className="flex flex-col">
                    <span className="text-sm font-black tracking-tight uppercase">{item.name}</span>
                    <span className="text-[10px] text-text-muted font-bold lowercase tracking-normal line-clamp-1">{item.keywords}</span>
                  </div>
                </Command.Item>
              ))}
            </Command.Group>
          </Command.List>
          
          <div className="hidden sm:flex items-center justify-between px-4 py-3 bg-elevated/20 border-t border-border-subtle">
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-1.5">
                <kbd className="px-1.5 py-0.5 rounded bg-elevated text-[10px] font-black text-text-muted border border-border-subtle">ESC</kbd>
                <span className="text-[10px] font-black text-text-muted uppercase">Dismiss</span>
              </div>
              <div className="flex items-center gap-1.5">
                <kbd className="px-1.5 py-0.5 rounded bg-elevated text-[10px] font-black text-text-muted border border-border-subtle">↵</kbd>
                <span className="text-[10px] font-black text-text-muted uppercase">Execute</span>
              </div>
            </div>
            <div className="text-[9px] font-black text-primary uppercase tracking-widest">AlphaForge Terminal v1.0.8</div>
          </div>
        </Command>
      </DialogContent>
    </Dialog>
  );
}