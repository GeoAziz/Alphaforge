'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { LayoutDashboard, Zap, BarChart3, Wallet, TrendingUp, Menu } from 'lucide-react';
import { cn } from '@/lib/utils';
import { 
  DropdownMenu, 
  DropdownMenuContent, 
  DropdownMenuItem, 
  DropdownMenuTrigger 
} from '@/components/ui/dropdown-menu';

const mobileNavItems = [
  { name: "Home", href: "/", icon: LayoutDashboard },
  { name: "Alpha", href: "/signals", icon: Zap },
  { name: "Intel", href: "/market-intelligence", icon: BarChart3 },
  { name: "Assets", href: "/portfolio", icon: Wallet },
];

const overflowItems = [
  { name: "Analytics", href: "/analytics", icon: TrendingUp },
  { name: "Strategies", href: "/strategies", icon: Menu },
];

export function MobileNav() {
  const pathname = usePathname();

  return (
    <nav className="lg:hidden fixed bottom-0 left-0 right-0 h-16 bg-surface/90 backdrop-blur-2xl border-t border-border-subtle px-6 flex items-center justify-between z-[60] pb-safe shadow-[0_-10px_40px_rgba(0,0,0,0.5)]">
      {mobileNavItems.map((item) => {
        const isActive = pathname === item.href;
        return (
          <Link 
            key={item.name} 
            href={item.href}
            className={cn(
              "flex flex-col items-center gap-1.5 transition-all duration-300 relative px-2 touch-target",
              isActive ? "text-primary scale-110" : "text-text-muted hover:text-text-secondary"
            )}
          >
            {isActive && <div className="absolute -top-[18px] w-8 h-1 bg-primary rounded-full shadow-[0_0_15px_rgba(96,165,250,0.8)]" />}
            <item.icon size={20} className={cn(isActive && "drop-shadow-[0_0_8px_rgba(96,165,250,0.4)]")} />
            <span className="text-[9px] font-black uppercase tracking-tighter">{item.name}</span>
          </Link>
        );
      })}

      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <button className="flex flex-col items-center gap-1.5 text-text-muted px-2 touch-target">
            <Menu size={20} />
            <span className="text-[9px] font-black uppercase tracking-tighter">More</span>
          </button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end" side="top" className="glass border-border-subtle mb-4 w-40 p-1">
          {overflowItems.map(item => (
            <DropdownMenuItem key={item.name} asChild className="rounded-lg p-3 focus:bg-primary/10 focus:text-primary min-h-[44px]">
              <Link href={item.href} className="flex items-center gap-3 w-full">
                <item.icon size={16} />
                <span className="text-[10px] font-black uppercase tracking-widest">{item.name}</span>
              </Link>
            </DropdownMenuItem>
          ))}
        </DropdownMenuContent>
      </DropdownMenu>
    </nav>
  );
}
