"use client";

import { useEffect } from "react";
import { 
  LayoutDashboard, Zap, BarChart3, Wallet, Target, 
  FlaskConical, Store, TrendingUp, Settings, ChevronLeft, ChevronRight, Activity, ShieldCheck, UserCircle, Menu
} from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { 
  Sidebar, 
  SidebarContent, 
  SidebarFooter, 
  SidebarGroup, 
  SidebarGroupContent, 
  SidebarGroupLabel, 
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  useSidebar
} from "@/components/ui/sidebar";
import { Button } from "@/components/ui/button";
import { useUser } from "@/firebase";

const navItems = [
  { name: "Dashboard", href: "/", icon: LayoutDashboard },
  { name: "Signals", href: "/signals", icon: Zap },
  { name: "Market Intel", href: "/market-intelligence", icon: BarChart3 },
  { name: "Portfolio", href: "/portfolio", icon: Wallet },
  { name: "Strategies", href: "/strategies", icon: Target },
  { name: "Backtesting", href: "/backtesting", icon: FlaskConical },
  { name: "Marketplace", href: "/marketplace", icon: Store },
  { name: "Analytics", href: "/analytics", icon: TrendingUp },
];

const advancedItems = [
  { name: "Proof Center", href: "/proofs", icon: ShieldCheck },
  { name: "Creator Portal", href: "/creator/verification", icon: UserCircle },
];

/**
 * AppSidebar
 * 
 * Accessibility:
 * - Landmark: nav
 * - aria-label: Main Navigation
 */
export function AppSidebar() {
  const pathname = usePathname();
  const { user } = useUser();
  const { toggleSidebar, state, setOpen } = useSidebar();
  const isCollapsed = state === "collapsed";

  // Force collapse on mid-sized screens (Laptop breakpoint)
  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth >= 1024 && window.innerWidth < 1280) {
        setOpen(false);
      } else if (window.innerWidth >= 1280) {
        setOpen(true);
      }
    };

    window.addEventListener('resize', handleResize);
    handleResize(); // Initial check
    return () => window.removeEventListener('resize', handleResize);
  }, [setOpen]);

  return (
    <Sidebar collapsible="icon" className="hidden lg:flex border-r border-border-subtle bg-surface z-50">
      <SidebarHeader className="p-4 flex flex-row items-center justify-between">
        <div className={cn("flex items-center gap-3", isCollapsed && "justify-center w-full")}>
          <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center font-bold text-primary-foreground shadow-[0_0_15px_rgba(96,165,250,0.4)] shrink-0">
            AF
          </div>
          {!isCollapsed && <span className="font-black text-lg tracking-tighter uppercase">AlphaForge</span>}
        </div>
      </SidebarHeader>

      <SidebarContent className="scrollbar-hide" role="navigation" aria-label="Main Navigation">
        <SidebarGroup>
          <SidebarMenu>
            {navItems.map((item) => {
              const isActive = pathname === item.href;
              return (
                <SidebarMenuItem key={item.name}>
                  <SidebarMenuButton 
                    asChild 
                    isActive={isActive}
                    tooltip={item.name}
                    className={cn(
                      "transition-all duration-200 h-10 px-3",
                      isActive 
                        ? "text-primary bg-primary/10 border-r-2 border-primary rounded-none" 
                        : "text-text-secondary hover:bg-elevated"
                    )}
                  >
                    <Link href={item.href}>
                      <item.icon className={cn("w-5 h-5", isActive && "text-primary")} />
                      <span className="font-bold uppercase text-[10px] tracking-widest">{item.name}</span>
                    </Link>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              );
            })}
          </SidebarMenu>
        </SidebarGroup>

        {!isCollapsed && (
          <SidebarGroup>
            <SidebarGroupLabel className="text-[9px] font-black uppercase px-4 py-4 text-text-muted tracking-widest">Verification Node</SidebarGroupLabel>
            <SidebarMenu>
              {advancedItems.map((item) => {
                const isActive = pathname === item.href || pathname.startsWith(item.href + '/');
                return (
                  <SidebarMenuItem key={item.name}>
                    <SidebarMenuButton 
                      asChild 
                      isActive={isActive}
                      tooltip={item.name}
                      className={cn(
                        "transition-all duration-200 h-10 px-3",
                        isActive 
                          ? "text-primary bg-primary/10 border-r-2 border-primary rounded-none" 
                          : "text-text-secondary hover:bg-elevated"
                      )}
                    >
                      <Link href={item.href}>
                        <item.icon className={cn("w-5 h-5", isActive && "text-primary")} />
                        <span className="font-bold uppercase text-[10px] tracking-widest">{item.name}</span>
                      </Link>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                );
              })}
            </SidebarMenu>
          </SidebarGroup>
        )}
      </SidebarContent>

      <SidebarFooter className="p-4 space-y-4">
        {!isCollapsed && user && (
          <div className="p-3 rounded-xl bg-elevated/50 border border-border-subtle space-y-2 animate-in fade-in zoom-in-95 duration-500">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-black uppercase text-text-muted tracking-tighter">Node Status</span>
              <div className="w-1.5 h-1.5 rounded-full bg-green animate-pulse shadow-[0_0_8px_rgba(52,211,153,0.5)]" aria-label="Online" />
            </div>
            <div className="flex items-center gap-2">
              <Activity size={12} className="text-primary" />
              <span className="text-[9px] font-black text-text-primary uppercase tracking-tighter">Institutional Sync</span>
            </div>
          </div>
        )}
        
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton 
              asChild 
              isActive={pathname === "/settings"}
              className="text-text-secondary h-10 px-3"
              tooltip="Settings"
            >
              <Link href="/settings">
                <Settings className="w-5 h-5" />
                <span className="font-bold uppercase text-[10px] tracking-widest">Settings</span>
              </Link>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
        
        <Button 
          variant="ghost" 
          size="icon" 
          onClick={toggleSidebar}
          className="w-full justify-center text-text-muted hover:text-text-primary hover:bg-elevated rounded-xl h-10 touch-target focus-visible:ring-2 focus-visible:ring-primary"
          aria-label={isCollapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          {isCollapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
        </Button>
      </SidebarFooter>
    </Sidebar>
  );
}
