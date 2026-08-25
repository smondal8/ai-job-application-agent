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
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.875rem', flexShrink: 0 }}>
        <div
          style={{
            width: '38px',
            height: '38px',
            borderRadius: '8px',
            backgroundColor: '#0284c7',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#fff',
            fontWeight: 700,
            fontSize: '0.9375rem',
            flexShrink: 0,
          }}
        >
          AI
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.125rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.625rem', flexWrap: 'nowrap' }}>
            <h1 style={{ fontSize: '1.0625rem', fontWeight: 700, lineHeight: 1.2, margin: 0, color: '#f8fafc', whiteSpace: 'nowrap' }}>
              AI Job Application Agent
            </h1>
            <span
              className="badge badge-green"
              style={{
                fontSize: '0.6875rem',
                padding: '0.15rem 0.5rem',
                fontWeight: 600,
                letterSpacing: '0.02em',
                whiteSpace: 'nowrap',
              }}
            >
              {displayVersion} (Phase 12 Complete)
            </span>
          </div>
          <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', margin: 0, lineHeight: 1.3, whiteSpace: 'nowrap' }}>
            Autonomous Application Preparation &amp; Safety System
          </p>
        </div>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
        {/* Backend health status indicator */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            padding: '0.35rem 0.75rem',
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
          style={{ padding: '0.35rem 0.75rem', fontSize: '0.8125rem' }}
          title="Refresh health checks"
          disabled={loading}
        >
          <RefreshCw size={13} />
          <span>Refresh</span>
        </button>

        {/* Swagger / Docs quick link */}
        <a
          href="/docs"
          target="_blank"
          rel="noopener noreferrer"
          className="btn btn-secondary"
          style={{ padding: '0.35rem 0.75rem', fontSize: '0.8125rem', textDecoration: 'none' }}
        >
          <BookOpen size={13} />
          <span>API Docs (Swagger)</span>
        </a>
      </div>
    </header>
  );
};
