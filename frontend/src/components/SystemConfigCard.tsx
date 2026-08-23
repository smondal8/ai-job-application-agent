import React from 'react';
import { Sliders, Terminal, Check } from 'lucide-react';
import { SystemConfigResponse } from '../types';

interface SystemConfigCardProps {
  config: SystemConfigResponse | null;
}

export const SystemConfigCard: React.FC<SystemConfigCardProps> = ({ config }) => {
  if (!config) {
    return (
      <div className="card" style={{ padding: '2rem', textAlign: 'center' }}>
        <p style={{ color: 'var(--text-secondary)' }}>Loading configuration...</p>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      <div>
        <h2 style={{ fontSize: '1.5rem', fontWeight: 700, marginBottom: '0.5rem' }}>
          System Configuration & Environment
        </h2>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
          Pydantic Settings loaded safely from <code>.env</code> with strict local boundaries.
        </p>
      </div>

      <div className="grid-2">
        {/* Core Parameters */}
        <div className="card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem', color: 'var(--accent-blue)' }}>
            <Sliders size={20} />
            <h3 style={{ fontSize: '1rem', fontWeight: 600 }}>Core Application Settings</h3>
          </div>

          <table className="data-table">
            <tbody>
              <tr>
                <td style={{ color: 'var(--text-muted)' }}>Application Name</td>
                <td><strong>{config.app_name}</strong></td>
              </tr>
              <tr>
                <td style={{ color: 'var(--text-muted)' }}>Version</td>
                <td><code>v{config.app_version}</code></td>
              </tr>
              <tr>
                <td style={{ color: 'var(--text-muted)' }}>Environment</td>
                <td>
                  <span className="badge badge-blue">{config.environment}</span>
                </td>
              </tr>
              <tr>
                <td style={{ color: 'var(--text-muted)' }}>Debug Mode</td>
                <td>
                  <span className={`badge ${config.debug ? 'badge-yellow' : 'badge-gray'}`}>
                    {config.debug ? 'Enabled' : 'Disabled'}
                  </span>
                </td>
              </tr>
              <tr>
                <td style={{ color: 'var(--text-muted)' }}>API v1 Prefix</td>
                <td><code>{config.api_v1_prefix}</code></td>
              </tr>
            </tbody>
          </table>
        </div>

        {/* Runtime & Logging Parameters */}
        <div className="card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem', color: 'var(--accent-emerald)' }}>
            <Terminal size={20} />
            <h3 style={{ fontSize: '1rem', fontWeight: 600 }}>Storage & Logging Subsystems</h3>
          </div>

          <table className="data-table">
            <tbody>
              <tr>
                <td style={{ color: 'var(--text-muted)' }}>Database Engine</td>
                <td>
                  <span className="badge badge-green">SQLite 3 (Local WAL)</span>
                </td>
              </tr>
              <tr>
                <td style={{ color: 'var(--text-muted)' }}>Local Storage Dir</td>
                <td><code>{config.storage_dir}</code></td>
              </tr>
              <tr>
                <td style={{ color: 'var(--text-muted)' }}>Log Level</td>
                <td>
                  <span className="badge badge-purple">{config.log_level}</span>
                </td>
              </tr>
              <tr>
                <td style={{ color: 'var(--text-muted)' }}>Log Format</td>
                <td><code>{config.log_format} (with Request-ID filter)</code></td>
              </tr>
              <tr>
                <td style={{ color: 'var(--text-muted)' }}>Cloud Dependencies</td>
                <td>
                  <span className="badge badge-green" style={{ display: 'inline-flex', alignItems: 'center', gap: '0.25rem' }}>
                    <Check size={12} /> None (100% Local)
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
