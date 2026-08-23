import React, { useState } from 'react';
import { Database, Key, Link as LinkIcon, Table } from 'lucide-react';

export const SchemaViewer: React.FC = () => {
  const [selectedTable, setSelectedTable] = useState<string>('jobs');

  const schemas: Record<
    string,
    {
      description: string;
      phase: string;
      columns: { name: string; type: string; constraints: string; description: string }[];
    }
  > = {
    jobs: {
      description: 'Stores discovered, scraped, and imported target job postings.',
      phase: 'Phase 2 Foundation',
      columns: [
        { name: 'id', type: 'Integer', constraints: 'PK, Autoincrement', description: 'Unique identifier' },
        { name: 'external_id', type: 'String(255)', constraints: 'Nullable, Indexed', description: 'ATS/Board job ID' },
        { name: 'title', type: 'String(255)', constraints: 'NOT NULL, Indexed', description: 'Position title' },
        { name: 'company', type: 'String(255)', constraints: 'NOT NULL, Indexed', description: 'Company name' },
        { name: 'location', type: 'String(255)', constraints: 'Nullable', description: 'City, State or Country' },
        { name: 'remote_type', type: 'String(50)', constraints: 'Default: unspecified', description: 'remote / hybrid / onsite' },
        { name: 'job_type', type: 'String(50)', constraints: 'Default: full-time', description: 'full-time / contract' },
        { name: 'url', type: 'String(1024)', constraints: 'Nullable', description: 'Original job posting URL' },
        { name: 'source', type: 'String(100)', constraints: 'Default: manual', description: 'greenhouse / lever / linkedin' },
        { name: 'description_raw', type: 'Text', constraints: 'Nullable', description: 'Raw job description' },
        { name: 'description_clean', type: 'Text', constraints: 'Nullable', description: 'Sanitized text' },
        { name: 'salary_min', type: 'Numeric(12,2)', constraints: 'Nullable', description: 'Base minimum compensation' },
        { name: 'salary_max', type: 'Numeric(12,2)', constraints: 'Nullable', description: 'Base maximum compensation' },
        { name: 'currency', type: 'String(10)', constraints: 'Default: USD', description: 'Currency ISO' },
        { name: 'status', type: 'String(50)', constraints: 'Default: discovered', description: 'Pipeline lifecycle status' },
        { name: 'posted_at', type: 'DateTime', constraints: 'Nullable', description: 'Date posted by employer' },
        { name: 'created_at', type: 'DateTime', constraints: 'NOT NULL (UTC)', description: 'Ingestion timestamp' },
        { name: 'updated_at', type: 'DateTime', constraints: 'NOT NULL (UTC)', description: 'Last modified timestamp' },
      ],
    },
    job_analyses: {
      description: 'Stores JD analysis, skill match breakdown, and qualification scoring.',
      phase: 'Phase 3 Foundation',
      columns: [
        { name: 'id', type: 'Integer', constraints: 'PK, Autoincrement', description: 'Unique identifier' },
        { name: 'job_id', type: 'Integer', constraints: 'FK -> jobs.id (CASCADE)', description: 'Associated job' },
        { name: 'fit_score', type: 'Float', constraints: 'Nullable (0-100)', description: 'Overall candidate match score' },
        { name: 'fit_level', type: 'String(50)', constraints: 'Nullable', description: 'high / medium / low' },
        { name: 'summary', type: 'Text', constraints: 'Nullable', description: 'Executive match summary' },
        { name: 'matched_skills', type: 'JSON', constraints: 'Default: []', description: 'Identified overlapping skills' },
        { name: 'missing_skills', type: 'JSON', constraints: 'Default: []', description: 'Missing required keywords' },
        { name: 'required_qualifications', type: 'JSON', constraints: 'Default: []', description: 'Must-have requirements' },
        { name: 'preferred_qualifications', type: 'JSON', constraints: 'Default: []', description: 'Bonus qualifications' },
        { name: 'keywords', type: 'JSON', constraints: 'Default: []', description: 'Extracted ATS keywords' },
        { name: 'analysis_metadata', type: 'JSON', constraints: 'Default: {}', description: 'Model runtime metadata' },
        { name: 'status', type: 'String(50)', constraints: 'Default: pending', description: 'pending / completed / failed' },
        { name: 'created_at', type: 'DateTime', constraints: 'NOT NULL (UTC)', description: 'Analysis timestamp' },
        { name: 'updated_at', type: 'DateTime', constraints: 'NOT NULL (UTC)', description: 'Last modified timestamp' },
      ],
    },
    resumes: {
      description: 'Stores master base resumes and candidate background profiles.',
      phase: 'Phase 4 Foundation',
      columns: [
        { name: 'id', type: 'Integer', constraints: 'PK, Autoincrement', description: 'Unique identifier' },
        { name: 'name', type: 'String(255)', constraints: 'NOT NULL', description: 'Profile / Resume label' },
        { name: 'version', type: 'String(50)', constraints: 'Default: 1.0', description: 'Version tag' },
        { name: 'contact_info', type: 'JSON', constraints: 'Default: {}', description: 'Name, email, phone, links' },
        { name: 'summary', type: 'Text', constraints: 'Nullable', description: 'Professional summary' },
        { name: 'skills', type: 'JSON', constraints: 'Default: []', description: 'Master skill taxonomy' },
        { name: 'experience', type: 'JSON', constraints: 'Default: []', description: 'Work history records' },
        { name: 'education', type: 'JSON', constraints: 'Default: []', description: 'Academic credentials' },
        { name: 'raw_content', type: 'Text', constraints: 'Nullable', description: 'Full text or Markdown' },
        { name: 'file_path', type: 'String(1024)', constraints: 'Nullable', description: 'Path to source PDF/DOCX' },
        { name: 'is_default', type: 'Boolean', constraints: 'Default: false', description: 'Default template flag' },
        { name: 'created_at', type: 'DateTime', constraints: 'NOT NULL (UTC)', description: 'Creation timestamp' },
        { name: 'updated_at', type: 'DateTime', constraints: 'NOT NULL (UTC)', description: 'Last modified timestamp' },
      ],
    },
    tailored_resumes: {
      description: 'Stores tailored resume variants generated for specific job postings.',
      phase: 'Phase 4 Foundation',
      columns: [
        { name: 'id', type: 'Integer', constraints: 'PK, Autoincrement', description: 'Unique identifier' },
        { name: 'job_id', type: 'Integer', constraints: 'FK -> jobs.id (CASCADE)', description: 'Target job' },
        { name: 'base_resume_id', type: 'Integer', constraints: 'FK -> resumes.id (CASCADE)', description: 'Base template' },
        { name: 'tailored_summary', type: 'Text', constraints: 'Nullable', description: 'Targeted summary' },
        { name: 'tailored_experience', type: 'JSON', constraints: 'Default: []', description: 'Aligned bullet points' },
        { name: 'highlighted_skills', type: 'JSON', constraints: 'Default: []', description: 'Emphasized skills' },
        { name: 'diff_summary', type: 'Text', constraints: 'Nullable', description: 'Summary of changes' },
        { name: 'file_path', type: 'String(1024)', constraints: 'Nullable', description: 'Rendered output PDF path' },
        { name: 'created_at', type: 'DateTime', constraints: 'NOT NULL (UTC)', description: 'Generation timestamp' },
        { name: 'updated_at', type: 'DateTime', constraints: 'NOT NULL (UTC)', description: 'Last modified timestamp' },
      ],
    },
    applications: {
      description: 'Tracks job application state machine from draft to submission.',
      phase: 'Phase 5 & 6 Foundation',
      columns: [
        { name: 'id', type: 'Integer', constraints: 'PK, Autoincrement', description: 'Unique identifier' },
        { name: 'job_id', type: 'Integer', constraints: 'FK -> jobs.id (CASCADE)', description: 'Target job' },
        { name: 'tailored_resume_id', type: 'Integer', constraints: 'FK -> tailored_resumes.id (SET NULL)', description: 'Attached resume variant' },
        { name: 'status', type: 'String(50)', constraints: 'Default: draft, Indexed', description: 'draft / pending_approval / approved / submitted' },
        { name: 'portal_type', type: 'String(100)', constraints: 'Default: generic', description: 'greenhouse / lever / workday' },
        { name: 'portal_url', type: 'String(1024)', constraints: 'Nullable', description: 'Direct application form URL' },
        { name: 'cover_letter', type: 'Text', constraints: 'Nullable', description: 'Tailored cover letter text' },
        { name: 'answers_payload', type: 'JSON', constraints: 'Default: {}', description: 'Pre-filled questionnaire answers' },
        { name: 'submission_notes', type: 'Text', constraints: 'Nullable', description: 'Log / verification notes' },
        { name: 'error_message', type: 'Text', constraints: 'Nullable', description: 'Submission error details' },
        { name: 'submitted_at', type: 'DateTime', constraints: 'Nullable', description: 'Timestamp when submitted' },
        { name: 'created_at', type: 'DateTime', constraints: 'NOT NULL (UTC)', description: 'Creation timestamp' },
        { name: 'updated_at', type: 'DateTime', constraints: 'NOT NULL (UTC)', description: 'Last modified timestamp' },
      ],
    },
    application_reviews: {
      description: 'Captures human reviewer feedback, decisions, and manual overrides.',
      phase: 'Phase 5 Foundation',
      columns: [
        { name: 'id', type: 'Integer', constraints: 'PK, Autoincrement', description: 'Unique identifier' },
        { name: 'application_id', type: 'Integer', constraints: 'FK -> applications.id (CASCADE)', description: 'Target application' },
        { name: 'decision', type: 'String(50)', constraints: 'Default: pending', description: 'pending / approved / rejected / changes_requested' },
        { name: 'reviewer_notes', type: 'Text', constraints: 'Nullable', description: 'User comments or guidance' },
        { name: 'manual_edits', type: 'JSON', constraints: 'Default: {}', description: 'Field-level user corrections' },
        { name: 'reviewed_at', type: 'DateTime', constraints: 'Nullable', description: 'Decision timestamp' },
        { name: 'created_at', type: 'DateTime', constraints: 'NOT NULL (UTC)', description: 'Creation timestamp' },
        { name: 'updated_at', type: 'DateTime', constraints: 'NOT NULL (UTC)', description: 'Last modified timestamp' },
      ],
    },
    audit_logs: {
      description: 'Immutable ledger of all automated steps, approvals, and system state transitions.',
      phase: 'Cross-Cutting',
      columns: [
        { name: 'id', type: 'Integer', constraints: 'PK, Autoincrement', description: 'Unique identifier' },
        { name: 'application_id', type: 'Integer', constraints: 'FK -> applications.id (CASCADE)', description: 'Related application (optional)' },
        { name: 'stage', type: 'String(50)', constraints: 'NOT NULL, Indexed', description: 'discovery / analysis / tailoring / approval / submission' },
        { name: 'action', type: 'String(100)', constraints: 'NOT NULL', description: 'Action descriptor' },
        { name: 'level', type: 'String(20)', constraints: 'Default: info', description: 'info / warning / error' },
        { name: 'message', type: 'Text', constraints: 'NOT NULL', description: 'Human-readable log entry' },
        { name: 'payload', type: 'JSON', constraints: 'Default: {}', description: 'Diagnostic event payload' },
        { name: 'created_at', type: 'DateTime', constraints: 'NOT NULL (UTC)', description: 'Event timestamp' },
      ],
    },
  };

  const current = schemas[selectedTable];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      <div>
        <h2 style={{ fontSize: '1.5rem', fontWeight: 700, marginBottom: '0.5rem' }}>
          Database Schema Explorer (SQLAlchemy + Alembic)
        </h2>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
          All 7 relational models are migrated and active in SQLite with WAL mode enabled.
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
            <span className="badge badge-blue">{current.phase}</span>
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
