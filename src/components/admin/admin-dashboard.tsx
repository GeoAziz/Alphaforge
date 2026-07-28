'use client';

import React, { useState, useEffect } from 'react';
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { Server, Users, TrendingUp, AlertTriangle, Settings, Activity, Eye, Lock } from 'lucide-react';
import { cn } from '@/lib/utils';

interface SystemHealth {
  database: 'healthy' | 'warning' | 'critical';
  api: 'healthy' | 'warning' | 'critical';
  cache: 'healthy' | 'warning' | 'critical';
  workers: 'healthy' | 'warning' | 'critical';
  uptime_percent: number;
  response_time_ms: number;
}

interface UserStats {
  total_users: number;
  active_users: number;
  new_users_today: number;
  kyc_pending: number;
  kyc_approved: number;
  kyc_rejected: number;
}

interface AdminDashboardProps {
  isAdmin?: boolean;
  className?: string;
}

export function AdminDashboard({ isAdmin = false, className = '' }: AdminDashboardProps) {
  const [systemHealth, setSystemHealth] = useState<SystemHealth>({
    database: 'healthy',
    api: 'healthy',
    cache: 'healthy',
    workers: 'healthy',
    uptime_percent: 99.9,
    response_time_ms: 145,
  });

  const [userStats, setUserStats] = useState<UserStats>({
    total_users: 5432,
    active_users: 1234,
    new_users_today: 45,
    kyc_pending: 123,
    kyc_approved: 4200,
    kyc_rejected: 45,
  });

  const [selectedTab, setSelectedTab] = useState<'overview' | 'users' | 'system' | 'settings'>('overview');

  if (!isAdmin) {
    return (
      <div className={cn('text-center py-12 text-red-400', className)}>
        <Lock size={32} className="mx-auto mb-2 opacity-50" />
        <p className="font-semibold">Access Denied: Admin privileges required</p>
      </div>
    );
  }

  const getHealthColor = (status: string) => {
    if (status === 'healthy') return 'text-green-400';
    if (status === 'warning') return 'text-yellow-400';
    return 'text-red-400';
  };

  const getHealthBgColor = (status: string) => {
    if (status === 'healthy') return 'bg-green-500/10 border-green-500/20';
    if (status === 'warning') return 'bg-yellow-500/10 border-yellow-500/20';
    return 'bg-red-500/10 border-red-500/20';
  };

  return (
    <div className={cn('space-y-6', className)}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-white flex items-center gap-2">
          <Settings size={28} className="text-blue-400" />
          Admin Control Panel
        </h1>
        <div className="flex items-center gap-2 px-3 py-1 bg-green-500/10 border border-green-500/20 rounded-lg">
          <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
          <span className="text-xs font-semibold text-green-400">System Operational</span>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="flex gap-2 border-b border-neutral-800">
        {(['overview', 'users', 'system', 'settings'] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setSelectedTab(tab)}
            className={cn(
              'px-4 py-2 font-semibold text-sm transition-colors capitalize',
              selectedTab === tab
                ? 'text-blue-400 border-b-2 border-blue-500 -mb-1'
                : 'text-neutral-400 hover:text-white'
            )}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Overview Tab */}
      {selectedTab === 'overview' && (
        <div className="space-y-6">
          {/* Key Metrics */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-neutral-900 border border-neutral-800 rounded-lg p-4">
              <div className="flex items-center justify-between mb-3">
                <span className="text-neutral-400 text-sm font-medium">Total Users</span>
                <Users size={16} className="text-blue-500" />
              </div>
              <p className="text-3xl font-bold text-white">{userStats.total_users.toLocaleString()}</p>
              <p className="text-xs text-neutral-500 mt-1">+{userStats.new_users_today} today</p>
            </div>

            <div className="bg-neutral-900 border border-neutral-800 rounded-lg p-4">
              <div className="flex items-center justify-between mb-3">
                <span className="text-neutral-400 text-sm font-medium">Active Users</span>
                <Activity size={16} className="text-green-500" />
              </div>
              <p className="text-3xl font-bold text-white">{userStats.active_users.toLocaleString()}</p>
              <p className="text-xs text-green-400 mt-1">{((userStats.active_users / userStats.total_users) * 100).toFixed(1)}% online</p>
            </div>

            <div className="bg-neutral-900 border border-neutral-800 rounded-lg p-4">
              <div className="flex items-center justify-between mb-3">
                <span className="text-neutral-400 text-sm font-medium">KYC Pending</span>
                <Eye size={16} className="text-yellow-500" />
              </div>
              <p className="text-3xl font-bold text-yellow-400">{userStats.kyc_pending}</p>
              <p className="text-xs text-neutral-500 mt-1">Needs review</p>
            </div>

            <div className="bg-neutral-900 border border-neutral-800 rounded-lg p-4">
              <div className="flex items-center justify-between mb-3">
                <span className="text-neutral-400 text-sm font-medium">System Uptime</span>
                <Server size={16} className="text-purple-500" />
              </div>
              <p className="text-3xl font-bold text-white">{systemHealth.uptime_percent}%</p>
              <p className="text-xs text-neutral-500 mt-1">Last 30 days</p>
            </div>
          </div>

          {/* System Health */}
          <div className="bg-neutral-900 border border-neutral-800 rounded-lg p-6">
            <h2 className="text-lg font-bold text-white mb-4">System Health</h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {[
                { name: 'Database', status: systemHealth.database },
                { name: 'API', status: systemHealth.api },
                { name: 'Cache', status: systemHealth.cache },
                { name: 'Workers', status: systemHealth.workers },
              ].map((service) => (
                <div
                  key={service.name}
                  className={cn(
                    'p-4 rounded-lg border',
                    getHealthBgColor(service.status)
                  )}
                >
                  <p className="text-sm font-semibold text-white mb-2">{service.name}</p>
                  <p className={cn('text-lg font-bold capitalize', getHealthColor(service.status))}>
                    {service.status}
                  </p>
                </div>
              ))}
            </div>
          </div>

          {/* User Growth Chart */}
          <div className="bg-neutral-900 border border-neutral-800 rounded-lg p-6">
            <h2 className="text-lg font-bold text-white mb-4">User Growth (30 Days)</h2>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={[
                { day: '1', users: 4800 },
                { day: '5', users: 4900 },
                { day: '10', users: 5100 },
                { day: '15', users: 5200 },
                { day: '20', users: 5300 },
                { day: '25', users: 5400 },
                { day: '30', users: 5432 },
              ]}>
                <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                <XAxis dataKey="day" stroke="#666" />
                <YAxis stroke="#666" />
                <Tooltip contentStyle={{ background: '#1a1a1a', border: '1px solid #333' }} />
                <Line type="monotone" dataKey="users" stroke="#3b82f6" strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* KYC Status Distribution */}
          <div className="bg-neutral-900 border border-neutral-800 rounded-lg p-6">
            <h2 className="text-lg font-bold text-white mb-4">KYC Status Distribution</h2>
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie
                  data={[
                    { name: 'Approved', value: userStats.kyc_approved },
                    { name: 'Pending', value: userStats.kyc_pending },
                    { name: 'Rejected', value: userStats.kyc_rejected },
                  ]}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={100}
                  dataKey="value"
                >
                  <Cell fill="#10b981" />
                  <Cell fill="#f59e0b" />
                  <Cell fill="#ef4444" />
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Users Tab */}
      {selectedTab === 'users' && (
        <div className="bg-neutral-900 border border-neutral-800 rounded-lg p-6">
          <h2 className="text-lg font-bold text-white mb-4">User Management</h2>
          <div className="space-y-4">
            <div className="flex items-center justify-between p-4 bg-neutral-800/50 rounded-lg">
              <div>
                <p className="font-semibold text-white">KYC Verification Queue</p>
                <p className="text-sm text-neutral-400">{userStats.kyc_pending} users pending approval</p>
              </div>
              <button className="bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-4 rounded transition-colors">
                Review Queue
              </button>
            </div>

            <div className="flex items-center justify-between p-4 bg-neutral-800/50 rounded-lg">
              <div>
                <p className="font-semibold text-white">User Reports</p>
                <p className="text-sm text-neutral-400">View detailed user activity and compliance</p>
              </div>
              <button className="bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-4 rounded transition-colors">
                Generate Report
              </button>
            </div>

            <div className="flex items-center justify-between p-4 bg-neutral-800/50 rounded-lg">
              <div>
                <p className="font-semibold text-white">Risk Assessment</p>
                <p className="text-sm text-neutral-400">Review high-risk users and accounts</p>
              </div>
              <button className="bg-orange-600 hover:bg-orange-700 text-white font-semibold py-2 px-4 rounded transition-colors">
                View High Risk
              </button>
            </div>
          </div>
        </div>
      )}

      {/* System Tab */}
      {selectedTab === 'system' && (
        <div className="bg-neutral-900 border border-neutral-800 rounded-lg p-6">
          <h2 className="text-lg font-bold text-white mb-4">System Configuration</h2>
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="p-4 bg-neutral-800/50 rounded-lg">
                <p className="text-sm font-semibold text-neutral-400 mb-1">API Response Time</p>
                <p className="text-2xl font-bold text-white">{systemHealth.response_time_ms}ms</p>
              </div>
              <div className="p-4 bg-neutral-800/50 rounded-lg">
                <p className="text-sm font-semibold text-neutral-400 mb-1">Database Connections</p>
                <p className="text-2xl font-bold text-white">42/50</p>
              </div>
            </div>

            <div className="space-y-2">
              <p className="text-sm font-semibold text-white">Server Configuration</p>
              <div className="bg-neutral-800/50 rounded-lg p-3 text-xs text-neutral-400 font-mono">
                <p>CPU Usage: 34%</p>
                <p>Memory Usage: 62%</p>
                <p>Disk Usage: 41%</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Settings Tab */}
      {selectedTab === 'settings' && (
        <div className="bg-neutral-900 border border-neutral-800 rounded-lg p-6">
          <h2 className="text-lg font-bold text-white mb-4">System Settings</h2>
          <div className="space-y-4">
            {[
              { label: 'Enable Maintenance Mode', description: 'Temporarily disable trading' },
              { label: 'Require 2FA for All Users', description: 'Enhanced security' },
              { label: 'Enable API Rate Limiting', description: 'Protect against abuse' },
              { label: 'Enable Automated Backups', description: 'Daily database backups' },
            ].map((setting, i) => (
              <div key={i} className="flex items-center justify-between p-4 bg-neutral-800/50 rounded-lg">
                <div>
                  <p className="font-semibold text-white">{setting.label}</p>
                  <p className="text-sm text-neutral-400">{setting.description}</p>
                </div>
                <input type="checkbox" className="w-5 h-5 cursor-pointer" />
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
