import { AuditLogEntry } from '@/lib/types';
import { subHours, subMinutes } from 'date-fns';

export const mockAuditLogs: AuditLogEntry[] = [
  { 
    id: 'log-1', 
    timestamp: subMinutes(new Date(), 5).toISOString(), 
    action: 'API Connection Established', 
    target: 'Binance API 01', 
    userId: 'u-12345', 
    status: 'Success', 
    node: 'AF-NODE-US-01' 
  },
  { 
    id: 'log-2', 
    timestamp: subHours(new Date(), 2).toISOString(), 
    action: 'Global Risk Calibrated', 
    target: 'Risk Engine', 
    userId: 'u-12345', 
    status: 'Success', 
    node: 'AF-NODE-US-01' 
  },
  { 
    id: 'log-3', 
    timestamp: subHours(new Date(), 3).toISOString(), 
    action: '2FA Validation', 
    target: 'Security Protocol', 
    userId: 'u-12345', 
    status: 'Authorized', 
    node: 'AF-NODE-US-01' 
  },
  { 
    id: 'log-4', 
    timestamp: subHours(new Date(), 4).toISOString(), 
    action: 'Node Session Initiated', 
    target: 'Terminal AF-01', 
    userId: 'u-12345', 
    status: 'Success', 
    node: 'AF-NODE-US-01' 
  }
];
