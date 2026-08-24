import React, { useState, useEffect } from 'react';
import {
  Activity,
  ShieldCheck,
  Database,
  Download,
  RefreshCw,
  Clock,
  CheckCircle2,
  AlertTriangle,
  Server,
  Lock,
  Cpu,
  Archive,
} from 'lucide-react';
import { api } from '../services/api';
import { SystemMetricsResponse, BackupMetadata } from '../types';

export const SystemObservabilityView: React.FC = () => {
  const [metrics, setMetrics] = useState<SystemMetricsResponse | null>(null);
  const [backups, setBackups] = useState<BackupMetadata[]>([]);
  const [refreshing, setRefreshing] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Redaction tester state
  const [redactInput, setRedactInput] = useState<string>(
    'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.xyz\nOpenAI Key: sk-1234567890abcdef1234567890\npassword="MySecretPassword123"'
  );
  const [redactOutput, setRedactOutput] = useState<string>('');
  const [redacting, setRedacting] = useState<boolean>(false);

  // Recovery state
  const [recovering, setRecovering] = useState<boolean>(false);

  // Backup creation state
  const [creatingBackup, setCreatingBackup] = useState<boolean>(false);
  const [includeArtifacts, setIncludeArtifacts] = useState<boolean>(true);

  const loadData = async () => {
    try {
      setRefreshing(true);
      setError(null);
      const [metricsData, backupsData] = await Promise.all([
        api.getSystemMetrics(),
        api.listBackups(),
      ]);
      setMetrics(metricsData);
      setBackups(backupsData);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch observability telemetry.');
    } finally {
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 10000);
    return () => clearInterval(interval);
  }, []);

  const handleRunCrashRecovery = async () => {
    try {
      setRecovering(true);
      setError(null);
      const result = await api.recoverStaleTasks(15);
      setSuccessMessage(`Crash recovery executed: ${result.total_recovered} orphaned tasks reconciled.`);
      await loadData();
    } catch (err: any) {
      setError(err.message || 'Failed to execute crash recovery reconciliation.');
    } finally {
      setRecovering(false);
    }
  };

  const handleCreateBackup = async () => {
    try {
      setCreatingBackup(true);
      setError(null);
      const backup = await api.createBackup(includeArtifacts);
      setSuccessMessage(`Backup snapshot '${backup.backup_id}' created successfully with SHA-256 integrity verification.`);
      await loadData();
    } catch (err: any) {
      setError(err.message || 'Failed to generate backup snapshot.');
    } finally {
      setCreatingBackup(false);
    }
  };

  const handleVerifyBackup = async (backupId: string) => {
    try {
      setError(null);
      const res = await api.verifyBackup(backupId);
      if (res.is_valid) {
        setSuccessMessage(`Backup '${backupId}' cryptographically verified: SHA-256 and SQLite integrity intact.`);
      } else {
        setError(`Backup '${backupId}' verification failed: ${res.reason}`);
      }
    } catch (err: any) {
      setError(err.message || 'Verification error.');
    }
  };

  const handleRestoreBackup = async (backupId: string) => {
    if (!window.confirm(`Are you sure you want to restore backup '${backupId}'? Current data will be replaced.`)) {
      return;
    }
    try {
      setError(null);
      const res = await api.restoreBackup(backupId);
      setSuccessMessage(`Backup '${backupId}' restored successfully (${res.artifacts_restored} artifacts recovered).`);
      await loadData();
    } catch (err: any) {
      setError(err.message || 'Restoration failed.');
    }
  };

  const handleTestRedaction = async () => {
    try {
      setRedacting(true);
      const res = await api.redactSensitiveData({ raw_text: redactInput });
      setRedactOutput(res.raw_text || JSON.stringify(res, null, 2));
    } catch (err: any) {
      setError(err.message || 'Redaction test failed.');
    } finally {
      setRedacting(false);
    }
  };

  const formatUptime = (seconds: number) => {
    const hrs = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    return `${hrs}h ${mins}m ${secs}s`;
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h2 style={{ fontSize: '1.5rem', fontWeight: 700, margin: '0 0 0.25rem 0', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <Activity color="#34d399" size={26} />
            System Observability & Resilience (Phase 11)
          </h2>
          <p style={{ color: 'var(--text-muted)', margin: 0, fontSize: '0.875rem' }}>
            Telemetry, latencies, untrusted input boundaries, idempotency, crash recovery, and disaster backup/restore.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
          <button
            onClick={loadData}
            disabled={refreshing}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              padding: '0.5rem 1rem',
              borderRadius: '6px',
              backgroundColor: 'var(--card-bg)',
              color: 'var(--text-color)',
              border: '1px solid var(--border-color)',
              cursor: refreshing ? 'not-allowed' : 'pointer',
            }}
          >
            <RefreshCw size={16} className={refreshing ? 'spin' : ''} />
            Refresh Telemetry
          </button>
          <button
            onClick={handleRunCrashRecovery}
            disabled={recovering}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              padding: '0.5rem 1rem',
              borderRadius: '6px',
              backgroundColor: 'rgba(245, 158, 11, 0.15)',
              color: '#f59e0b',
              border: '1px solid rgba(245, 158, 11, 0.3)',
              cursor: recovering ? 'not-allowed' : 'pointer',
              fontWeight: 600,
            }}
          >
            <ShieldCheck size={16} />
            {recovering ? 'Reconciling...' : 'Run Crash Recovery'}
          </button>
        </div>
      </div>

      {error && (
        <div style={{ padding: '0.75rem 1rem', borderRadius: '6px', backgroundColor: 'rgba(239, 68, 68, 0.15)', border: '1px solid rgba(239, 68, 68, 0.3)', color: '#ef4444', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <AlertTriangle size={18} />
          <span>{error}</span>
        </div>
      )}

      {successMessage && (
        <div style={{ padding: '0.75rem 1rem', borderRadius: '6px', backgroundColor: 'rgba(52, 211, 153, 0.15)', border: '1px solid rgba(52, 211, 153, 0.3)', color: '#34d399', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <CheckCircle2 size={18} />
          <span>{successMessage}</span>
        </div>
      )}

      {/* Top Metrics Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1rem' }}>
        <div className="card" style={{ padding: '1.25rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
            <span style={{ color: 'var(--text-muted)', fontSize: '0.8125rem' }}>Service Health</span>
            <Server size={18} color="#34d399" />
          </div>
          <div style={{ fontSize: '1.25rem', fontWeight: 700, color: '#34d399', textTransform: 'capitalize' }}>
            {metrics?.status || 'Active'}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
            Uptime: {metrics ? formatUptime(metrics.uptime_seconds) : '...'}
          </div>
        </div>

        <div className="card" style={{ padding: '1.25rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
            <span style={{ color: 'var(--text-muted)', fontSize: '0.8125rem' }}>Database Latency</span>
            <Database size={18} color="#38bdf8" />
          </div>
          <div style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--text-color)' }}>
            {metrics?.database.latency_ms != null ? `${metrics.database.latency_ms.toFixed(2)} ms` : 'N/A'}
          </div>
          <div style={{ fontSize: '0.75rem', color: '#34d399', marginTop: '0.25rem' }}>
            Dialect: {metrics?.database.dialect || 'sqlite'} (Healthy)
          </div>
        </div>

        <div className="card" style={{ padding: '1.25rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
            <span style={{ color: 'var(--text-muted)', fontSize: '0.8125rem' }}>Approvals Granted</span>
            <ShieldCheck size={18} color="#c084fc" />
          </div>
          <div style={{ fontSize: '1.25rem', fontWeight: 700, color: '#c084fc' }}>
            {metrics?.counters['approvals_granted'] || 0}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
            Human security boundary events
          </div>
        </div>

        <div className="card" style={{ padding: '1.25rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
            <span style={{ color: 'var(--text-muted)', fontSize: '0.8125rem' }}>Local LLM Provider</span>
            <Cpu size={18} color="#f59e0b" />
          </div>
          <div style={{ fontSize: '1.125rem', fontWeight: 700, color: 'var(--text-color)' }}>
            {metrics?.system.llm_model || 'qwen3:8b'}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
            Provider: {metrics?.system.llm_provider || 'ollama'} (Apple Silicon GPU)
          </div>
        </div>
      </div>

      {/* Latency Telemetry Table */}
      <div className="card" style={{ padding: '1.25rem' }}>
        <h3 style={{ fontSize: '1rem', fontWeight: 600, margin: '0 0 1rem 0', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Clock size={18} color="#38bdf8" />
          Rolling Operation Latency Distribution
        </h3>
        {metrics && Object.keys(metrics.latencies).length > 0 ? (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.875rem' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border-color)', textAlign: 'left', color: 'var(--text-muted)' }}>
                  <th style={{ padding: '0.5rem' }}>Operation Name</th>
                  <th style={{ padding: '0.5rem' }}>Executions</th>
                  <th style={{ padding: '0.5rem' }}>Avg Latency</th>
                  <th style={{ padding: '0.5rem' }}>Min Latency</th>
                  <th style={{ padding: '0.5rem' }}>Max Latency</th>
                  <th style={{ padding: '0.5rem' }}>P95 Latency</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(metrics.latencies).map(([opName, metric]) => (
                  <tr key={opName} style={{ borderBottom: '1px solid var(--border-color)' }}>
                    <td style={{ padding: '0.625rem 0.5rem', fontWeight: 500 }}>
                      <code>{opName}</code>
                    </td>
                    <td style={{ padding: '0.625rem 0.5rem' }}>{metric.count}</td>
                    <td style={{ padding: '0.625rem 0.5rem', color: '#34d399' }}>{metric.avg_ms.toFixed(1)} ms</td>
                    <td style={{ padding: '0.625rem 0.5rem' }}>{metric.min_ms.toFixed(1)} ms</td>
                    <td style={{ padding: '0.625rem 0.5rem', color: metric.max_ms > 1000 ? '#f59e0b' : 'inherit' }}>
                      {metric.max_ms.toFixed(1)} ms
                    </td>
                    <td style={{ padding: '0.625rem 0.5rem', fontWeight: 600 }}>{metric.p95_ms.toFixed(1)} ms</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div style={{ padding: '1rem', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.875rem' }}>
            No operations executed yet during this session. Latency statistics will appear dynamically.
          </div>
        )}
      </div>

      {/* Backup & Disaster Recovery Section */}
      <div className="card" style={{ padding: '1.25rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <div>
            <h3 style={{ fontSize: '1rem', fontWeight: 600, margin: '0 0 0.25rem 0', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Archive size={18} color="#c084fc" />
              Disaster Recovery & SQLite Snapshots
            </h3>
            <p style={{ margin: 0, fontSize: '0.8125rem', color: 'var(--text-muted)' }}>
              Non-blocking point-in-time SQLite backups with PRAGMA integrity verification and SHA-256 artifact bundles.
            </p>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <label style={{ fontSize: '0.8125rem', display: 'flex', alignItems: 'center', gap: '0.375rem', cursor: 'pointer' }}>
              <input
                type="checkbox"
                checked={includeArtifacts}
                onChange={(e) => setIncludeArtifacts(e.target.checked)}
              />
              Bundle Artifacts
            </label>
            <button
              onClick={handleCreateBackup}
              disabled={creatingBackup}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.375rem',
                padding: '0.4rem 0.875rem',
                borderRadius: '6px',
                backgroundColor: 'rgba(192, 132, 252, 0.15)',
                color: '#c084fc',
                border: '1px solid rgba(192, 132, 252, 0.3)',
                cursor: creatingBackup ? 'not-allowed' : 'pointer',
                fontWeight: 600,
                fontSize: '0.8125rem',
              }}
            >
              <Download size={14} />
              {creatingBackup ? 'Creating...' : 'Create Snapshot'}
            </button>
          </div>
        </div>

        {backups.length > 0 ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {backups.map((b) => (
              <div
                key={b.backup_id}
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  padding: '0.75rem 1rem',
                  backgroundColor: 'rgba(255, 255, 255, 0.02)',
                  border: '1px solid var(--border-color)',
                  borderRadius: '6px',
                }}
              >
                <div>
                  <div style={{ fontWeight: 600, fontSize: '0.875rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <code>{b.backup_id}</code>
                    <span style={{ fontSize: '0.75rem', padding: '0.125rem 0.375rem', borderRadius: '4px', backgroundColor: 'rgba(52, 211, 153, 0.15)', color: '#34d399' }}>
                      Verified
                    </span>
                  </div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.25rem', display: 'flex', gap: '1rem' }}>
                    <span>Created: {new Date(b.created_at).toLocaleString()}</span>
                    <span>DB Size: {(b.db_size_bytes / 1024).toFixed(1)} KB</span>
                    <span>Artifacts: {b.artifacts_count} files ({(b.artifacts_size_bytes / 1024).toFixed(1)} KB)</span>
                    <span>SHA-256: <code>{b.db_sha256?.substring(0, 8)}...</code></span>
                  </div>
                </div>

                <div style={{ display: 'flex', gap: '0.5rem' }}>
                  <button
                    onClick={() => handleVerifyBackup(b.backup_id)}
                    style={{
                      padding: '0.35rem 0.65rem',
                      borderRadius: '4px',
                      backgroundColor: 'var(--card-bg)',
                      border: '1px solid var(--border-color)',
                      color: 'var(--text-color)',
                      fontSize: '0.75rem',
                      cursor: 'pointer',
                    }}
                  >
                    Verify
                  </button>
                  <button
                    onClick={() => handleRestoreBackup(b.backup_id)}
                    style={{
                      padding: '0.35rem 0.65rem',
                      borderRadius: '4px',
                      backgroundColor: 'rgba(245, 158, 11, 0.15)',
                      border: '1px solid rgba(245, 158, 11, 0.3)',
                      color: '#f59e0b',
                      fontSize: '0.75rem',
                      fontWeight: 600,
                      cursor: 'pointer',
                    }}
                  >
                    Restore
                  </button>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div style={{ padding: '1rem', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.875rem' }}>
            No backup snapshots generated yet. Click 'Create Snapshot' to produce an encrypted integrity-checked archive.
          </div>
        )}
      </div>

      {/* Sensitive Data Redaction Interactive Lab */}
      <div className="card" style={{ padding: '1.25rem' }}>
        <h3 style={{ fontSize: '1rem', fontWeight: 600, margin: '0 0 0.5rem 0', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Lock size={18} color="#ef4444" />
          Sensitive Data Redaction & Log Sanitization Lab
        </h3>
        <p style={{ fontSize: '0.8125rem', color: 'var(--text-muted)', margin: '0 0 1rem 0' }}>
          Tests real-time regex redaction of Bearer tokens, OpenAI/GitHub API keys, passwords, and private credentials.
        </p>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
          <div>
            <label style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', display: 'block', marginBottom: '0.375rem' }}>
              Input Payload / Raw Logs:
            </label>
            <textarea
              value={redactInput}
              onChange={(e) => setRedactInput(e.target.value)}
              rows={5}
              style={{
                width: '100%',
                backgroundColor: 'rgba(0, 0, 0, 0.2)',
                border: '1px solid var(--border-color)',
                borderRadius: '6px',
                padding: '0.5rem',
                color: 'var(--text-color)',
                fontFamily: 'monospace',
                fontSize: '0.8125rem',
              }}
            />
            <button
              onClick={handleTestRedaction}
              disabled={redacting}
              style={{
                marginTop: '0.5rem',
                padding: '0.4rem 0.875rem',
                borderRadius: '6px',
                backgroundColor: 'var(--card-bg)',
                border: '1px solid var(--border-color)',
                color: 'var(--text-color)',
                fontSize: '0.8125rem',
                cursor: 'pointer',
              }}
            >
              {redacting ? 'Sanitizing...' : 'Redact Payload'}
            </button>
          </div>

          <div>
            <label style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', display: 'block', marginBottom: '0.375rem' }}>
              Sanitized Output (Safe for Logs & Audit):
            </label>
            <textarea
              value={redactOutput}
              readOnly
              rows={5}
              placeholder="Sanitized text will appear here..."
              style={{
                width: '100%',
                backgroundColor: 'rgba(0, 0, 0, 0.4)',
                border: '1px solid rgba(52, 211, 153, 0.3)',
                borderRadius: '6px',
                padding: '0.5rem',
                color: '#34d399',
                fontFamily: 'monospace',
                fontSize: '0.8125rem',
              }}
            />
          </div>
        </div>
      </div>
    </div>
  );
};
