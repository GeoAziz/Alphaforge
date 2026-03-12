
'use client';

import { useState, useEffect } from 'react';
import { AuditLogEntry } from '@/lib/types';
import { api } from '@/lib/api';

/**
 * useAuditLog - Fetches and manages terminal audit telemetry.
 */
export function useAuditLog(userId: string) {
  const [logs, setLogs] = useState<AuditLogEntry[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (!userId) return;

    const fetchLogs = async () => {
      try {
        const data = await api.system.getAuditLogs(userId);
        setLogs(data);
      } catch (e) {
        console.error('Audit log traversal failed');
      } finally {
        setIsLoading(false);
      }
    };

    fetchLogs();
  }, [userId]);

  return { logs, isLoading };
}
