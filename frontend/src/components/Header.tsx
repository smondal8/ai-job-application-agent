import React from 'react';
import { BookOpen, RefreshCw } from 'lucide-react';
import { HealthResponse } from '../types';

interface HeaderProps {
  health: HealthResponse | null;
  loading: boolean;
  onRefresh: () => void;
}

export const Header: React.FC<HeaderProps> = ({ health, loading, onRefresh }) => {
  const isHealthy = health?.status === 'healthy';
  const displayVersion = health?.version ? `v${health.version}` : 'v1.0.0';

  return (
    <header className="app-header">
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <div
            style={{
              width: '36px',
              height: '36px',
              borderRadius: '8px',
              backgroundColor: '#0284c7',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#fff',
              fontWeight: 700,
            }}
          >
            AI
          </div>
          <div>
            <h1 style={{ fontSize: '1.125rem', fontWeight: 700, lineHeight: 1.2 }}>
              AI Job Application Agent
            </h1>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              Autonomous Application Preparation & Safety System
            </p>
          </div>
        </div>

        <span className="badge badge-green" style={{ marginLeft: '0.5rem' }}>
          {displayVersion} (Phase 12 Complete)
        </span>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
        {/* Backend health status indicator */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            padding: '0.375rem 0.75rem',
            borderRadius: '9999px',
            backgroundColor: 'rgba(15, 23, 42, 0.6)',
            border: '1px solid var(--border-color)',
            fontSize: '0.8125rem',
          }}
        >
          <span className={`dot ${isHealthy ? 'dot-green' : 'dot-red'}`} />
          <span style={{ color: 'var(--text-secondary)' }}>Backend:</span>
          <strong style={{ color: isHealthy ? '#34d399' : '#f43f5e' }}>
            {health ? health.status.toUpperCase() : 'CONNECTING...'}
          </strong>
          {health?.database && (
            <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>
              ({health.database.latency_ms}ms)
            </span>
          )}
        </div>

        {/* Refresh button */}
        <button
          onClick={onRefresh}
          className="btn btn-secondary"
          style={{ padding: '0.375rem 0.75rem', fontSize: '0.8125rem' }}
          title="Refresh health checks"
          disabled={loading}
        >
          <RefreshCw size={14} />
          <span>Refresh</span>
        </button>

        {/* Swagger / Docs quick link */}
        <a
          href="/docs"
          target="_blank"
          rel="noopener noreferrer"
          className="btn btn-secondary"
          style={{ padding: '0.375rem 0.75rem', fontSize: '0.8125rem', textDecoration: 'none' }}
        >
          <BookOpen size={14} />
          <span>API Docs (Swagger)</span>
        </a>
      </div>
    </header>
  );
};
