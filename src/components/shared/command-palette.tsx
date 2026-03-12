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
  X,
  ArrowRight
} from 'lucide-react';
import { Dialog, DialogContent, DialogTitle } from '@/components/ui/dialog';
import { cn } from '@/lib/utils';

const NAV_ITEMS = [
  { name: "Dashboard", href: "/", icon: LayoutDashboard, keywords: "home main overview", cluster: "Primary" },
  { name: "Signals", href: "/signals", icon: Zap, keywords: "alpha alerts trades long short", cluster: "Intelligence" },
  { name: "Market Intel", href: "/market-intelligence", icon: BarChart3, keywords: "tickers sentiment data prices", cluster: "Intelligence" },
  { name: "Portfolio", href: "/portfolio", icon: Wallet, keywords: "assets balance holding pnl", cluster: "Execution" },
  { name: "Strategies", href: "/strategies", icon: Target, keywords: "algo logic performance", cluster: "Execution" },
  { name: "Backtesting", href: "/backtesting", icon: FlaskConical, keywords: "simulation historical test", cluster: "Analytics" },
  { name: "Marketplace", href: "/marketplace", icon: Store, keywords: "subscribe provider shop", cluster: "Social" },
  { name: "Analytics", href: "/analytics", icon: TrendingUp, keywords: "metrics growth system", cluster: "Analytics" },
  { name: "Settings", href: "/settings", icon: Settings, keywords: "profile api keys risk config", cluster: "System" },
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
        "fixed inset-x-0 bottom-0 sm:inset-auto sm:top-[20%] sm:left-[50%] sm:translate-x-[-50%] sm:translate-y-0",
        "flex flex-col sm:block h-[80vh] sm:h-auto rounded-t-3xl sm:rounded-none"
      )}>
        <DialogTitle className="sr-only">Traverse Terminal Nodes</DialogTitle>
        <Command className={cn(
          "glass flex-1 sm:flex-none sm:rounded-2xl overflow-hidden border border-white/10 shadow-[0_32px_64px_-12px_rgba(0,0,0,0.8)]",
          "animate-in slide-in-from-bottom sm:zoom-in-95 duration-500 ease-out-custom h-full flex flex-col"
        )}>
          <div className="flex items-center border-b border-border-subtle px-6 relative shrink-0">
            <Search className="w-5 h-5 text-text-muted shrink-0" />
            <Command.Input 
              placeholder="Initialize traverse handshake... (⌘K)" 
              className="flex h-20 w-full bg-transparent px-4 text-sm outline-none placeholder:text-text-muted font-black uppercase tracking-widest text-text-primary"
            />
            <button 
              onClick={() => setOpen(false)}
              className="p-2 text-text-muted hover:text-text-primary transition-colors bg-elevated/50 rounded-xl"
            >
              <X size={20} />
            </button>
          </div>
          
          <Command.List className="flex-1 overflow-y-auto p-4 scrollbar-hide">
            <Command.Empty className="py-20 text-center space-y-4">
              <div className="w-16 h-16 rounded-full bg-elevated/50 mx-auto flex items-center justify-center text-text-muted opacity-20">
                <Search size={32} />
              </div>
              <div className="text-[10px] font-black text-text-muted uppercase tracking-[0.2em]">Node identifier not recognized.</div>
            </Command.Empty>
            
            {["Primary", "Intelligence", "Execution", "Analytics", "System"].map(cluster => (
              <Command.Group 
                key={cluster} 
                heading={cluster}
                className="px-2 py-4 first:pt-0"
              >
                {NAV_ITEMS.filter(item => item.cluster === cluster).map((item) => (
                  <Command.Item
                    key={item.href}
                    value={item.name + " " + item.keywords}
                    onSelect={() => onSelect(item.href)}
                    className="flex items-center gap-4 px-4 py-4 rounded-2xl cursor-pointer hover:bg-primary/10 transition-all aria-selected:bg-primary/10 aria-selected:text-primary group mt-1"
                  >
                    <div className="w-10 h-10 rounded-xl bg-elevated/50 flex items-center justify-center text-text-muted group-aria-selected:text-primary group-aria-selected:bg-primary/20 group-aria-selected:shadow-[0_0_20px_rgba(96,165,250,0.3)] transition-all shrink-0">
                      <item.icon className="w-5 h-5" />
                    </div>
                    <div className="flex flex-col flex-1 min-w-0">
                      <span className="text-sm font-black tracking-tighter uppercase">{item.name}</span>
                      <span className="text-[9px] text-text-muted font-bold uppercase tracking-widest truncate">{item.keywords}</span>
                    </div>
                    <ArrowRight size={14} className="text-primary opacity-0 group-aria-selected:opacity-100 transition-opacity -translate-x-2 group-aria-selected:translate-x-0" />
                  </Command.Item>
                ))}
              </Command.Group>
            ))}
          </Command.List>
          
          <div className="flex items-center justify-between px-6 py-4 bg-elevated/20 border-t border-border-subtle shrink-0">
            <div className="flex items-center gap-6">
              <div className="flex items-center gap-2">
                <kbd className="px-2 py-1 rounded-lg bg-surface text-[10px] font-black text-text-muted border border-border-subtle shadow-inner">ESC</kbd>
                <span className="text-[9px] font-black text-text-muted uppercase tracking-widest">Close</span>
              </div>
              <div className="flex items-center gap-2">
                <kbd className="px-2 py-1 rounded-lg bg-surface text-[10px] font-black text-text-muted border border-border-subtle shadow-inner">↵</kbd>
                <span className="text-[9px] font-black text-text-muted uppercase tracking-widest">Engage</span>
              </div>
            </div>
            <div className="hidden sm:flex items-center gap-2 text-[9px] font-black text-primary/50 uppercase tracking-widest">
              <Zap size={10} /> Handshake Terminal US-01
            </div>
          </div>
        </Command>
      </DialogContent>
    </Dialog>
  );
}
