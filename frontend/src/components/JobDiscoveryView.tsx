import React, { useState, useEffect, useCallback } from 'react';
import {
  Compass,
  Play,
  CheckCircle,
  ExternalLink,
  Plus,
  Trash2,
  RefreshCw,
  Bookmark,
} from 'lucide-react';
import { api } from '../services/api';
import { AdapterInfo, DiscoveryRun, SearchProfile, SearchCriteria } from '../types';

export const JobDiscoveryView: React.FC = () => {
  const [adapters, setAdapters] = useState<AdapterInfo[]>([]);
  const [runs, setRuns] = useState<DiscoveryRun[]>([]);
  const [profiles, setProfiles] = useState<SearchProfile[]>([]);
  const [activeSubTab, setActiveSubTab] = useState<'launcher' | 'adapters' | 'profiles' | 'history'>('launcher');

  // Criteria State
  const [keywordsStr, setKeywordsStr] = useState<string>('Software Engineer, Distributed Systems');
  const [targetCompaniesStr, setTargetCompaniesStr] = useState<string>('stripe, openai, anthropic, figma, netflix');
  const [locationsStr, setLocationsStr] = useState<string>('San Francisco, CA, Remote');
  const [remoteOnly, setRemoteOnly] = useState<boolean>(false);
  const [minSalary, setMinSalary] = useState<string>('');
  const [selectedSources, setSelectedSources] = useState<string[]>(['greenhouse', 'lever', 'remote_tech', 'protected_portal_fallback']);
  const maxPerSource = 25;

  // Execution State
  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [lastRunResult, setLastRunResult] = useState<DiscoveryRun | null>(null);

  // New Profile Form
  const [showSaveProfileModal, setShowSaveProfileModal] = useState<boolean>(false);
  const [newProfileName, setNewProfileName] = useState<string>('');
  const [newProfileDesc, setNewProfileDesc] = useState<string>('');

  const fetchData = useCallback(async () => {
    try {
      const [adaptersData, runsData, profilesData] = await Promise.all([
        api.getDiscoveryAdapters(),
        api.getDiscoveryRuns(1, 20),
        api.getSearchProfiles(),
      ]);
      setAdapters(adaptersData);
      setRuns(runsData.items);
      setProfiles(profilesData.items);
    } catch (err) {
      console.error('Failed to load discovery data:', err);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const parseCriteria = (): SearchCriteria => {
    return {
      keywords: keywordsStr.split(',').map((s) => s.trim()).filter(Boolean),
      target_companies: targetCompaniesStr.split(',').map((s) => s.trim()).filter(Boolean),
      locations: locationsStr.split(',').map((s) => s.trim()).filter(Boolean),
      remote_only: remoteOnly,
      seniority_levels: [],
      min_salary: minSalary ? parseFloat(minSalary) : null,
      sources: selectedSources,
      max_results_per_source: maxPerSource,
    };
  };

  const handleLaunchDiscovery = async (criteriaOverride?: SearchCriteria, profileId?: number) => {
    setIsRunning(true);
    try {
      const criteria = criteriaOverride || parseCriteria();
      const runRecord = await api.runDiscovery({
        criteria,
        search_profile_id: profileId,
      });
      setLastRunResult(runRecord);
      await fetchData();
    } catch (err: any) {
      alert(`Discovery run failed: ${err.message}`);
    } finally {
      setIsRunning(false);
    }
  };

  const handleToggleSource = (sourceName: string) => {
    if (selectedSources.includes(sourceName)) {
      if (selectedSources.length === 1) return; // Keep at least one
      setSelectedSources(selectedSources.filter((s) => s !== sourceName));
    } else {
      setSelectedSources([...selectedSources, sourceName]);
    }
  };

  const handleSaveProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newProfileName.trim()) return;
    try {
      await api.createSearchProfile({
        name: newProfileName.trim(),
        description: newProfileDesc.trim() || undefined,
        criteria: parseCriteria(),
      });
      setShowSaveProfileModal(false);
      setNewProfileName('');
      setNewProfileDesc('');
      await fetchData();
      alert('Search profile saved successfully!');
    } catch (err: any) {
      alert(`Failed to save profile: ${err.message}`);
    }
  };

  const handleDeleteProfile = async (id: number) => {
    if (!confirm('Are you sure you want to delete this search profile?')) return;
    try {
      await api.deleteSearchProfile(id);
      await fetchData();
    } catch (err: any) {
      alert(`Failed to delete profile: ${err.message}`);
    }
  };

  const totalDiscoveredCount = runs.reduce((acc, r) => acc + r.total_discovered, 0);

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
            <Compass size={24} color="#38bdf8" />
            <h2 style={{ fontSize: '1.25rem', fontWeight: 700 }}>Source-Agnostic Job Discovery Framework</h2>
            <span className="badge badge-blue">Phase 4 Active</span>
          </div>
          <p style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
            Adapter-based job discovery with rate limiting, exponential backoff retries, and safe fallback for bot-protected platforms.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <button onClick={fetchData} className="btn btn-secondary" style={{ fontSize: '0.8125rem' }}>
            <RefreshCw size={14} />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* Metrics Cards */}
      <div className="grid-4">
        <div className="card">
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>
            Registered Adapters
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: 700, color: '#38bdf8', marginTop: '0.25rem' }}>
            {adapters.length}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
            Greenhouse, Lever, Feeds, Fallbacks
          </div>
        </div>

        <div className="card">
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>
            Discovery Runs
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: 700, color: '#34d399', marginTop: '0.25rem' }}>
            {runs.length}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
            Historical executions
          </div>
        </div>

        <div className="card">
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>
            Total Discovered
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: 700, color: '#c084fc', marginTop: '0.25rem' }}>
            {totalDiscoveredCount}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
            Listings passed to Phase 3
          </div>
        </div>

        <div className="card">
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>
            Fallback Safety
          </div>
          <div style={{ fontSize: '1.125rem', fontWeight: 700, color: '#fbbf24', marginTop: '0.25rem' }}>
            100% Compliant
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
            Safe manual links, no bypasses
          </div>
        </div>
      </div>

      {/* Sub-Tabs Navigation */}
      <div style={{ display: 'flex', gap: '0.5rem', borderBottom: '1px solid var(--border-color)', paddingBottom: '0.5rem', flexWrap: 'wrap' }}>
        {[
          { id: 'launcher', label: '🚀 Launch Discovery Run' },
          { id: 'adapters', label: `🔌 Adapters Directory (${adapters.length})` },
          { id: 'profiles', label: `📁 Saved Search Profiles (${profiles.length})` },
          { id: 'history', label: `🕒 Execution History (${runs.length})` },
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

      {/* SUB-TAB 1: Launch Discovery */}
      {activeSubTab === 'launcher' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          <div className="grid-2">
            {/* Criteria Form */}
            <div className="card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                <h3 style={{ fontSize: '1.0625rem', fontWeight: 700 }}>Search Criteria Builder</h3>
                <button
                  onClick={() => setShowSaveProfileModal(true)}
                  className="btn btn-secondary"
                  style={{ fontSize: '0.75rem', padding: '0.25rem 0.5rem' }}
                >
                  <Bookmark size={13} />
                  <span>Save as Profile</span>
                </button>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.375rem', fontWeight: 600 }}>
                    Target Role Keywords (comma-separated)
                  </label>
                  <input
                    type="text"
                    value={keywordsStr}
                    onChange={(e) => setKeywordsStr(e.target.value)}
                    placeholder="e.g. Senior Backend Engineer, Distributed Systems, Python"
                    style={{ width: '100%', padding: '0.5rem', background: '#090d16', border: '1px solid var(--border-color)', borderRadius: '6px', color: '#f8fafc', fontSize: '0.8125rem' }}
                  />
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.375rem', fontWeight: 600 }}>
                    Target Companies (Greenhouse / Lever board handles)
                  </label>
                  <input
                    type="text"
                    value={targetCompaniesStr}
                    onChange={(e) => setTargetCompaniesStr(e.target.value)}
                    placeholder="e.g. stripe, openai, anthropic, figma, datadog, netflix"
                    style={{ width: '100%', padding: '0.5rem', background: '#090d16', border: '1px solid var(--border-color)', borderRadius: '6px', color: '#f8fafc', fontSize: '0.8125rem' }}
                  />
                </div>

                <div className="grid-2">
                  <div>
                    <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.375rem', fontWeight: 600 }}>
                      Locations
                    </label>
                    <input
                      type="text"
                      value={locationsStr}
                      onChange={(e) => setLocationsStr(e.target.value)}
                      placeholder="e.g. San Francisco, CA, Remote"
                      style={{ width: '100%', padding: '0.5rem', background: '#090d16', border: '1px solid var(--border-color)', borderRadius: '6px', color: '#f8fafc', fontSize: '0.8125rem' }}
                    />
                  </div>

                  <div>
                    <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.375rem', fontWeight: 600 }}>
                      Min Salary ($)
                    </label>
                    <input
                      type="number"
                      value={minSalary}
                      onChange={(e) => setMinSalary(e.target.value)}
                      placeholder="e.g. 160000"
                      style={{ width: '100%', padding: '0.5rem', background: '#090d16', border: '1px solid var(--border-color)', borderRadius: '6px', color: '#f8fafc', fontSize: '0.8125rem' }}
                    />
                  </div>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <input
                    type="checkbox"
                    id="remoteOnly"
                    checked={remoteOnly}
                    onChange={(e) => setRemoteOnly(e.target.checked)}
                    style={{ cursor: 'pointer' }}
                  />
                  <label htmlFor="remoteOnly" style={{ fontSize: '0.8125rem', color: '#f8fafc', cursor: 'pointer' }}>
                    Strict Remote Only Listings
                  </label>
                </div>

                {/* Sources Selection */}
                <div>
                  <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.375rem', fontWeight: 600 }}>
                    Select Discovery Adapters
                  </label>
                  <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                    {adapters.map((a) => {
                      const selected = selectedSources.includes(a.source_name);
                      return (
                        <button
                          key={a.source_name}
                          type="button"
                          onClick={() => handleToggleSource(a.source_name)}
                          className={`btn ${selected ? 'btn-primary' : 'btn-secondary'}`}
                          style={{ fontSize: '0.75rem', padding: '0.3rem 0.6rem' }}
                        >
                          {selected ? <CheckCircle size={12} /> : <Plus size={12} />}
                          <span>{a.display_name}</span>
                        </button>
                      );
                    })}
                  </div>
                </div>

                <button
                  onClick={() => handleLaunchDiscovery()}
                  disabled={isRunning}
                  className="btn btn-primary"
                  style={{ width: '100%', padding: '0.75rem', fontSize: '0.9375rem', fontWeight: 600, marginTop: '0.5rem' }}
                >
                  <Play size={16} />
                  <span>{isRunning ? 'Discovering & Ingesting...' : 'Launch Multi-Source Discovery Run'}</span>
                </button>
              </div>
            </div>

            {/* Live Run Result Card */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              {lastRunResult ? (
                <div className="card" style={{ borderTop: `3px solid ${lastRunResult.status === 'completed' ? '#34d399' : '#fbbf24'}` }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                    <div>
                      <h4 style={{ fontSize: '1rem', fontWeight: 700 }}>Run: <code>{lastRunResult.run_id}</code></h4>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.125rem' }}>
                        Duration: {lastRunResult.duration_ms} ms · Status: <span className="badge badge-green">{lastRunResult.status.toUpperCase()}</span>
                      </div>
                    </div>
                  </div>

                  <div className="grid-3" style={{ marginBottom: '1.25rem' }}>
                    <div style={{ background: '#090d16', padding: '0.75rem', borderRadius: '6px' }}>
                      <div style={{ fontSize: '0.6875rem', color: 'var(--text-muted)' }}>Discovered</div>
                      <div style={{ fontSize: '1.25rem', fontWeight: 700, color: '#38bdf8' }}>{lastRunResult.total_discovered}</div>
                    </div>
                    <div style={{ background: '#090d16', padding: '0.75rem', borderRadius: '6px' }}>
                      <div style={{ fontSize: '0.6875rem', color: 'var(--text-muted)' }}>Inserted New</div>
                      <div style={{ fontSize: '1.25rem', fontWeight: 700, color: '#34d399' }}>{lastRunResult.inserted_count}</div>
                    </div>
                    <div style={{ background: '#090d16', padding: '0.75rem', borderRadius: '6px' }}>
                      <div style={{ fontSize: '0.6875rem', color: 'var(--text-muted)' }}>Duplicates Prevented</div>
                      <div style={{ fontSize: '1.25rem', fontWeight: 700, color: '#fbbf24' }}>{lastRunResult.duplicate_count}</div>
                    </div>
                  </div>

                  <h5 style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '0.5rem' }}>
                    Per-Adapter Execution Logs
                  </h5>

                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                    {lastRunResult.adapter_logs?.map((log, idx) => (
                      <div key={idx} style={{ background: '#090d16', padding: '0.75rem', borderRadius: '6px', fontSize: '0.75rem' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                          <strong>{log.adapter}</strong>
                          <span className={`badge ${log.status === 'success' ? 'badge-green' : 'badge-purple'}`}>
                            {log.status}
                          </span>
                        </div>

                        {log.fallback_links && (
                          <div style={{ marginTop: '0.5rem' }}>
                            <div style={{ color: '#fbbf24', marginBottom: '0.25rem' }}>
                              Compliant Manual Search Links:
                            </div>
                            <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                              {log.fallback_links.map((link: any, lIdx: number) => (
                                <a
                                  key={lIdx}
                                  href={link.url}
                                  target="_blank"
                                  rel="noreferrer"
                                  className="btn btn-secondary"
                                  style={{ fontSize: '0.6875rem', padding: '0.2rem 0.5rem', color: '#38bdf8' }}
                                >
                                  <span>{link.portal}</span>
                                  <ExternalLink size={11} />
                                </a>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="card" style={{ padding: '3rem 1.5rem', textAlign: 'center', color: 'var(--text-muted)' }}>
                  <Compass size={40} color="var(--border-color)" style={{ margin: '0 auto 1rem' }} />
                  <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
                    Configure search parameters and launch discovery to pull fresh opportunities across Greenhouse, Lever, and remote feeds.
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* SUB-TAB 2: Adapters Directory */}
      {activeSubTab === 'adapters' && (
        <div className="grid-2">
          {adapters.map((a) => (
            <div key={a.source_name} className="card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.5rem' }}>
                <div>
                  <h4 style={{ fontSize: '1.0625rem', fontWeight: 600 }}>{a.display_name}</h4>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                    Key: <code>{a.source_name}</code>
                  </div>
                </div>
                <span className={`badge ${a.is_reliable ? 'badge-green' : 'badge-blue'}`}>
                  {a.is_reliable ? 'Reliable Public' : 'Protected'}
                </span>
              </div>

              <p style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)', lineHeight: 1.5, margin: '0.5rem 0 1rem' }}>
                {a.description}
              </p>

              <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', fontSize: '0.75rem' }}>
                <span style={{ padding: '0.2rem 0.5rem', background: '#090d16', borderRadius: '4px', border: '1px solid var(--border-color)' }}>
                  Rate Limit: <strong>{a.rate_limit_per_minute} req/min</strong>
                </span>
                <span style={{ padding: '0.2rem 0.5rem', background: '#090d16', borderRadius: '4px', border: '1px solid var(--border-color)' }}>
                  Auth: <strong>{a.requires_auth ? 'Required (Safe Fallback)' : 'None (Open API)'}</strong>
                </span>
                {a.fallback_mode && (
                  <span style={{ padding: '0.2rem 0.5rem', background: '#090d16', borderRadius: '4px', border: '1px solid #fbbf24', color: '#fbbf24' }}>
                    Mode: {a.fallback_mode}
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* SUB-TAB 3: Saved Search Profiles */}
      {activeSubTab === 'profiles' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h3 style={{ fontSize: '1.125rem', fontWeight: 600 }}>Saved Search Criteria Templates</h3>
            <button onClick={() => setShowSaveProfileModal(true)} className="btn btn-primary" style={{ fontSize: '0.8125rem' }}>
              <Plus size={14} />
              <span>Create New Profile</span>
            </button>
          </div>

          {profiles.length === 0 ? (
            <div className="card" style={{ padding: '2.5rem', textAlign: 'center', color: 'var(--text-muted)' }}>
              No saved profiles yet. Save your current search criteria to enable 1-click repeated discovery.
            </div>
          ) : (
            <div className="grid-2">
              {profiles.map((p) => (
                <div key={p.id} className="card">
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                    <div>
                      <h4 style={{ fontSize: '1rem', fontWeight: 600 }}>{p.name}</h4>
                      {p.description && (
                        <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
                          {p.description}
                        </p>
                      )}
                    </div>
                    <button
                      onClick={() => handleDeleteProfile(p.id)}
                      className="btn btn-secondary"
                      style={{ padding: '0.25rem', color: '#f87171' }}
                    >
                      <Trash2 size={14} />
                    </button>
                  </div>

                  <div style={{ background: '#090d16', padding: '0.5rem 0.75rem', borderRadius: '6px', fontSize: '0.75rem', margin: '0.75rem 0' }}>
                    <div>Keywords: <code>{p.criteria.keywords?.join(', ') || 'N/A'}</code></div>
                    <div>Companies: <code>{p.criteria.target_companies?.join(', ') || 'Default'}</code></div>
                  </div>

                  <button
                    onClick={() => handleLaunchDiscovery(p.criteria, p.id)}
                    disabled={isRunning}
                    className="btn btn-primary"
                    style={{ width: '100%', fontSize: '0.8125rem' }}
                  >
                    <Play size={13} />
                    <span>Run This Profile</span>
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* SUB-TAB 4: History */}
      {activeSubTab === 'history' && (
        <div className="card">
          <h3 style={{ fontSize: '1.125rem', fontWeight: 600, marginBottom: '1rem' }}>
            Discovery Run Execution Ledger
          </h3>

          <div style={{ overflowX: 'auto', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Run ID</th>
                  <th>Source</th>
                  <th>Total Discovered</th>
                  <th>Inserted</th>
                  <th>Duplicates</th>
                  <th>Duration</th>
                  <th>Status</th>
                  <th>Timestamp</th>
                </tr>
              </thead>
              <tbody>
                {runs.map((r) => (
                  <tr key={r.run_id}>
                    <td><code>{r.run_id}</code></td>
                    <td><span className="badge badge-gray">{r.source}</span></td>
                    <td style={{ fontWeight: 600, color: '#38bdf8' }}>{r.total_discovered}</td>
                    <td style={{ color: '#34d399' }}>{r.inserted_count}</td>
                    <td style={{ color: '#fbbf24' }}>{r.duplicate_count}</td>
                    <td>{r.duration_ms ? `${r.duration_ms} ms` : 'N/A'}</td>
                    <td>
                      <span className={`badge ${r.status === 'completed' ? 'badge-green' : r.status === 'partial' ? 'badge-purple' : 'badge-red'}`}>
                        {r.status}
                      </span>
                    </td>
                    <td style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                      {new Date(r.created_at).toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Save Profile Modal */}
      {showSaveProfileModal && (
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
          <div className="card" style={{ maxWidth: '480px', width: '100%', backgroundColor: '#0f172a', border: '1px solid #38bdf8' }}>
            <h3 style={{ fontSize: '1.125rem', fontWeight: 700, marginBottom: '1rem' }}>Save Search Profile</h3>
            <form onSubmit={handleSaveProfile} style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              <input
                type="text"
                placeholder="Profile Name (e.g. Senior Distributed Systems SF)"
                value={newProfileName}
                onChange={(e) => setNewProfileName(e.target.value)}
                required
                style={{ width: '100%', padding: '0.5rem', background: '#090d16', border: '1px solid var(--border-color)', borderRadius: '6px', color: '#f8fafc', fontSize: '0.8125rem' }}
              />
              <textarea
                placeholder="Optional description..."
                value={newProfileDesc}
                onChange={(e) => setNewProfileDesc(e.target.value)}
                rows={3}
                style={{ width: '100%', padding: '0.5rem', background: '#090d16', border: '1px solid var(--border-color)', borderRadius: '6px', color: '#f8fafc', fontSize: '0.8125rem' }}
              />
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.5rem', marginTop: '0.5rem' }}>
                <button type="button" onClick={() => setShowSaveProfileModal(false)} className="btn btn-secondary">
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary">
                  Save Profile
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
