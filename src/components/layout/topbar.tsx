'use client';

import { useEffect, useState } from 'react';
import { Search, Bell, User, Loader2, LogIn, ChevronDown, Activity } from "lucide-react";
import { 
  DropdownMenu, 
  DropdownMenuContent, 
  DropdownMenuItem, 
  DropdownMenuTrigger,
  DropdownMenuLabel,
  DropdownMenuSeparator
} from "@/components/ui/dropdown-menu";
import { useUser } from "@/firebase";
import { useAuth } from "@/firebase";
import { signOut } from "firebase/auth";
import { Button } from "@/components/ui/button";
import { Notification } from "@/lib/types";
import { cn } from "@/lib/utils";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { usePathname } from "next/navigation";

const MOCK_NOTIFICATIONS: Notification[] = [
  { id: 'n-1', userId: 'mock-user-001', type: 'signal', title: 'BTCUSDT Long Signal Triggered', message: 'Momentum Breakout node: 92% confidence breakout on 4H cluster.', read: false, critical: false, createdAt: new Date().toISOString() },
  { id: 'n-2', userId: 'mock-user-001', type: 'trade', title: 'Position Established — SOLUSDT', message: 'Institutional LONG position confirmed at 142.30 entry.', read: false, critical: false, createdAt: new Date(Date.now() - 1800000).toISOString() },
  { id: 'n-3', userId: 'mock-user-001', type: 'system', title: 'Node Sync Initialized', message: 'Institutional handshake established with AF-NODE-US-01.', read: true, critical: false, createdAt: new Date(Date.now() - 3600000).toISOString() },
  { id: 'n-4', userId: 'mock-user-001', type: 'risk', title: 'Risk Threshold Advisory', message: 'Portfolio margin utilization reached 14.5%. Review cluster exposure.', read: false, critical: true, createdAt: new Date(Date.now() - 7200000).toISOString() },
];

export function Topbar() {
  const { user, isUserLoading } = useUser();
  const auth = useAuth();
  const pathname = usePathname();
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [isLoggingOut, setIsLoggingOut] = useState(false);

  useEffect(() => {
    // Mock mode: load mock notifications
    setNotifications(MOCK_NOTIFICATIONS);
  }, []);

  const unreadCount = notifications.filter(n => !n.read).length;

  const pageTitle = pathname === '/' ? 'Terminal Home' : 
                    pathname.split('/').filter(Boolean).pop()?.replace(/-/g, ' ').replace(/\b\w/g, c => c.toUpperCase()) || 'Dashboard';

  // Handle logout
  const handleLogout = async () => {
    setIsLoggingOut(true);
    try {
      await signOut(auth);
    } catch (error) {
      console.error("Logout failed:", error);
    } finally {
      setIsLoggingOut(false);
    }
  }

  return (
    <header className="h-14 border-b border-border-subtle bg-surface/80 backdrop-blur-xl flex items-center justify-between px-6 z-40 sticky top-0 shrink-0 select-none">
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2">
          <Activity size={14} className="text-primary animate-pulse" />
          <h2 className="text-xs font-black uppercase tracking-widest text-text-primary hidden sm:block whitespace-nowrap">
            {pageTitle}
          </h2>
        </div>
        <div className="h-4 w-px bg-border-subtle hidden sm:block" />
        <button 
          onClick={() => window.dispatchEvent(new KeyboardEvent('keydown', { key: 'k', metaKey: true }))}
          className="flex items-center gap-3 px-4 py-1.5 rounded-xl bg-elevated/40 border border-border-subtle text-text-muted hover:text-text-primary hover:border-primary/30 transition-all text-[10px] font-black uppercase tracking-widest group"
        >
          <Search size={14} className="group-hover:text-primary transition-colors" />
          <span className="hidden lg:inline">Traverse Nodes</span>
          <kbd className="hidden lg:inline-flex items-center gap-1 px-1.5 py-0.5 rounded-lg bg-surface border border-border-subtle text-[9px] font-black shadow-inner">
            ⌘K
          </kbd>
        </button>
      </div>

      <div className="flex items-center gap-4">
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button className="relative p-2 text-text-secondary hover:text-text-primary transition-all rounded-xl hover:bg-elevated/50 group">
              <Bell size={18} className="group-hover:rotate-12 transition-transform" />
              {unreadCount > 0 && (
                <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-red rounded-full border-2 border-surface shadow-[0_0_8px_rgba(248,113,113,0.6)]" />
              )}
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-80 glass p-0 overflow-hidden shadow-2xl border-border-subtle mt-2">
            <DropdownMenuLabel className="p-4 text-[10px] font-black uppercase tracking-widest text-text-muted border-b border-border-subtle bg-elevated/20">
              Intelligence Node Feed
            </DropdownMenuLabel>
            <div className="max-h-80 overflow-y-auto scrollbar-hide">
              {notifications?.length === 0 ? (
                <div className="p-10 text-center space-y-2 opacity-40">
                  <Bell className="w-8 h-8 text-text-muted mx-auto" />
                  <div className="text-[9px] font-black text-text-muted uppercase tracking-widest">Scanning frequency...</div>
                </div>
              ) : (
                notifications?.map(n => (
                  <div key={n.id} className={cn(
                    "p-4 border-b border-border-subtle hover:bg-elevated/50 transition-colors cursor-pointer group relative",
                    !n.read && "bg-primary/5"
                  )}>
                    {!n.read && <div className="absolute left-0 top-0 bottom-0 w-1 bg-primary shadow-[0_0_8px_rgba(96,165,250,0.5)]" />}
                    <div className="flex items-start gap-3">
                      <div className={cn(
                        "w-1.5 h-1.5 rounded-full mt-1.5 shrink-0",
                        n.critical ? "bg-red shadow-[0_0_8px_rgba(248,113,113,0.5)]" : "bg-primary shadow-[0_0_8px_rgba(96,165,250,0.5)]"
                      )} />
                      <div className="flex-1 min-w-0">
                        <div className="text-[11px] font-black uppercase leading-tight mb-1 group-hover:text-primary transition-colors truncate">{n.title}</div>
                        <div className="text-[10px] text-text-muted font-medium leading-relaxed line-clamp-2 uppercase">{n.message}</div>
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </DropdownMenuContent>
        </DropdownMenu>

        <div className="h-4 w-px bg-border-subtle" />

        {!user ? (
          // Mock mode: user is always connected, this block never renders
          <Button 
            disabled={isUserLoading}
            variant="outline" 
            size="sm" 
            className="h-9 border-primary/40 text-primary hover:bg-primary/10 px-5 font-black uppercase text-[10px] tracking-widest rounded-xl transition-all shadow-[0_0_15px_rgba(96,165,250,0.1)]"
          >
            {isUserLoading ? <Loader2 className="animate-spin" size={12} /> : <LogIn size={12} />}
            <span className="hidden sm:inline ml-2">Establish Sync</span>
          </Button>
        ) : (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <button className="flex items-center gap-3 group px-2 py-1 rounded-xl hover:bg-elevated/50 transition-all border border-transparent hover:border-border-subtle">
                <Avatar className="w-8 h-8 border border-border-subtle shadow-inner">
                  <AvatarFallback className="bg-primary/20 text-primary text-[10px] font-black uppercase">
                    {user.email?.[0]?.toUpperCase() || 'AF'}
                  </AvatarFallback>
                </Avatar>
                <div className="hidden lg:flex flex-col items-start text-left">
                  <span className="text-[10px] font-black uppercase text-text-primary tracking-tight truncate w-24">{user.email?.split('@')[0]}</span>
                  <span className="text-[8px] font-bold uppercase text-text-muted">Verified Node</span>
                </div>
                <ChevronDown size={14} className="text-text-muted group-hover:text-primary transition-colors" />
              </button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-60 glass border-border-subtle mt-2 shadow-2xl p-1">
              <DropdownMenuLabel className="text-[10px] font-black uppercase text-text-muted px-3 py-2">Node Identity</DropdownMenuLabel>
              <DropdownMenuSeparator className="bg-border-subtle" />
              <DropdownMenuItem className="text-[11px] font-black uppercase cursor-pointer rounded-lg px-3 py-2.5 hover:bg-primary/10 focus:bg-primary/10 focus:text-primary group">
                <User size={14} className="mr-3 text-text-muted group-hover:text-primary" /> Profile Settings
              </DropdownMenuItem>
              <DropdownMenuItem className="text-[11px] font-black uppercase cursor-pointer rounded-lg px-3 py-2.5 hover:bg-primary/10 focus:bg-primary/10 focus:text-primary group">
                <Activity size={14} className="mr-3 text-text-muted group-hover:text-primary" /> API Management
              </DropdownMenuItem>
              <DropdownMenuSeparator className="bg-border-subtle" />
              <DropdownMenuItem 
                onClick={handleLogout}
                disabled={isLoggingOut}
                className="text-red focus:bg-red/10 focus:text-red text-[11px] font-black uppercase cursor-pointer rounded-lg px-3 py-2.5 disabled:opacity-50"
              >
                {isLoggingOut ? 'Terminating...' : 'Terminate Node session'}
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        )}
      </div>
    </header>
  );
}
