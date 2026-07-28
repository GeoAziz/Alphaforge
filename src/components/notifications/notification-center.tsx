'use client';

import React, { useState, useEffect } from 'react';
import { Bell, AlertCircle, CheckCircle, TrendingUp, XCircle, Zap } from 'lucide-react';
import { cn } from '@/lib/utils';

interface Notification {
  id: string;
  type: 'signal' | 'trade' | 'risk' | 'info' | 'alert';
  title: string;
  message: string;
  timestamp: string;
  read: boolean;
  action?: { label: string; href: string };
}

interface NotificationCenterProps {
  notifications?: Notification[];
  onMarkRead?: (id: string) => void;
  className?: string;
}

export function NotificationCenter({
  notifications = [],
  onMarkRead,
  className = '',
}: NotificationCenterProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [items, setItems] = useState<Notification[]>(notifications);

  useEffect(() => {
    setItems(notifications);
  }, [notifications]);

  const unreadCount = items.filter((n) => !n.read).length;

  const getIcon = (type: string) => {
    switch (type) {
      case 'signal':
        return <Zap size={16} className="text-yellow-500" />;
      case 'trade':
        return <TrendingUp size={16} className="text-blue-500" />;
      case 'risk':
        return <AlertCircle size={16} className="text-red-500" />;
      case 'info':
        return <CheckCircle size={16} className="text-green-500" />;
      default:
        return <Bell size={16} className="text-neutral-500" />;
    }
  };

  const getBackgroundColor = (type: string) => {
    switch (type) {
      case 'signal':
        return 'bg-yellow-500/10 border-yellow-500/20';
      case 'trade':
        return 'bg-blue-500/10 border-blue-500/20';
      case 'risk':
        return 'bg-red-500/10 border-red-500/20';
      case 'info':
        return 'bg-green-500/10 border-green-500/20';
      default:
        return 'bg-neutral-800/50 border-neutral-700';
    }
  };

  return (
    <div className={cn('relative', className)}>
      {/* Bell Icon with Badge */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="relative p-2 hover:bg-neutral-800 rounded-lg transition-colors"
      >
        <Bell size={20} className="text-neutral-400" />
        {unreadCount > 0 && (
          <span className="absolute top-1 right-1 inline-flex items-center justify-center w-5 h-5 text-xs font-bold text-white bg-red-500 rounded-full">
            {unreadCount}
          </span>
        )}
      </button>

      {/* Notification Dropdown */}
      {isOpen && (
        <div className="absolute right-0 top-12 w-96 max-h-[600px] overflow-y-auto bg-neutral-900 border border-neutral-800 rounded-lg shadow-xl z-50">
          {/* Header */}
          <div className="sticky top-0 p-4 border-b border-neutral-800 bg-neutral-900">
            <h3 className="font-bold text-white flex items-center justify-between">
              Notifications
              {unreadCount > 0 && (
                <span className="text-xs font-bold text-red-400">{unreadCount} new</span>
              )}
            </h3>
          </div>

          {/* Notifications List */}
          {items.length > 0 ? (
            <div className="divide-y divide-neutral-800">
              {items.map((notif) => (
                <div
                  key={notif.id}
                  className={cn(
                    'p-4 hover:bg-neutral-800/50 transition-colors cursor-pointer',
                    !notif.read && 'bg-neutral-800/30'
                  )}
                  onClick={() => {
                    if (onMarkRead && !notif.read) {
                      onMarkRead(notif.id);
                    }
                  }}
                >
                  <div className="flex gap-3">
                    {/* Icon */}
                    <div className="shrink-0 mt-1">{getIcon(notif.type)}</div>

                    {/* Content */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between gap-2">
                        <div>
                          <p className="font-semibold text-white text-sm">{notif.title}</p>
                          <p className="text-neutral-400 text-xs mt-1">{notif.message}</p>
                        </div>
                        {!notif.read && (
                          <div className="shrink-0 w-2 h-2 rounded-full bg-blue-500 mt-1" />
                        )}
                      </div>

                      {/* Timestamp and Action */}
                      <div className="flex items-center justify-between mt-2">
                        <span className="text-xs text-neutral-500">
                          {new Date(notif.timestamp).toLocaleTimeString([], {
                            hour: '2-digit',
                            minute: '2-digit',
                          })}
                        </span>
                        {notif.action && (
                          <a
                            href={notif.action.href}
                            className="text-xs font-semibold text-blue-400 hover:text-blue-300"
                            onClick={(e) => e.stopPropagation()}
                          >
                            {notif.action.label} →
                          </a>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-neutral-400">
              <Bell size={32} className="mx-auto mb-2 opacity-50" />
              <p>No notifications</p>
            </div>
          )}

          {/* Footer */}
          {items.length > 0 && (
            <div className="p-3 border-t border-neutral-800 text-center">
              <button className="text-xs font-semibold text-blue-400 hover:text-blue-300">
                View All Notifications
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
