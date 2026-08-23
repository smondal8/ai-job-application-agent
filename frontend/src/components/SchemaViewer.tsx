import React, { useState } from 'react';
import { Database, Key, Link as LinkIcon, Table } from 'lucide-react';

export const SchemaViewer: React.FC = () => {
  const [selectedTable, setSelectedTable] = useState<string>('job_analyses');

  const schemas: Record<
    string,
    {
      description: string;
      phase: string;
      columns: { name: string; type: string; constraints: string; description: string }[];
    }
  > = {
    job_analyses: {
      description: 'AI-driven job description analysis, fit score, and skill alignment matrix produced by local Ollama.',
      phase: 'Phase 5 Active',
      columns: [
        { name: 'id', type: 'Integer', constraints: 'PK, Autoincrement', description: 'Unique analysis ID' },
        { name: 'job_id', type: 'Integer', constraints: 'FK -> jobs.id (CASCADE), Indexed', description: 'Associated job listing' },
        { name: 'candidate_profile_id', type: 'Integer', constraints: 'FK -> candidate_profiles.id (SET NULL)', description: 'Evaluated candidate profile' },
        { name: 'fit_score', type: 'Float', constraints: 'Nullable', description: 'Objective match score (0.0 to 100.0)' },
        { name: 'fit_level', type: 'String(50)', constraints: 'Nullable', description: 'high, medium, low' },
        { name: 'summary', type: 'Text', constraints: 'Nullable', description: 'Executive fit assessment' },
        { name: 'role_summary', type: 'Text', constraints: 'Nullable', description: 'Synthesis of the role' },
        { name: 'key_responsibilities', type: 'JSON', constraints: 'Default: []', description: 'Extracted key responsibilities' },
        { name: 'matched_skills', type: 'JSON', constraints: 'Default: []', description: 'Verified candidate skills matching JD' },
        { name: 'missing_skills', type: 'JSON', constraints: 'Default: []', description: 'Skills requested in JD that candidate lacks' },
        { name: 'required_qualifications', type: 'JSON', constraints: 'Default: []', description: 'Mandatory role requirements' },
        { name: 'preferred_qualifications', type: 'JSON', constraints: 'Default: []', description: 'Nice-to-have qualifications' },
        { name: 'keywords', type: 'JSON', constraints: 'Default: []', description: 'High-signal ATS keywords' },
        { name: 'model_used', type: 'String(100)', constraints: 'Nullable', description: 'Local LLM model name (e.g. qwen3:8b)' },
        { name: 'raw_llm_response', type: 'Text', constraints: 'Nullable', description: 'Raw LLM completion' },
        { name: 'analysis_metadata', type: 'JSON', constraints: 'Default: {}', description: 'Diagnostic execution metadata' },
        { name: 'status', type: 'String(50)', constraints: 'Default: pending, Indexed', description: 'pending, completed, failed' },
        { name: 'created_at', type: 'DateTime', constraints: 'NOT NULL (UTC)', description: 'Created timestamp' },
      ],
    },
    tailored_resumes: {
      description: 'Tailored resume variants, atomic fact attribution matrices, and deterministically compiled documents (Markdown, ASCII, HTML).',
      phase: 'Phase 6 Active',
      columns: [
        { name: 'id', type: 'Integer', constraints: 'PK, Autoincrement', description: 'Unique tailored resume ID' },
        { name: 'job_id', type: 'Integer', constraints: 'FK -> jobs.id (CASCADE), Indexed', description: 'Target job listing' },
        { name: 'candidate_profile_id', type: 'Integer', constraints: 'FK -> candidate_profiles.id (SET NULL)', description: 'Source candidate profile' },
        { name: 'job_analysis_id', type: 'Integer', constraints: 'FK -> job_analyses.id (SET NULL), Indexed', description: 'Associated JD analysis' },
        { name: 'prompt_version', type: 'String(50)', constraints: 'NOT NULL, Default: v1.0.0', description: 'Versioned prompt identifier' },
        { name: 'model_used', type: 'String(100)', constraints: 'Nullable', description: 'Local LLM model name (e.g. qwen3:8b)' },
        { name: 'tailored_summary', type: 'Text', constraints: 'Nullable', description: 'Targeted executive summary' },
        { name: 'tailored_experience', type: 'JSON', constraints: 'Default: []', description: 'Tailored highlights mapped to source_fact_ids' },
        { name: 'highlighted_skills', type: 'JSON', constraints: 'Default: []', description: 'Selected verified candidate skills' },
        { name: 'cover_letter', type: 'Text', constraints: 'Nullable', description: 'Personalized cover letter' },
        { name: 'compiled_markdown', type: 'Text', constraints: 'Nullable', description: 'Deterministically compiled ATS Markdown' },
        { name: 'compiled_text', type: 'Text', constraints: 'Nullable', description: 'Plain ASCII text document' },
        { name: 'compiled_html', type: 'Text', constraints: 'Nullable', description: 'Styled print-ready HTML' },
        { name: 'traceability_matrix', type: 'JSON', constraints: 'Default: {}', description: 'Mapping of atomic fact IDs to tailored claims' },
        { name: 'validation_status', type: 'String(50)', constraints: 'NOT NULL, Default: valid', description: 'valid, requires_human_review, rejected' },
        { name: 'validation_details', type: 'JSON', constraints: 'Default: {}', description: 'Traceability score, untraced claims report' },
        { name: 'human_approved_at', type: 'DateTime', constraints: 'Nullable', description: 'Human approval timestamp' },
        { name: 'status', type: 'String(50)', constraints: 'Default: ready_for_review, Indexed', description: 'draft, ready_for_review, approved, rejected' },
        { name: 'created_at', type: 'DateTime', constraints: 'NOT NULL (UTC)', description: 'Created timestamp' },
      ],
    },
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
        { name: 'status', type: 'String(50)', constraints: 'Default: running, Indexed', description: 'completed, partial, failed' },
        { name: 'duration_ms', type: 'Float', constraints: 'Nullable', description: 'Total execution time in ms' },
        { name: 'created_at', type: 'DateTime', constraints: 'NOT NULL (UTC)', description: 'Created timestamp' },
      ],
    },
    jobs: {
      description: 'Normalized job listings catalog with deduplication hash and workplace metadata.',
      phase: 'Phase 3 Active',
      columns: [
        { name: 'id', type: 'Integer', constraints: 'PK, Autoincrement', description: 'Unique identifier' },
        { name: 'title', type: 'String(255)', constraints: 'NOT NULL, Indexed', description: 'Job position title' },
        { name: 'company', type: 'String(255)', constraints: 'NOT NULL, Indexed', description: 'Raw company name' },
        { name: 'location', type: 'String(255)', constraints: 'Nullable', description: 'Job location' },
        { name: 'remote_type', type: 'String(50)', constraints: 'Default: unspecified', description: 'remote, hybrid, on_site' },
        { name: 'status', type: 'String(50)', constraints: 'Default: discovered, Indexed', description: 'discovered/analyzed/applied' },
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

  const current = schemas[selectedTable] || schemas['job_analyses'];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      <div>
        <h2 style={{ fontSize: '1.5rem', fontWeight: 700, marginBottom: '0.5rem' }}>
          Database Schema Explorer (SQLAlchemy + Alembic)
        </h2>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
          Phase 5 models and tables active in SQLite WAL mode.
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
            <Database size={20} color="#c084fc" />
            <h3 style={{ fontSize: '1.125rem', fontWeight: 700 }}>Table: <code>{selectedTable}</code></h3>
          </div>
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <span className="badge badge-purple">{current.phase}</span>
            <span className="badge badge-blue">{current.columns.length} Columns</span>
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
                    <code style={{ color: '#c084fc', fontSize: '0.8125rem' }}>{col.type}</code>
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
