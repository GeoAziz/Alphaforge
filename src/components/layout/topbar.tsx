'use client';

import { Search, Bell, User, Loader2, LogIn, ChevronDown } from "lucide-react";
import { 
  DropdownMenu, 
  DropdownMenuContent, 
  DropdownMenuItem, 
  DropdownMenuTrigger,
  DropdownMenuLabel,
  DropdownMenuSeparator
} from "@/components/ui/dropdown-menu";
import { useAuth, useUser, useFirestore, useCollection, useMemoFirebase } from "@/firebase";
import { initiateAnonymousSignIn } from "@/firebase/non-blocking-login";
import { Button } from "@/components/ui/button";
import { collection, query, orderBy, limit } from "firebase/firestore";
import { Notification } from "@/lib/types";
import { cn } from "@/lib/utils";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { usePathname } from "next/navigation";

export function Topbar() {
  const auth = useAuth();
  const db = useFirestore();
  const pathname = usePathname();
  const { user, isUserLoading } = useUser();

  // Real-time notification stream
  const notificationsQuery = useMemoFirebase(() => {
    if (!user || !db) return null;
    return query(collection(db, 'users', user.uid, 'notifications'), orderBy('createdAt', 'desc'), limit(5));
  }, [user, db]);

  const { data: notifications } = useCollection<Notification>(notificationsQuery);
  const unreadCount = notifications?.filter(n => !n.read).length || 0;

  // Derive page title from pathname
  const pageTitle = pathname === '/' ? 'Dashboard' : 
                    pathname.split('/').pop()?.replace(/-/g, ' ').replace(/\b\w/g, c => c.toUpperCase()) || '';

  function handleConnect() {
    if (auth) {
      initiateAnonymousSignIn(auth);
    }
  }

  return (
    <header className="h-14 md:h-14 border-b border-border-subtle bg-surface/80 backdrop-blur-xl flex items-center justify-between px-6 z-40 sticky top-0 shrink-0">
      <div className="flex items-center gap-4">
        <h2 className="text-sm font-black uppercase tracking-tighter text-text-primary hidden sm:block">
          {pageTitle}
        </h2>
        <div className="h-4 w-px bg-border-subtle hidden sm:block" />
        <button 
          onClick={() => window.dispatchEvent(new KeyboardEvent('keydown', { key: 'k', metaKey: true }))}
          className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-elevated/40 border border-border-subtle text-text-muted hover:text-text-primary hover:border-primary/30 transition-all text-[11px] font-medium group"
        >
          <Search size={14} className="group-hover:text-primary transition-colors" />
          <span className="hidden lg:inline">Search nodes...</span>
          <kbd className="hidden lg:inline-flex items-center gap-1 px-1.5 py-0.5 rounded bg-surface border border-border-subtle text-[9px] font-black">
            ⌘K
          </kbd>
        </button>
      </div>

      <div className="flex items-center gap-4">
        {/* Notifications Dropdown */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button className="relative p-2 text-text-secondary hover:text-text-primary transition-all rounded-lg hover:bg-elevated/50">
              <Bell size={18} />
              {unreadCount > 0 && (
                <span className="absolute top-1.5 right-1.5 w-1.5 h-1.5 bg-red rounded-full border-2 border-surface animate-pulse" />
              )}
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-80 glass p-0 overflow-hidden shadow-2xl border-border-subtle">
            <DropdownMenuLabel className="p-4 text-[10px] font-black uppercase tracking-widest text-text-muted border-b border-border-subtle bg-elevated/20">
              System Intelligence
            </DropdownMenuLabel>
            <div className="max-h-80 overflow-y-auto">
              {notifications?.length === 0 ? (
                <div className="p-8 text-center">
                  <Bell className="w-6 h-6 text-text-muted/20 mx-auto mb-2" />
                  <div className="text-[10px] font-black text-text-muted uppercase tracking-widest">Scanning frequency...</div>
                </div>
              ) : (
                notifications?.map(n => (
                  <div key={n.id} className={cn(
                    "p-4 border-b border-border-subtle hover:bg-elevated/50 transition-colors cursor-pointer group",
                    !n.read && "bg-primary/5"
                  )}>
                    <div className="flex items-start gap-3">
                      <div className={cn(
                        "w-1.5 h-1.5 rounded-full mt-1.5 shrink-0",
                        n.critical ? "bg-red shadow-[0_0_8px_rgba(248,113,113,0.5)]" : "bg-primary shadow-[0_0_8px_rgba(96,165,250,0.5)]"
                      )} />
                      <div className="flex-1">
                        <div className="text-[11px] font-black leading-tight mb-1 group-hover:text-primary transition-colors">{n.title}</div>
                        <div className="text-[10px] text-text-muted leading-relaxed line-clamp-2">{n.message}</div>
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </DropdownMenuContent>
        </DropdownMenu>

        <div className="h-4 w-px bg-border-subtle" />

        {/* User Session */}
        {!user ? (
          <Button 
            onClick={handleConnect} 
            disabled={isUserLoading}
            variant="outline" 
            size="sm" 
            className="h-8 border-primary/40 text-primary hover:bg-primary/10 px-4 font-black uppercase text-[10px] tracking-widest rounded-lg transition-all"
          >
            {isUserLoading ? <Loader2 className="animate-spin" size={12} /> : <LogIn size={12} />}
            <span className="hidden sm:inline ml-2">Connect Node</span>
          </Button>
        ) : (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <button className="flex items-center gap-2 group">
                <Avatar className="w-8 h-8 border border-border-subtle group-hover:border-primary/50 transition-colors">
                  <AvatarFallback className="bg-elevated/80 text-text-primary text-[10px] font-black uppercase">
                    {user.email?.[0]?.toUpperCase() || 'U'}
                  </AvatarFallback>
                </Avatar>
                <ChevronDown size={14} className="text-text-muted group-hover:text-primary transition-colors" />
              </button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-56 glass border-border-subtle mt-1">
              <DropdownMenuLabel className="text-[10px] font-black uppercase text-text-muted">Node Identity</DropdownMenuLabel>
              <DropdownMenuSeparator className="bg-border-subtle" />
              <DropdownMenuItem className="text-[11px] font-bold uppercase cursor-pointer">Profile Settings</DropdownMenuItem>
              <DropdownMenuItem className="text-[11px] font-bold uppercase cursor-pointer">API Management</DropdownMenuItem>
              <DropdownMenuSeparator className="bg-border-subtle" />
              <DropdownMenuItem 
                onClick={() => auth.signOut()}
                className="text-red focus:bg-red/10 focus:text-red text-[11px] font-black uppercase cursor-pointer"
              >
                Terminate Session
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        )}
      </div>
    </header>
  );
}