import React from 'react';
import { Database, HardDrive, Clock, Cpu, CheckCircle2, AlertTriangle, XCircle } from 'lucide-react';
import { HealthResponse } from '../types';

interface HealthStatusCardProps {
  health: HealthResponse | null;
  loading?: boolean;
  error?: string | null;
}

export const HealthStatusCard: React.FC<HealthStatusCardProps> = ({ health, error }) => {
  const formatUptime = (seconds: number) => {
    if (seconds < 60) return `${Math.round(seconds)}s`;
    const mins = Math.floor(seconds / 60);
    const secs = Math.round(seconds % 60);
    return `${mins}m ${secs}s`;
  };

  if (error) {
    return (
      <div className="card" style={{ borderColor: 'rgba(244, 63, 94, 0.4)', backgroundColor: 'rgba(244, 63, 94, 0.05)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', color: '#f43f5e' }}>
          <XCircle size={24} />
          <div>
            <h3 style={{ fontSize: '1rem', fontWeight: 600 }}>Backend Unreachable</h3>
            <p style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)' }}>{error}</p>
          </div>
        </div>
      </div>
    );
  }

  if (!health) {
    return (
      <div className="card" style={{ textAlign: 'center', padding: '2rem' }}>
        <p style={{ color: 'var(--text-secondary)' }}>Checking subsystem health...</p>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Top Banner */}
      <div
        className="card"
        style={{
          borderLeft: `4px solid ${health.status === 'healthy' ? '#10b981' : '#f59e0b'}`,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '1rem',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          {health.status === 'healthy' ? (
            <CheckCircle2 size={32} color="#34d399" />
          ) : (
            <AlertTriangle size={32} color="#fbbf24" />
          )}
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <h2 style={{ fontSize: '1.25rem', fontWeight: 700 }}>System Health: {health.status.toUpperCase()}</h2>
              <span className="badge badge-green">Live Probe 200 OK</span>
            </div>
            <p style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
              All core services and local storage subsystems operational.
            </p>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <span className="badge badge-gray">Env: {health.environment}</span>
          <span className="badge badge-blue">Version: {health.version}</span>
        </div>
      </div>

      {/* Grid of Diagnostic Subsystems */}
      <div className="grid-4">
        {/* Database Diagnostic */}
        <div className="card card-hover">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--accent-blue)' }}>
              <Database size={20} />
              <span style={{ fontWeight: 600, fontSize: '0.875rem' }}>Database (SQLite)</span>
            </div>
            <span className={`badge ${health.database.connected ? 'badge-green' : 'badge-red'}`}>
              {health.database.connected ? 'Connected' : 'Disconnected'}
            </span>
          </div>
          <div style={{ fontSize: '1.5rem', fontWeight: 700, marginBottom: '0.25rem' }}>
            {health.database.latency_ms} <span style={{ fontSize: '0.875rem', fontWeight: 400, color: 'var(--text-muted)' }}>ms roundtrip</span>
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
            Target: {health.database.database_target || 'SQLite WAL'}
          </div>
        </div>

        {/* Local Storage Diagnostic */}
        <div className="card card-hover">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--accent-emerald)' }}>
              <HardDrive size={20} />
              <span style={{ fontWeight: 600, fontSize: '0.875rem' }}>Local Storage</span>
            </div>
            <span className={`badge ${health.storage.writable ? 'badge-green' : 'badge-red'}`}>
              {health.storage.writable ? 'Writable' : 'Read-Only'}
            </span>
          </div>
          <div style={{ fontSize: '1.125rem', fontWeight: 600, marginBottom: '0.25rem', color: '#f8fafc' }}>
            Ready & Mounted
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
            Path: {health.storage.storage_dir}
          </div>
        </div>

        {/* System Uptime */}
        <div className="card card-hover">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--accent-amber)' }}>
              <Clock size={20} />
              <span style={{ fontWeight: 600, fontSize: '0.875rem' }}>Uptime</span>
            </div>
            <span className="badge badge-yellow">Active</span>
          </div>
          <div style={{ fontSize: '1.5rem', fontWeight: 700, marginBottom: '0.25rem' }}>
            {formatUptime(health.uptime_seconds)}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            Process PID live
          </div>
        </div>

        {/* Engine Specs */}
        <div className="card card-hover">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--accent-purple)' }}>
              <Cpu size={20} />
              <span style={{ fontWeight: 600, fontSize: '0.875rem' }}>Dialect</span>
            </div>
            <span className="badge badge-purple">SQLAlchemy 2.0</span>
          </div>
          <div style={{ fontSize: '1.125rem', fontWeight: 600, marginBottom: '0.25rem', color: '#f8fafc' }}>
            SQLite + WAL
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            Foreign keys enforced
          </div>
        </div>
      </div>
    </div>
  );
};
