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

export function Topbar() {
  const auth = useAuth();
  const db = useFirestore();
  const { user, isUserLoading } = useUser();

  // Real-time notification stream
  const notificationsQuery = useMemoFirebase(() => {
    if (!user || !db) return null;
    return query(collection(db, 'users', user.uid, 'notifications'), orderBy('createdAt', 'desc'), limit(5));
  }, [user, db]);

  const { data: notifications } = useCollection<Notification>(notificationsQuery);
  const unreadCount = notifications?.filter(n => !n.read).length || 0;

  function handleConnect() {
    if (auth) {
      initiateAnonymousSignIn(auth);
    }
  }

  return (
    <header className="h-16 border-b border-border-subtle bg-surface/80 backdrop-blur-xl flex items-center justify-between px-8 z-40 sticky top-0">
      <div className="flex items-center gap-6">
        <div className="relative group max-w-lg w-64 md:w-96">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-text-muted w-4 h-4 group-focus-within:text-primary transition-colors" />
          <input 
            type="text" 
            placeholder="Search signals, assets, strategies... (⌘K)" 
            className="w-full bg-elevated/40 border border-border-subtle rounded-xl py-2 pl-12 pr-4 text-[13px] font-medium focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all placeholder:text-text-muted/50"
          />
        </div>
      </div>

      <div className="flex items-center gap-6">
        {/* Notifications Dropdown */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button className="relative p-2.5 text-text-secondary hover:text-text-primary transition-all rounded-xl hover:bg-elevated/50">
              <Bell className="w-5 h-5" />
              {unreadCount > 0 && (
                <span className="absolute top-2.5 right-2.5 w-2 h-2 bg-red rounded-full border-2 border-surface animate-pulse" />
              )}
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-96 glass p-0 overflow-hidden shadow-2xl border-border-subtle">
            <DropdownMenuLabel className="p-5 text-[10px] font-black uppercase tracking-widest text-text-muted border-b border-border-subtle bg-elevated/20">
              System Alerts & Intelligence
            </DropdownMenuLabel>
            <div className="max-h-[450px] overflow-y-auto">
              {notifications?.length === 0 ? (
                <div className="p-12 text-center">
                  <Bell className="w-8 h-8 text-text-muted/20 mx-auto mb-3" />
                  <div className="text-[10px] font-black text-text-muted uppercase tracking-widest">Scanning active frequency...</div>
                </div>
              ) : (
                notifications?.map(n => (
                  <div key={n.id} className={cn(
                    "p-5 border-b border-border-subtle hover:bg-elevated/50 transition-colors cursor-pointer group",
                    !n.read && "bg-primary/5"
                  )}>
                    <div className="flex items-start gap-4">
                      <div className={cn(
                        "w-2 h-2 rounded-full mt-1.5 shrink-0",
                        n.critical ? "bg-red shadow-[0_0_8px_rgba(248,113,113,0.5)]" : "bg-primary shadow-[0_0_8px_rgba(96,165,250,0.5)]"
                      )} />
                      <div className="flex-1">
                        <div className="text-xs font-black leading-tight mb-1 group-hover:text-primary transition-colors">{n.title}</div>
                        <div className="text-[11px] text-text-muted leading-relaxed line-clamp-2">{n.message}</div>
                        <div className="text-[9px] text-text-muted/60 mt-2 font-mono uppercase tracking-tighter">
                          {new Date(n.createdAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </div>
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
            <div className="p-3 bg-elevated/40 text-center border-t border-border-subtle">
              <Button variant="ghost" className="w-full h-10 text-[10px] font-black uppercase tracking-widest hover:bg-primary/10 hover:text-primary">Archived Feed</Button>
            </div>
          </DropdownMenuContent>
        </DropdownMenu>

        {/* User Session Interface */}
        {!user ? (
          <Button 
            onClick={handleConnect} 
            disabled={isUserLoading}
            variant="outline" 
            size="sm" 
            className="gap-2 border-primary/40 text-primary hover:bg-primary/10 h-10 px-5 font-black uppercase text-[10px] tracking-widest rounded-xl transition-all shadow-inner"
          >
            {isUserLoading ? <Loader2 className="animate-spin" size={14} /> : <LogIn size={14} />}
            Connect Terminal
          </Button>
        ) : (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <button className="flex items-center gap-3 pl-4 border-l border-border-subtle group">
                <Avatar className="w-9 h-9 border border-border-subtle group-hover:border-primary/50 transition-colors">
                  <AvatarFallback className="bg-elevated/80 text-text-primary text-[10px] font-black uppercase">
                    {user.email?.[0]?.toUpperCase() || 'U'}
                  </AvatarFallback>
                </Avatar>
                <div className="hidden md:block text-left">
                  <div className="text-[11px] font-black leading-none uppercase tracking-tight group-hover:text-primary transition-colors">{user.displayName || 'Authorized Node'}</div>
                  <div className="flex items-center gap-1.5 text-[9px] text-text-muted leading-tight uppercase font-black mt-1">
                    <span className={cn("w-1 h-1 rounded-full", user.isAnonymous ? "bg-amber" : "bg-green")} />
                    {user.isAnonymous ? 'Guest Node' : 'Pro Tier'}
                  </div>
                </div>
                <ChevronDown size={14} className="text-text-muted group-hover:text-primary transition-colors ml-1" />
              </button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-56 glass border-border-subtle mt-1 shadow-2xl">
              <DropdownMenuLabel className="text-[10px] font-black uppercase tracking-widest text-text-muted">Terminal Access</DropdownMenuLabel>
              <DropdownMenuSeparator className="bg-border-subtle" />
              <DropdownMenuItem className="text-[11px] font-bold uppercase tracking-tight cursor-pointer">Profile Configuration</DropdownMenuItem>
              <DropdownMenuItem className="text-[11px] font-bold uppercase tracking-tight cursor-pointer">API Handshake Keys</DropdownMenuItem>
              <DropdownMenuSeparator className="bg-border-subtle" />
              <DropdownMenuItem 
                onClick={() => auth.signOut()}
                className="text-red focus:bg-red/10 focus:text-red text-[11px] font-black uppercase tracking-widest cursor-pointer"
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
