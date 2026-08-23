import React, { useState } from 'react';
import { Database, Key, Link as LinkIcon, Table } from 'lucide-react';

export const SchemaViewer: React.FC = () => {
  const [selectedTable, setSelectedTable] = useState<string>('candidate_profiles');

  const schemas: Record<
    string,
    {
      description: string;
      phase: string;
      columns: { name: string; type: string; constraints: string; description: string }[];
    }
  > = {
    candidate_profiles: {
      description: 'Master candidate profile representing verified ground truth for downstream AI modules.',
      phase: 'Phase 2 Active',
      columns: [
        { name: 'id', type: 'Integer', constraints: 'PK, Autoincrement', description: 'Unique profile identifier' },
        { name: 'full_name', type: 'String(255)', constraints: 'NOT NULL, Indexed', description: 'Candidate legal full name' },
        { name: 'email', type: 'String(255)', constraints: 'NOT NULL, Indexed', description: 'Primary contact email' },
        { name: 'phone', type: 'String(50)', constraints: 'Nullable', description: 'Telephone number' },
        { name: 'location', type: 'String(255)', constraints: 'Nullable', description: 'City, State/Country' },
        { name: 'headline', type: 'String(255)', constraints: 'Nullable', description: 'Professional title/headline' },
        { name: 'summary', type: 'Text', constraints: 'Nullable', description: 'Executive bio/summary' },
        { name: 'website', type: 'String(512)', constraints: 'Nullable', description: 'Personal website' },
        { name: 'linkedin_url', type: 'String(512)', constraints: 'Nullable', description: 'LinkedIn URL' },
        { name: 'github_url', type: 'String(512)', constraints: 'Nullable', description: 'GitHub URL' },
        { name: 'portfolio_url', type: 'String(512)', constraints: 'Nullable', description: 'Portfolio URL' },
        { name: 'is_verified', type: 'Boolean', constraints: 'Default: False, Indexed', description: 'Human verification gate' },
        { name: 'verified_at', type: 'DateTime', constraints: 'Nullable', description: 'Timestamp when approved' },
        { name: 'created_at', type: 'DateTime', constraints: 'NOT NULL (UTC)', description: 'Creation timestamp' },
        { name: 'updated_at', type: 'DateTime', constraints: 'NOT NULL (UTC)', description: 'Last modified timestamp' },
      ],
    },
    work_experiences: {
      description: 'Verified employment and work history entries.',
      phase: 'Phase 2 Active',
      columns: [
        { name: 'id', type: 'Integer', constraints: 'PK, Autoincrement', description: 'Unique identifier' },
        { name: 'profile_id', type: 'Integer', constraints: 'FK -> candidate_profiles.id (CASCADE)', description: 'Parent profile' },
        { name: 'company', type: 'String(255)', constraints: 'NOT NULL', description: 'Employer company' },
        { name: 'position', type: 'String(255)', constraints: 'NOT NULL', description: 'Job title / position' },
        { name: 'location', type: 'String(255)', constraints: 'Nullable', description: 'Work location' },
        { name: 'start_date', type: 'String(50)', constraints: 'NOT NULL', description: 'Start date (YYYY-MM)' },
        { name: 'end_date', type: 'String(50)', constraints: 'Nullable', description: 'End date (YYYY-MM)' },
        { name: 'is_current', type: 'Boolean', constraints: 'Default: False', description: 'Currently working flag' },
        { name: 'description', type: 'Text', constraints: 'Nullable', description: 'Overview description' },
        { name: 'highlights', type: 'JSON', constraints: 'Default: []', description: 'Bullet achievements' },
        { name: 'skills_used', type: 'JSON', constraints: 'Default: []', description: 'Skill tags applied' },
        { name: 'is_verified', type: 'Boolean', constraints: 'Default: False, Indexed', description: 'Human verified flag' },
        { name: 'order_index', type: 'Integer', constraints: 'Default: 0', description: 'Display order' },
        { name: 'created_at', type: 'DateTime', constraints: 'NOT NULL (UTC)', description: 'Creation timestamp' },
        { name: 'updated_at', type: 'DateTime', constraints: 'NOT NULL (UTC)', description: 'Last modified timestamp' },
      ],
    },
    educations: {
      description: 'Candidate academic degrees and certifications.',
      phase: 'Phase 2 Active',
      columns: [
        { name: 'id', type: 'Integer', constraints: 'PK, Autoincrement', description: 'Unique identifier' },
        { name: 'profile_id', type: 'Integer', constraints: 'FK -> candidate_profiles.id (CASCADE)', description: 'Parent profile' },
        { name: 'institution', type: 'String(255)', constraints: 'NOT NULL', description: 'University / College' },
        { name: 'degree', type: 'String(255)', constraints: 'NOT NULL', description: 'Degree title' },
        { name: 'field_of_study', type: 'String(255)', constraints: 'Nullable', description: 'Major / Field' },
        { name: 'start_date', type: 'String(50)', constraints: 'Nullable', description: 'Start date' },
        { name: 'end_date', type: 'String(50)', constraints: 'Nullable', description: 'Graduation date' },
        { name: 'gpa', type: 'String(50)', constraints: 'Nullable', description: 'Grade point average' },
        { name: 'highlights', type: 'JSON', constraints: 'Default: []', description: 'Honors & activities' },
        { name: 'is_verified', type: 'Boolean', constraints: 'Default: False, Indexed', description: 'Human verified flag' },
        { name: 'created_at', type: 'DateTime', constraints: 'NOT NULL (UTC)', description: 'Creation timestamp' },
        { name: 'updated_at', type: 'DateTime', constraints: 'NOT NULL (UTC)', description: 'Last modified timestamp' },
      ],
    },
    candidate_skills: {
      description: 'Categorized candidate technical competencies and proficiencies.',
      phase: 'Phase 2 Active',
      columns: [
        { name: 'id', type: 'Integer', constraints: 'PK, Autoincrement', description: 'Unique identifier' },
        { name: 'profile_id', type: 'Integer', constraints: 'FK -> candidate_profiles.id (CASCADE)', description: 'Parent profile' },
        { name: 'name', type: 'String(100)', constraints: 'NOT NULL, Indexed', description: 'Skill name' },
        { name: 'category', type: 'String(50)', constraints: 'Default: general', description: 'languages/frameworks/etc' },
        { name: 'proficiency', type: 'String(50)', constraints: 'Default: intermediate', description: 'Skill level' },
        { name: 'years_of_experience', type: 'Float', constraints: 'Nullable', description: 'Years of practice' },
        { name: 'is_verified', type: 'Boolean', constraints: 'Default: False, Indexed', description: 'Human verified flag' },
        { name: 'created_at', type: 'DateTime', constraints: 'NOT NULL (UTC)', description: 'Creation timestamp' },
        { name: 'updated_at', type: 'DateTime', constraints: 'NOT NULL (UTC)', description: 'Last modified timestamp' },
      ],
    },
    projects: {
      description: 'Candidate portfolio projects and open-source contributions.',
      phase: 'Phase 2 Active',
      columns: [
        { name: 'id', type: 'Integer', constraints: 'PK, Autoincrement', description: 'Unique identifier' },
        { name: 'profile_id', type: 'Integer', constraints: 'FK -> candidate_profiles.id (CASCADE)', description: 'Parent profile' },
        { name: 'name', type: 'String(255)', constraints: 'NOT NULL', description: 'Project title' },
        { name: 'description', type: 'Text', constraints: 'Nullable', description: 'Project summary' },
        { name: 'url', type: 'String(512)', constraints: 'Nullable', description: 'Live / Repository URL' },
        { name: 'highlights', type: 'JSON', constraints: 'Default: []', description: 'Key bullet points' },
        { name: 'technologies', type: 'JSON', constraints: 'Default: []', description: 'Tech stack tags' },
        { name: 'is_verified', type: 'Boolean', constraints: 'Default: False, Indexed', description: 'Human verified flag' },
        { name: 'created_at', type: 'DateTime', constraints: 'NOT NULL (UTC)', description: 'Creation timestamp' },
        { name: 'updated_at', type: 'DateTime', constraints: 'NOT NULL (UTC)', description: 'Last modified timestamp' },
      ],
    },
    raw_resume_imports: {
      description: 'Untrusted uploaded resume files and parsed draft fact snapshots.',
      phase: 'Phase 2 Active',
      columns: [
        { name: 'id', type: 'Integer', constraints: 'PK, Autoincrement', description: 'Unique identifier' },
        { name: 'profile_id', type: 'Integer', constraints: 'FK -> candidate_profiles.id (CASCADE)', description: 'Target profile' },
        { name: 'filename', type: 'String(255)', constraints: 'NOT NULL', description: 'Original uploaded filename' },
        { name: 'file_path', type: 'String(1024)', constraints: 'NOT NULL', description: 'Secure local storage path' },
        { name: 'file_hash', type: 'String(64)', constraints: 'NOT NULL, Indexed', description: 'SHA-256 integrity hash' },
        { name: 'file_size_bytes', type: 'Integer', constraints: 'NOT NULL', description: 'Size on disk' },
        { name: 'mime_type', type: 'String(100)', constraints: 'NOT NULL', description: 'MIME type' },
        { name: 'raw_text', type: 'Text', constraints: 'Nullable', description: 'Extracted raw text' },
        { name: 'parsed_data', type: 'JSON', constraints: 'Default: {}', description: 'Draft extracted facts' },
        { name: 'status', type: 'String(50)', constraints: 'Default: uploaded', description: 'uploaded/parsed/applied' },
        { name: 'created_at', type: 'DateTime', constraints: 'NOT NULL (UTC)', description: 'Upload timestamp' },
        { name: 'updated_at', type: 'DateTime', constraints: 'NOT NULL (UTC)', description: 'Last modified timestamp' },
      ],
    },
    jobs: {
      description: 'Stores discovered, scraped, and imported target job postings.',
      phase: 'Phase 1 Foundation',
      columns: [
        { name: 'id', type: 'Integer', constraints: 'PK, Autoincrement', description: 'Unique identifier' },
        { name: 'title', type: 'String(255)', constraints: 'NOT NULL, Indexed', description: 'Position title' },
        { name: 'company', type: 'String(255)', constraints: 'NOT NULL, Indexed', description: 'Company name' },
        { name: 'location', type: 'String(255)', constraints: 'Nullable', description: 'Location' },
        { name: 'status', type: 'String(50)', constraints: 'Default: discovered', description: 'Pipeline lifecycle status' },
      ],
    },
    audit_logs: {
      description: 'Immutable ledger of all automated steps, approvals, and system state transitions.',
      phase: 'Cross-Cutting',
      columns: [
        { name: 'id', type: 'Integer', constraints: 'PK, Autoincrement', description: 'Unique identifier' },
        { name: 'stage', type: 'String(50)', constraints: 'NOT NULL, Indexed', description: 'Pipeline stage' },
        { name: 'action', type: 'String(100)', constraints: 'NOT NULL', description: 'Action descriptor' },
        { name: 'level', type: 'String(20)', constraints: 'Default: info', description: 'info / warning / error' },
        { name: 'message', type: 'Text', constraints: 'NOT NULL', description: 'Human-readable log entry' },
        { name: 'payload', type: 'JSON', constraints: 'Default: {}', description: 'Diagnostic event payload' },
        { name: 'created_at', type: 'DateTime', constraints: 'NOT NULL (UTC)', description: 'Event timestamp' },
      ],
    },
  };

  const current = schemas[selectedTable] || schemas['candidate_profiles'];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      <div>
        <h2 style={{ fontSize: '1.5rem', fontWeight: 700, marginBottom: '0.5rem' }}>
          Database Schema Explorer (SQLAlchemy + Alembic)
        </h2>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
          Phase 2 models are migrated and active in SQLite WAL mode.
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
