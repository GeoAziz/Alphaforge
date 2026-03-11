"use client";

import { 
  LayoutDashboard, Zap, BarChart3, Wallet, Target, 
  FlaskConical, Store, TrendingUp, Settings, ChevronLeft, ChevronRight, Activity
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

export function AppSidebar() {
  const pathname = usePathname();
  const { user } = useUser();
  const { toggleSidebar, state } = useSidebar();
  const isCollapsed = state === "collapsed";

  return (
    <Sidebar collapsible="icon" className="border-r border-border-subtle bg-surface">
      <SidebarHeader className="p-4 flex flex-row items-center justify-between">
        <div className={cn("flex items-center gap-2", isCollapsed && "justify-center w-full")}>
          <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center font-bold text-primary-foreground shadow-[0_0_15px_rgba(96,165,250,0.4)]">
            AF
          </div>
          {!isCollapsed && <span className="font-bold text-lg tracking-tight">AlphaForge</span>}
        </div>
      </SidebarHeader>

      <SidebarContent>
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
                      "transition-all duration-200",
                      isActive ? "text-primary bg-primary/10" : "text-text-secondary hover:bg-elevated"
                    )}
                  >
                    <Link href={item.href}>
                      <item.icon className={cn("w-5 h-5", isActive && "text-primary")} />
                      <span>{item.name}</span>
                    </Link>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              );
            })}
          </SidebarMenu>
        </SidebarGroup>
      </SidebarContent>

      <SidebarFooter className="p-4 space-y-4">
        {!isCollapsed && user && (
          <div className="p-3 rounded-xl bg-elevated/50 border border-border-subtle space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-black uppercase text-text-muted">Node Status</span>
              <div className="w-1.5 h-1.5 rounded-full bg-green animate-pulse" />
            </div>
            <div className="flex items-center gap-2">
              <Activity size={12} className="text-primary" />
              <span className="text-[10px] font-bold text-text-primary uppercase tracking-tighter">Syncing Institutional Core</span>
            </div>
          </div>
        )}
        
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton 
              asChild 
              isActive={pathname === "/settings"}
              className="text-text-secondary"
            >
              <Link href="/settings">
                <Settings className="w-5 h-5" />
                <span>Settings</span>
              </Link>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
        <Button 
          variant="ghost" 
          size="icon" 
          onClick={toggleSidebar}
          className="w-full justify-center text-text-muted hover:text-text-primary"
        >
          {isCollapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
        </Button>
      </SidebarFooter>
    </Sidebar>
  );
}