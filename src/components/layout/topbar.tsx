"use client";

import { Search, Bell, User } from "lucide-react";
import { 
  DropdownMenu, 
  DropdownMenuContent, 
  DropdownMenuItem, 
  DropdownMenuTrigger 
} from "@/components/ui/dropdown-menu";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";

export function Topbar() {
  return (
    <header className="h-14 border-b border-border-subtle bg-surface flex items-center justify-between px-6 z-30">
      <div className="flex items-center gap-4">
        <div className="relative group max-w-md w-64 md:w-96">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted w-4 h-4" />
          <input 
            type="text" 
            placeholder="Search signals, assets, strategies... (⌘K)" 
            className="w-full bg-elevated/50 border border-border-subtle rounded-lg py-1.5 pl-10 pr-4 text-sm focus:outline-none focus:ring-1 focus:ring-primary/50"
          />
        </div>
      </div>

      <div className="flex items-center gap-4">
        <button className="relative p-2 text-text-secondary hover:text-text-primary transition-colors">
          <Bell className="w-5 h-5" />
          <span className="absolute top-2 right-2 w-2 h-2 bg-red rounded-full border border-surface" />
        </button>

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button className="flex items-center gap-2 pl-2 border-l border-border-subtle">
              <Avatar className="w-8 h-8 border border-border-subtle">
                <AvatarFallback className="bg-elevated text-text-primary text-xs">JD</AvatarFallback>
              </Avatar>
              <div className="hidden md:block text-left">
                <div className="text-xs font-bold leading-none">John Doe</div>
                <div className="text-[10px] text-text-muted leading-tight uppercase font-black">Pro Plan</div>
              </div>
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-48 glass">
            <DropdownMenuItem>Profile Settings</DropdownMenuItem>
            <DropdownMenuItem>Subscription Management</DropdownMenuItem>
            <DropdownMenuItem className="text-red">Sign Out</DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  );
}
