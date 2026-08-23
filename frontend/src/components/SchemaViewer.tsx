import React, { useState } from 'react';
import { Database, Key, Link as LinkIcon, Table } from 'lucide-react';

export const SchemaViewer: React.FC = () => {
  const [selectedTable, setSelectedTable] = useState<string>('job_discovery_runs');

  const schemas: Record<
    string,
    {
      description: string;
      phase: string;
      columns: { name: string; type: string; constraints: string; description: string }[];
    }
  > = {
    job_discovery_runs: {
      description: 'Audit log of multi-source job discovery executions and per-adapter metrics.',
      phase: 'Phase 4 Active',
      columns: [
        { name: 'id', type: 'Integer', constraints: 'PK, Autoincrement', description: 'Unique execution ID' },
        { name: 'run_id', type: 'String(64)', constraints: 'NOT NULL, Unique, Indexed', description: 'Correlation run identifier' },
        { name: 'source', type: 'String(100)', constraints: 'NOT NULL', description: 'multi_source, greenhouse, lever, etc.' },
        { name: 'criteria', type: 'JSON', constraints: 'NOT NULL', description: 'SearchCriteria snapshot' },
        { name: 'total_discovered', type: 'Integer', constraints: 'Default: 0', description: 'Total postings discovered' },
        { name: 'inserted_count', type: 'Integer', constraints: 'Default: 0', description: 'New jobs saved to catalog' },
        { name: 'duplicate_count', type: 'Integer', constraints: 'Default: 0', description: 'Duplicates deduplicated' },
        { name: 'error_count', type: 'Integer', constraints: 'Default: 0', description: 'Adapter error count' },
        { name: 'status', type: 'String(50)', constraints: 'Default: running, Indexed', description: 'completed, partial, failed' },
        { name: 'duration_ms', type: 'Float', constraints: 'Nullable', description: 'Total execution time in ms' },
        { name: 'adapter_logs', type: 'JSON', constraints: 'Default: []', description: 'Per-adapter execution and fallback logs' },
        { name: 'created_at', type: 'DateTime', constraints: 'NOT NULL (UTC)', description: 'Created timestamp' },
      ],
    },
    job_search_profiles: {
      description: 'Saved search criteria templates for automated or 1-click repeated discovery.',
      phase: 'Phase 4 Active',
      columns: [
        { name: 'id', type: 'Integer', constraints: 'PK, Autoincrement', description: 'Unique profile identifier' },
        { name: 'name', type: 'String(255)', constraints: 'NOT NULL, Unique', description: 'Profile name template' },
        { name: 'description', type: 'Text', constraints: 'Nullable', description: 'Optional user description' },
        { name: 'criteria', type: 'JSON', constraints: 'NOT NULL', description: 'Target criteria configuration' },
        { name: 'is_active', type: 'Boolean', constraints: 'Default: True, Indexed', description: 'Active template flag' },
        { name: 'auto_run_interval_hours', type: 'Integer', constraints: 'Nullable', description: 'Optional periodic interval' },
        { name: 'created_at', type: 'DateTime', constraints: 'NOT NULL (UTC)', description: 'Created timestamp' },
      ],
    },
    jobs: {
      description: 'Normalized job listings catalog with deduplication hash and workplace metadata.',
      phase: 'Phase 3 Active',
      columns: [
        { name: 'id', type: 'Integer', constraints: 'PK, Autoincrement', description: 'Unique identifier' },
        { name: 'external_id', type: 'String(255)', constraints: 'Nullable, Indexed', description: 'Source job ID' },
        { name: 'company_id', type: 'Integer', constraints: 'FK -> companies.id (SET NULL)', description: 'Normalized company' },
        { name: 'batch_id', type: 'String(64)', constraints: 'FK -> job_ingestion_batches.batch_id', description: 'Ingestion batch ID' },
        { name: 'title', type: 'String(255)', constraints: 'NOT NULL, Indexed', description: 'Job position title' },
        { name: 'company', type: 'String(255)', constraints: 'NOT NULL, Indexed', description: 'Raw company name' },
        { name: 'location', type: 'String(255)', constraints: 'Nullable', description: 'Job location' },
        { name: 'department', type: 'String(100)', constraints: 'Nullable', description: 'Department or business unit' },
        { name: 'dedup_hash', type: 'String(64)', constraints: 'Nullable, Indexed', description: 'Deterministic SHA-256 deduplication hash' },
        { name: 'normalized_company', type: 'String(255)', constraints: 'Nullable, Indexed', description: 'Normalized company key' },
        { name: 'normalized_title', type: 'String(255)', constraints: 'Nullable, Indexed', description: 'Normalized title key' },
        { name: 'normalized_location', type: 'String(255)', constraints: 'Nullable, Indexed', description: 'Normalized location key' },
        { name: 'remote_type', type: 'String(50)', constraints: 'Default: unspecified', description: 'remote, hybrid, on_site' },
        { name: 'job_type', type: 'String(50)', constraints: 'Default: full-time', description: 'full-time, contract, part-time' },
        { name: 'seniority_level', type: 'String(50)', constraints: 'Nullable', description: 'entry, mid, senior, staff, lead' },
        { name: 'url', type: 'String(1024)', constraints: 'Nullable', description: 'Canonical posting URL' },
        { name: 'source', type: 'String(100)', constraints: 'NOT NULL', description: 'Source feed / adapter' },
        { name: 'description_raw', type: 'Text', constraints: 'Nullable', description: 'Original job description' },
        { name: 'salary_min', type: 'Numeric(12, 2)', constraints: 'Nullable', description: 'Minimum base salary' },
        { name: 'salary_max', type: 'Numeric(12, 2)', constraints: 'Nullable', description: 'Maximum base salary' },
        { name: 'currency', type: 'String(10)', constraints: 'Default: USD', description: 'Currency code' },
        { name: 'skills_raw', type: 'JSON', constraints: 'Default: []', description: 'Raw skill keywords' },
        { name: 'status', type: 'String(50)', constraints: 'Default: discovered, Indexed', description: 'discovered/analyzing/applied' },
        { name: 'is_active', type: 'Boolean', constraints: 'Default: True, Indexed', description: 'Active job flag' },
        { name: 'last_seen_at', type: 'DateTime', constraints: 'Nullable', description: 'Last ingestion confirmation' },
        { name: 'posted_at', type: 'DateTime', constraints: 'Nullable', description: 'Original posting date' },
        { name: 'created_at', type: 'DateTime', constraints: 'NOT NULL (UTC)', description: 'Created timestamp' },
      ],
    },
    companies: {
      description: 'Normalized registry of hiring companies and organizations.',
      phase: 'Phase 3 Active',
      columns: [
        { name: 'id', type: 'Integer', constraints: 'PK, Autoincrement', description: 'Unique company ID' },
        { name: 'name', type: 'String(255)', constraints: 'NOT NULL, Unique', description: 'Company display name' },
        { name: 'normalized_name', type: 'String(255)', constraints: 'NOT NULL, Unique, Indexed', description: 'Canonical normalized key' },
        { name: 'domain', type: 'String(255)', constraints: 'Nullable', description: 'Website domain' },
        { name: 'industry', type: 'String(100)', constraints: 'Nullable', description: 'Industry classification' },
        { name: 'company_size', type: 'String(50)', constraints: 'Nullable', description: 'Employee size bracket' },
        { name: 'careers_url', type: 'String(1024)', constraints: 'Nullable', description: 'Careers portal link' },
        { name: 'created_at', type: 'DateTime', constraints: 'NOT NULL (UTC)', description: 'Created timestamp' },
      ],
    },
    candidate_profiles: {
      description: 'Master candidate profile representing verified ground truth for downstream AI modules.',
      phase: 'Phase 2 Active',
      columns: [
        { name: 'id', type: 'Integer', constraints: 'PK, Autoincrement', description: 'Unique profile identifier' },
        { name: 'full_name', type: 'String(255)', constraints: 'NOT NULL, Indexed', description: 'Candidate legal full name' },
        { name: 'email', type: 'String(255)', constraints: 'NOT NULL, Indexed', description: 'Primary contact email' },
        { name: 'phone', type: 'String(50)', constraints: 'Nullable', description: 'Telephone number' },
        { name: 'is_verified', type: 'Boolean', constraints: 'Default: False, Indexed', description: 'Human verification gate' },
        { name: 'verified_at', type: 'DateTime', constraints: 'Nullable', description: 'Timestamp when approved' },
      ],
    },
    audit_logs: {
      description: 'Immutable ledger of all automated steps, approvals, and system state transitions.',
      phase: 'Cross-Cutting',
      columns: [
        { name: 'id', type: 'Integer', constraints: 'PK, Autoincrement', description: 'Unique identifier' },
        { name: 'stage', type: 'String(50)', constraints: 'NOT NULL, Indexed', description: 'Pipeline stage' },
        { name: 'action', type: 'String(100)', constraints: 'NOT NULL', description: 'Action descriptor' },
        { name: 'message', type: 'Text', constraints: 'NOT NULL', description: 'Human-readable log entry' },
        { name: 'payload', type: 'JSON', constraints: 'Default: {}', description: 'Diagnostic event payload' },
        { name: 'created_at', type: 'DateTime', constraints: 'NOT NULL (UTC)', description: 'Event timestamp' },
      ],
    },
  };

  const current = schemas[selectedTable] || schemas['job_discovery_runs'];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      <div>
        <h2 style={{ fontSize: '1.5rem', fontWeight: 700, marginBottom: '0.5rem' }}>
          Database Schema Explorer (SQLAlchemy + Alembic)
        </h2>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
          Phase 4 models and discovery tables active in SQLite WAL mode.
        </p>
      </div>

      {/* Table Selector Tabs */}
      <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
        {Object.keys(schemas).map((tableName) => (
          <button
            key={tableName}
            onClick={() => setSelectedTable(tableName)}
            className={`btn ${selectedTable === tableName ? 'btn-primary' : 'btn-secondary'}`}
            style={{ fontSize: '0.8125rem', padding: '0.5rem 0.875rem' }}
          >
            <Table size={14} />
            <span>{tableName}</span>
          </button>
        ))}
      </div>

      {/* Selected Table Card */}
      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem', flexWrap: 'wrap', gap: '0.5rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <Database size={20} color="#38bdf8" />
            <h3 style={{ fontSize: '1.125rem', fontWeight: 700 }}>Table: <code>{selectedTable}</code></h3>
          </div>
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <span className="badge badge-green">{current.phase}</span>
            <span className="badge badge-purple">{current.columns.length} Columns</span>
          </div>
        </div>

        <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', marginBottom: '1.25rem' }}>
          {current.description}
        </p>

        {/* Columns Table */}
        <div style={{ overflowX: 'auto', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
          <table className="data-table">
            <thead>
              <tr>
                <th>Column</th>
                <th>Type</th>
                <th>Constraints & Indexes</th>
                <th>Description</th>
              </tr>
            </thead>
            <tbody>
              {current.columns.map((col) => (
                <tr key={col.name}>
                  <td>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.375rem' }}>
                      {col.constraints.includes('PK') && <Key size={12} color="#fbbf24" />}
                      {col.constraints.includes('FK') && <LinkIcon size={12} color="#38bdf8" />}
                      <strong style={{ color: col.constraints.includes('PK') ? '#fbbf24' : '#f8fafc' }}>
                        {col.name}
                      </strong>
                    </div>
                  </td>
                  <td>
                    <code style={{ color: '#38bdf8', fontSize: '0.8125rem' }}>{col.type}</code>
                  </td>
                  <td>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{col.constraints}</span>
                  </td>
                  <td style={{ color: 'var(--text-secondary)' }}>{col.description}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
