import React, { useState, useEffect, useCallback } from 'react';
import {
  Search,
  Building2,
  MapPin,
  DollarSign,
  FileUp,
  Sparkles,
  ExternalLink,
  X,
  RefreshCw,
} from 'lucide-react';
import { api, JobFilterParams } from '../services/api';
import { Job, Company, JobIngestionBatch } from '../types';

export const JobDatabaseView: React.FC = () => {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [totalJobs, setTotalJobs] = useState<number>(0);
  const [loadingJobs, setLoadingJobs] = useState<boolean>(true);
  const [activeSubTab, setActiveSubTab] = useState<'explorer' | 'ingestion' | 'companies' | 'batches'>('explorer');

  // Filters
  const [searchKeyword, setSearchKeyword] = useState<string>('');
  const [selectedCompany, setSelectedCompany] = useState<string>('');
  const [selectedWorkplace, setSelectedWorkplace] = useState<string>('all');
  const [selectedSeniority, setSelectedSeniority] = useState<string>('all');

  // Selected Job for Details Modal
  const [selectedJob, setSelectedJob] = useState<Job | null>(null);

  // Ingestion State
  const [ingestionType, setIngestionType] = useState<'json' | 'csv'>('json');
  const [rawTextToIngest, setRawTextToIngest] = useState<string>('');
  const [ingestionSource, setIngestionSource] = useState<string>('manual_import');
  const [isIngesting, setIsIngesting] = useState<boolean>(false);
  const [lastBatchResult, setLastBatchResult] = useState<JobIngestionBatch | null>(null);

  // Companies & Batches
  const [companies, setCompanies] = useState<Company[]>([]);
  const [batches, setBatches] = useState<JobIngestionBatch[]>([]);

  const fetchJobs = useCallback(async () => {
    setLoadingJobs(true);
    try {
      const params: JobFilterParams = {
        search: searchKeyword || undefined,
        company: selectedCompany || undefined,
        remote_type: selectedWorkplace !== 'all' ? selectedWorkplace : undefined,
        seniority_level: selectedSeniority !== 'all' ? selectedSeniority : undefined,
        page: 1,
        page_size: 50,
      };
      const data = await api.getJobs(params);
      setJobs(data.items);
      setTotalJobs(data.total);
    } catch (err) {
      console.error('Failed to load jobs:', err);
    } finally {
      setLoadingJobs(false);
    }
  }, [searchKeyword, selectedCompany, selectedWorkplace, selectedSeniority]);

  const fetchCompanies = useCallback(async () => {
    try {
      const data = await api.getCompanies();
      setCompanies(data.items);
    } catch (err) {
      console.error('Failed to load companies:', err);
    }
  }, []);

  const fetchBatches = useCallback(async () => {
    try {
      const data = await api.getIngestionBatches();
      setBatches(data.items);
    } catch (err) {
      console.error('Failed to load batches:', err);
    }
  }, []);

  useEffect(() => {
    fetchJobs();
    fetchCompanies();
    fetchBatches();
  }, [fetchJobs, fetchCompanies, fetchBatches]);

  // Seed sample fixtures
  const handleSeedFixtures = async () => {
    setIsIngesting(true);
    try {
      const results = await api.seedSampleFixtures();
      if (results.length > 0) {
        setLastBatchResult(results[0]);
      }
      await fetchJobs();
      await fetchCompanies();
      await fetchBatches();
      alert('Sample fixtures successfully ingested with conservative deduplication!');
    } catch (err: any) {
      alert(`Seeding failed: ${err.message}`);
    } finally {
      setIsIngesting(false);
    }
  };

  // Raw Text Ingestion
  const handleIngestText = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!rawTextToIngest.trim()) return;
    setIsIngesting(true);
    try {
      let batch: JobIngestionBatch;
      if (ingestionType === 'json') {
        batch = await api.ingestJobsJson(rawTextToIngest, ingestionSource);
      } else {
        batch = await api.ingestJobsCsv(rawTextToIngest, ingestionSource);
      }
      setLastBatchResult(batch);
      setRawTextToIngest('');
      await fetchJobs();
      await fetchCompanies();
      await fetchBatches();
    } catch (err: any) {
      alert(`Ingestion failed: ${err.message}`);
    } finally {
      setIsIngesting(false);
    }
  };

  // File Upload
  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setIsIngesting(true);
    try {
      const batch = await api.uploadJobsFile(file);
      setLastBatchResult(batch);
      await fetchJobs();
      await fetchCompanies();
      await fetchBatches();
    } catch (err: any) {
      alert(`File upload failed: ${err.message}`);
    } finally {
      setIsIngesting(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Top Banner */}
      <div
        className="card"
        style={{
          borderLeft: '4px solid #38bdf8',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '1rem',
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <h2 style={{ fontSize: '1.25rem', fontWeight: 700 }}>Normalized Job Database & Ingestion Hub</h2>
            <span className="badge badge-blue">Phase 3 Active</span>
          </div>
          <p style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
            Structured repository of discovered opportunities with deterministic, conservative deduplication.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
          <button
            onClick={handleSeedFixtures}
            disabled={isIngesting}
            className="btn btn-primary"
            style={{ fontSize: '0.8125rem' }}
          >
            <Sparkles size={14} />
            <span>{isIngesting ? 'Seeding...' : 'Seed Sample Fixtures (JSON/CSV)'}</span>
          </button>

          <button onClick={fetchJobs} className="btn btn-secondary" style={{ fontSize: '0.8125rem' }}>
            <RefreshCw size={14} />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid-3">
        <div className="card">
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>
            Total Discovered Jobs
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: 700, color: '#38bdf8', marginTop: '0.25rem' }}>
            {totalJobs}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
            Active normalized listings
          </div>
        </div>

        <div className="card">
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>
            Registered Companies
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: 700, color: '#34d399', marginTop: '0.25rem' }}>
            {companies.length}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
            Normalized company entities
          </div>
        </div>

        <div className="card">
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>
            Deduplication Strategy
          </div>
          <div style={{ fontSize: '1.125rem', fontWeight: 700, color: '#a855f7', marginTop: '0.25rem' }}>
            Deterministic & Conservative
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
            Protects distinct roles & locations
          </div>
        </div>
      </div>

      {/* Navigation Sub-Tabs */}
      <div style={{ display: 'flex', gap: '0.5rem', borderBottom: '1px solid var(--border-color)', paddingBottom: '0.5rem', flexWrap: 'wrap' }}>
        {[
          { id: 'explorer', label: `📋 Jobs Explorer (${totalJobs})` },
          { id: 'ingestion', label: '⚡ Ingestion Hub & Importers' },
          { id: 'companies', label: `🏢 Companies Registry (${companies.length})` },
          { id: 'batches', label: `🕒 Ingestion Batches (${batches.length})` },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveSubTab(tab.id as any)}
            className={`btn ${activeSubTab === tab.id ? 'btn-primary' : 'btn-secondary'}`}
            style={{ fontSize: '0.8125rem', padding: '0.4rem 0.875rem' }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* SUB-TAB 1: Jobs Explorer */}
      {activeSubTab === 'explorer' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          {/* Filters Bar */}
          <div className="card" style={{ padding: '1rem' }}>
            <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap', alignItems: 'center' }}>
              <div style={{ flex: 2, minWidth: '220px', position: 'relative' }}>
                <Search size={16} color="var(--text-muted)" style={{ position: 'absolute', left: '0.75rem', top: '50%', transform: 'translateY(-50%)' }} />
                <input
                  type="text"
                  placeholder="Search title, skills, keywords..."
                  value={searchKeyword}
                  onChange={(e) => setSearchKeyword(e.target.value)}
                  style={{ width: '100%', padding: '0.5rem 0.5rem 0.5rem 2.25rem', background: '#090d16', border: '1px solid var(--border-color)', borderRadius: '6px', color: '#f8fafc', fontSize: '0.8125rem' }}
                />
              </div>

              <div style={{ flex: 1, minWidth: '150px' }}>
                <input
                  type="text"
                  placeholder="Filter Company..."
                  value={selectedCompany}
                  onChange={(e) => setSelectedCompany(e.target.value)}
                  style={{ width: '100%', padding: '0.5rem', background: '#090d16', border: '1px solid var(--border-color)', borderRadius: '6px', color: '#f8fafc', fontSize: '0.8125rem' }}
                />
              </div>

              <div>
                <select
                  value={selectedWorkplace}
                  onChange={(e) => setSelectedWorkplace(e.target.value)}
                  style={{ padding: '0.5rem', background: '#090d16', border: '1px solid var(--border-color)', borderRadius: '6px', color: '#f8fafc', fontSize: '0.8125rem' }}
                >
                  <option value="all">Workplace: All</option>
                  <option value="remote">Remote Only</option>
                  <option value="hybrid">Hybrid</option>
                  <option value="on_site">On-Site</option>
                </select>
              </div>

              <div>
                <select
                  value={selectedSeniority}
                  onChange={(e) => setSelectedSeniority(e.target.value)}
                  style={{ padding: '0.5rem', background: '#090d16', border: '1px solid var(--border-color)', borderRadius: '6px', color: '#f8fafc', fontSize: '0.8125rem' }}
                >
                  <option value="all">Seniority: All</option>
                  <option value="senior">Senior</option>
                  <option value="staff">Staff</option>
                  <option value="lead">Lead</option>
                  <option value="principal">Principal</option>
                  <option value="mid">Mid-Level</option>
                  <option value="entry">Entry-Level</option>
                </select>
              </div>
            </div>
          </div>

          {/* Jobs List */}
          {loadingJobs ? (
            <div className="card" style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-muted)' }}>
              Loading normalized jobs...
            </div>
          ) : jobs.length === 0 ? (
            <div className="card" style={{ padding: '3rem', textAlign: 'center' }}>
              <p style={{ color: 'var(--text-secondary)', marginBottom: '1rem' }}>
                No jobs found matching your filters.
              </p>
              <button onClick={handleSeedFixtures} className="btn btn-primary">
                <Sparkles size={14} />
                <span>Seed Sample Jobs from Fixtures</span>
              </button>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {jobs.map((job) => (
                <div key={job.id} className="card card-hover" style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '0.5rem' }}>
                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
                        <h3 style={{ fontSize: '1.0625rem', fontWeight: 600 }}>{job.title}</h3>
                        {job.seniority_level && (
                          <span className="badge badge-purple" style={{ fontSize: '0.6875rem' }}>
                            {job.seniority_level.toUpperCase()}
                          </span>
                        )}
                        {job.remote_type && (
                          <span className={`badge ${job.remote_type === 'remote' ? 'badge-green' : 'badge-blue'}`} style={{ fontSize: '0.6875rem' }}>
                            {job.remote_type.toUpperCase()}
                          </span>
                        )}
                      </div>

                      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginTop: '0.25rem', fontSize: '0.8125rem', color: 'var(--text-secondary)', flexWrap: 'wrap' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                          <Building2 size={14} color="var(--accent-blue)" />
                          <strong style={{ color: '#f8fafc' }}>{job.company}</strong>
                        </div>
                        {job.location && (
                          <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                            <MapPin size={14} color="var(--text-muted)" />
                            <span>{job.location}</span>
                          </div>
                        )}
                        {job.salary_min && (
                          <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem', color: '#34d399' }}>
                            <DollarSign size={14} />
                            <span>
                              {job.currency} {Number(job.salary_min).toLocaleString()}
                              {job.salary_max ? ` - ${Number(job.salary_max).toLocaleString()}` : ''}
                            </span>
                          </div>
                        )}
                      </div>
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <button
                        onClick={() => setSelectedJob(job)}
                        className="btn btn-secondary"
                        style={{ fontSize: '0.75rem', padding: '0.3rem 0.75rem' }}
                      >
                        <span>View Details</span>
                      </button>

                      {job.url && (
                        <a
                          href={job.url}
                          target="_blank"
                          rel="noreferrer"
                          className="btn btn-secondary"
                          style={{ fontSize: '0.75rem', padding: '0.3rem 0.6rem', color: '#38bdf8' }}
                          title="Open Original Link"
                        >
                          <ExternalLink size={14} />
                        </a>
                      )}
                    </div>
                  </div>

                  {job.skills_raw && job.skills_raw.length > 0 && (
                    <div style={{ display: 'flex', gap: '0.375rem', flexWrap: 'wrap' }}>
                      {job.skills_raw.map((s, idx) => (
                        <span key={idx} style={{ fontSize: '0.6875rem', padding: '0.125rem 0.375rem', background: '#090d16', border: '1px solid var(--border-color)', borderRadius: '4px', color: '#94a3b8' }}>
                          {s}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* SUB-TAB 2: Ingestion Hub */}
      {activeSubTab === 'ingestion' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          <div className="card" style={{ borderLeft: '4px solid #10b981' }}>
            <h3 style={{ fontSize: '1.125rem', fontWeight: 600, marginBottom: '0.5rem' }}>
              Multi-Source Job Ingestion & Normalization Engine
            </h3>
            <p style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
              Ingest job batches via JSON or CSV feeds. The engine automatically standardizes column aliases, registers normalized company profiles, and applies deterministic, conservative deduplication.
            </p>
          </div>

          <div className="grid-2">
            {/* Direct Text Ingest */}
            <div className="card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
                <h4 style={{ fontSize: '0.9375rem', fontWeight: 600 }}>Paste Raw Jobs (JSON / CSV)</h4>
                <div style={{ display: 'flex', gap: '0.25rem' }}>
                  <button
                    type="button"
                    onClick={() => setIngestionType('json')}
                    className={`btn ${ingestionType === 'json' ? 'btn-primary' : 'btn-secondary'}`}
                    style={{ fontSize: '0.6875rem', padding: '0.2rem 0.5rem' }}
                  >
                    JSON
                  </button>
                  <button
                    type="button"
                    onClick={() => setIngestionType('csv')}
                    className={`btn ${ingestionType === 'csv' ? 'btn-primary' : 'btn-secondary'}`}
                    style={{ fontSize: '0.6875rem', padding: '0.2rem 0.5rem' }}
                  >
                    CSV
                  </button>
                </div>
              </div>

              <form onSubmit={handleIngestText} style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                <input
                  type="text"
                  placeholder="Source Label (e.g. greenhouse_feed, manual_import)"
                  value={ingestionSource}
                  onChange={(e) => setIngestionSource(e.target.value)}
                  style={{ width: '100%', padding: '0.5rem', background: '#090d16', border: '1px solid var(--border-color)', borderRadius: '6px', color: '#f8fafc', fontSize: '0.8125rem' }}
                />

                <textarea
                  rows={8}
                  placeholder={
                    ingestionType === 'json'
                      ? '[\n  {\n    "title": "Software Engineer",\n    "company": "Stripe",\n    "location": "San Francisco, CA"\n  }\n]'
                      : 'job_title,employer,location,remote_type\nSenior SRE,Cloudflare,Remote,remote'
                  }
                  value={rawTextToIngest}
                  onChange={(e) => setRawTextToIngest(e.target.value)}
                  style={{ width: '100%', padding: '0.5rem', background: '#090d16', border: '1px solid var(--border-color)', borderRadius: '6px', color: '#f8fafc', fontFamily: 'monospace', fontSize: '0.75rem' }}
                />

                <button type="submit" disabled={isIngesting || !rawTextToIngest.trim()} className="btn btn-primary">
                  <FileUp size={14} />
                  <span>{isIngesting ? 'Ingesting...' : `Ingest Raw ${ingestionType.toUpperCase()}`}</span>
                </button>
              </form>
            </div>

            {/* File Upload & Fixture Actions */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div className="card">
                <h4 style={{ fontSize: '0.9375rem', fontWeight: 600, marginBottom: '0.75rem' }}>
                  Upload Job File (.json or .csv)
                </h4>
                <div
                  style={{
                    border: '2px dashed var(--border-color)',
                    borderRadius: '8px',
                    padding: '2rem 1rem',
                    textAlign: 'center',
                    background: '#090d16',
                  }}
                >
                  <FileUp size={32} color="#38bdf8" style={{ margin: '0 auto 0.75rem' }} />
                  <label className="btn btn-secondary" style={{ cursor: 'pointer' }}>
                    <span>Choose File to Ingest</span>
                    <input type="file" accept=".json,.csv,.txt" onChange={handleFileUpload} style={{ display: 'none' }} />
                  </label>
                </div>
              </div>

              <div className="card" style={{ background: '#0b1120' }}>
                <h4 style={{ fontSize: '0.9375rem', fontWeight: 600, marginBottom: '0.5rem' }}>
                  Built-in Sample Fixtures
                </h4>
                <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: '0.75rem', lineHeight: 1.4 }}>
                  Instantly load bundled test fixtures (<code>jobs_sample.json</code> and <code>jobs_sample.csv</code>) containing tech roles across multiple companies with intentional duplicates to verify conservative deduplication.
                </p>
                <button onClick={handleSeedFixtures} disabled={isIngesting} className="btn btn-primary" style={{ width: '100%' }}>
                  <Sparkles size={14} />
                  <span>Seed Built-in Fixtures Now</span>
                </button>
              </div>
            </div>
          </div>

          {/* Last Batch Result Summary */}
          {lastBatchResult && (
            <div className="card" style={{ borderTop: '3px solid #34d399' }}>
              <h4 style={{ fontSize: '1rem', fontWeight: 700, marginBottom: '0.75rem' }}>
                Latest Batch Ingestion Result: <code>{lastBatchResult.batch_id}</code>
              </h4>
              <div className="grid-3" style={{ marginBottom: '1rem' }}>
                <div style={{ background: '#090d16', padding: '0.75rem', borderRadius: '6px' }}>
                  <div style={{ fontSize: '0.6875rem', color: 'var(--text-muted)' }}>Inserted New Jobs</div>
                  <div style={{ fontSize: '1.25rem', fontWeight: 700, color: '#34d399' }}>{lastBatchResult.inserted_count}</div>
                </div>
                <div style={{ background: '#090d16', padding: '0.75rem', borderRadius: '6px' }}>
                  <div style={{ fontSize: '0.6875rem', color: 'var(--text-muted)' }}>Duplicates Deduplicated</div>
                  <div style={{ fontSize: '1.25rem', fontWeight: 700, color: '#fbbf24' }}>{lastBatchResult.duplicate_count}</div>
                </div>
                <div style={{ background: '#090d16', padding: '0.75rem', borderRadius: '6px' }}>
                  <div style={{ fontSize: '0.6875rem', color: 'var(--text-muted)' }}>Errors Encountered</div>
                  <div style={{ fontSize: '1.25rem', fontWeight: 700, color: lastBatchResult.error_count > 0 ? '#f87171' : '#94a3b8' }}>
                    {lastBatchResult.error_count}
                  </div>
                </div>
              </div>

              {lastBatchResult.error_log && lastBatchResult.error_log.length > 0 && (
                <div>
                  <h5 style={{ fontSize: '0.8125rem', color: '#f87171', marginBottom: '0.25rem' }}>Error Logs:</h5>
                  <pre className="code-block" style={{ maxHeight: '150px', overflowY: 'auto' }}>
                    {JSON.stringify(lastBatchResult.error_log, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* SUB-TAB 3: Companies Registry */}
      {activeSubTab === 'companies' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          <div className="card">
            <h3 style={{ fontSize: '1.125rem', fontWeight: 600, marginBottom: '1rem' }}>
              Normalized Company Directory
            </h3>

            {companies.length === 0 ? (
              <p style={{ color: 'var(--text-muted)' }}>No companies registered yet. Ingest jobs to populate companies.</p>
            ) : (
              <div className="grid-3">
                {companies.map((comp) => (
                  <div key={comp.id} className="card" style={{ background: '#090d16' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                      <div>
                        <h4 style={{ fontSize: '1rem', fontWeight: 600 }}>{comp.name}</h4>
                        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.125rem' }}>
                          Key: <code>{comp.normalized_name}</code>
                        </div>
                      </div>
                      {comp.careers_url && (
                        <a href={comp.careers_url} target="_blank" rel="noreferrer" style={{ color: '#38bdf8' }}>
                          <ExternalLink size={14} />
                        </a>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* SUB-TAB 4: Ingestion Batches */}
      {activeSubTab === 'batches' && (
        <div className="card">
          <h3 style={{ fontSize: '1.125rem', fontWeight: 600, marginBottom: '1rem' }}>
            Ingestion Batch Audit Trail
          </h3>

          <div style={{ overflowX: 'auto', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Batch ID</th>
                  <th>Source</th>
                  <th>Total</th>
                  <th>Inserted</th>
                  <th>Duplicates</th>
                  <th>Errors</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {batches.map((b) => (
                  <tr key={b.batch_id}>
                    <td><code>{b.batch_id}</code></td>
                    <td><span className="badge badge-gray">{b.source}</span></td>
                    <td>{b.total_records}</td>
                    <td style={{ color: '#34d399', fontWeight: 600 }}>{b.inserted_count}</td>
                    <td style={{ color: '#fbbf24' }}>{b.duplicate_count}</td>
                    <td style={{ color: b.error_count > 0 ? '#f87171' : 'inherit' }}>{b.error_count}</td>
                    <td>
                      <span className={`badge ${b.status === 'completed' ? 'badge-green' : 'badge-red'}`}>
                        {b.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Job Details Modal */}
      {selectedJob && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.8)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 100,
            padding: '1.5rem',
          }}
        >
          <div
            className="card"
            style={{
              maxWidth: '750px',
              width: '100%',
              maxHeight: '90vh',
              overflowY: 'auto',
              backgroundColor: '#0f172a',
              border: '1px solid #38bdf8',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1rem' }}>
              <div>
                <h3 style={{ fontSize: '1.25rem', fontWeight: 700 }}>{selectedJob.title}</h3>
                <div style={{ fontSize: '0.875rem', color: 'var(--accent-blue)', marginTop: '0.25rem' }}>
                  {selectedJob.company} {selectedJob.location && `· ${selectedJob.location}`}
                </div>
              </div>
              <button onClick={() => setSelectedJob(null)} className="btn btn-secondary" style={{ padding: '0.25rem 0.5rem' }}>
                <X size={16} />
              </button>
            </div>

            <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', marginBottom: '1.25rem' }}>
              {selectedJob.seniority_level && <span className="badge badge-purple">{selectedJob.seniority_level}</span>}
              {selectedJob.remote_type && <span className="badge badge-green">{selectedJob.remote_type}</span>}
              {selectedJob.salary_min && (
                <span className="badge badge-blue">
                  {selectedJob.currency} {Number(selectedJob.salary_min).toLocaleString()}
                  {selectedJob.salary_max ? ` - ${Number(selectedJob.salary_max).toLocaleString()}` : ''}
                </span>
              )}
            </div>

            <div style={{ marginBottom: '1.25rem' }}>
              <h4 style={{ fontSize: '0.8125rem', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '0.5rem' }}>
                Description
              </h4>
              <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', lineHeight: 1.6, whiteSpace: 'pre-wrap' }}>
                {selectedJob.description_raw || 'No raw description provided.'}
              </p>
            </div>

            <div style={{ background: '#090d16', padding: '0.75rem', borderRadius: '6px', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              <div>Deduplication Signature Hash: <code>{selectedJob.dedup_hash || 'N/A'}</code></div>
              <div>Source Feed: <code>{selectedJob.source}</code> {selectedJob.external_id && `· Ext ID: ${selectedJob.external_id}`}</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
