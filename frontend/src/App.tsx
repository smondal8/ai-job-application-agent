import React, { useEffect, useState, useCallback } from 'react';
import { Header } from './components/Header';
import { Sidebar, NavTab } from './components/Sidebar';
import { HealthStatusCard } from './components/HealthStatusCard';
import { JobDiscoveryView } from './components/JobDiscoveryView';
import { JobDatabaseView } from './components/JobDatabaseView';
import { CandidateProfileView } from './components/CandidateProfileView';
import { PipelineOverview } from './components/PipelineOverview';
import { SchemaViewer } from './components/SchemaViewer';
import { SystemConfigCard } from './components/SystemConfigCard';
import { ErrorLab } from './components/ErrorLab';
import { api } from './services/api';
import { HealthResponse, SystemConfigResponse, PipelineStageInfo } from './types';
import { ArrowRight, UserCheck, Briefcase, Compass } from 'lucide-react';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<NavTab>('overview');
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [config, setConfig] = useState<SystemConfigResponse | null>(null);
  const [pipelineStages, setPipelineStages] = useState<PipelineStageInfo[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchInitialData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [healthData, configData, stagesData] = await Promise.all([
        api.getHealth(),
        api.getConfig(),
        api.getPipelineStages(),
      ]);
      setHealth(healthData);
      setConfig(configData);
      setPipelineStages(stagesData);
    } catch (err: any) {
      console.error('Failed fetching data:', err);
      setError(err.message || 'Unable to connect to backend server.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchInitialData();
    const interval = setInterval(async () => {
      try {
        const healthData = await api.getHealth();
        setHealth(healthData);
        setError(null);
      } catch (err: any) {
        // preserve display on temporary glitch
      }
    }, 20000);

    return () => clearInterval(interval);
  }, [fetchInitialData]);

  return (
    <div className="app-container">
      <Sidebar activeTab={activeTab} onSelectTab={setActiveTab} />

      <div className="main-content">
        <Header health={health} loading={loading} onRefresh={fetchInitialData} />

        <main className="content-body">
          {activeTab === 'overview' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
              <HealthStatusCard health={health} loading={loading} error={error} />

              {/* Highlights Grid */}
              <div className="grid-3">
                <div className="card card-hover" style={{ cursor: 'pointer' }} onClick={() => setActiveTab('discovery')}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.75rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#38bdf8' }}>
                      <Compass size={18} />
                      <h4 style={{ fontWeight: 600, fontSize: '0.9375rem' }}>Job Discovery & Feeds</h4>
                    </div>
                    <span className="badge badge-blue">Phase 4 Active</span>
                  </div>
                  <p style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)', lineHeight: 1.4 }}>
                    Source-agnostic adapter framework with Greenhouse, Lever, and remote feeds plus safe manual fallbacks.
                  </p>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem', color: '#38bdf8', fontSize: '0.75rem', marginTop: '1rem', fontWeight: 600 }}>
                    <span>Launch Discovery</span>
                    <ArrowRight size={12} />
                  </div>
                </div>

                <div className="card card-hover" style={{ cursor: 'pointer' }} onClick={() => setActiveTab('jobs')}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.75rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#34d399' }}>
                      <Briefcase size={18} />
                      <h4 style={{ fontWeight: 600, fontSize: '0.9375rem' }}>Job DB & Ingestion</h4>
                    </div>
                    <span className="badge badge-green">Phase 3 Active</span>
                  </div>
                  <p style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)', lineHeight: 1.4 }}>
                    Normalized job catalog, JSON/CSV ingestion fixtures, and deterministic conservative deduplication.
                  </p>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem', color: '#34d399', fontSize: '0.75rem', marginTop: '1rem', fontWeight: 600 }}>
                    <span>Open Job Catalog</span>
                    <ArrowRight size={12} />
                  </div>
                </div>

                <div className="card card-hover" style={{ cursor: 'pointer' }} onClick={() => setActiveTab('profile')}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.75rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#c084fc' }}>
                      <UserCheck size={18} />
                      <h4 style={{ fontWeight: 600, fontSize: '0.9375rem' }}>Candidate Profile & CV</h4>
                    </div>
                    <span className="badge badge-purple">Phase 2 Active</span>
                  </div>
                  <p style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)', lineHeight: 1.4 }}>
                    Verified candidate facts, master resume inventory, and authoritative LLM ground truth context boundary.
                  </p>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem', color: '#c084fc', fontSize: '0.75rem', marginTop: '1rem', fontWeight: 600 }}>
                    <span>Manage Profile</span>
                    <ArrowRight size={12} />
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'discovery' && <JobDiscoveryView />}
          {activeTab === 'jobs' && <JobDatabaseView />}
          {activeTab === 'profile' && <CandidateProfileView />}
          {activeTab === 'pipeline' && <PipelineOverview stages={pipelineStages} />}
          {activeTab === 'schemas' && <SchemaViewer />}
          {activeTab === 'config' && <SystemConfigCard config={config} />}
          {activeTab === 'error-lab' && <ErrorLab />}
        </main>
      </div>
    </div>
  );
};
