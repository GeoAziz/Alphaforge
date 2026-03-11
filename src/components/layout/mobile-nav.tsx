'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { LayoutDashboard, Zap, BarChart3, Wallet, TrendingUp } from 'lucide-react';
import { cn } from '@/lib/utils';

const mobileNavItems = [
  { name: "Home", href: "/", icon: LayoutDashboard },
  { name: "Signals", href: "/signals", icon: Zap },
  { name: "Intel", href: "/market-intelligence", icon: BarChart3 },
  { name: "Portfolio", href: "/portfolio", icon: Wallet },
  { name: "Analytics", href: "/analytics", icon: TrendingUp },
];

export function MobileNav() {
  const pathname = usePathname();

  return (
    <nav className="md:hidden fixed bottom-0 left-0 right-0 h-16 bg-surface/80 backdrop-blur-xl border-t border-border-subtle px-6 flex items-center justify-between z-50">
      {mobileNavItems.map((item) => {
        const isActive = pathname === item.href;
        return (
          <Link 
            key={item.name} 
            href={item.href}
            className={cn(
              "flex flex-col items-center gap-1 transition-colors",
              isActive ? "text-primary" : "text-text-muted"
            )}
          >
            <item.icon size={20} className={cn(isActive && "text-primary")} />
            <span className="text-[9px] font-black uppercase tracking-tighter">{item.name}</span>
          </Link>
        );
      })}
    </nav>
  );
}