import React, { useEffect, useState, useCallback } from 'react';
import { Header } from './components/Header';
import { Sidebar, NavTab } from './components/Sidebar';
import { HealthStatusCard } from './components/HealthStatusCard';
import { CandidateProfileView } from './components/CandidateProfileView';
import { PipelineOverview } from './components/PipelineOverview';
import { SchemaViewer } from './components/SchemaViewer';
import { SystemConfigCard } from './components/SystemConfigCard';
import { ErrorLab } from './components/ErrorLab';
import { api } from './services/api';
import { HealthResponse, SystemConfigResponse, PipelineStageInfo } from './types';
import { Database, Layers, ArrowRight, UserCheck } from 'lucide-react';

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

              {/* Highlights */}
              <div className="grid-3">
                <div className="card card-hover" style={{ cursor: 'pointer' }} onClick={() => setActiveTab('profile')}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.75rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#34d399' }}>
                      <UserCheck size={18} />
                      <h4 style={{ fontWeight: 600, fontSize: '0.9375rem' }}>Candidate Profile & CV</h4>
                    </div>
                    <span className="badge badge-green">Phase 2 Active</span>
                  </div>
                  <p style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)', lineHeight: 1.4 }}>
                    Verified candidate facts, master resume inventory, untrusted raw parser & LLM ground truth boundary.
                  </p>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem', color: '#34d399', fontSize: '0.75rem', marginTop: '1rem', fontWeight: 600 }}>
                    <span>Manage & Verify Profile</span>
                    <ArrowRight size={12} />
                  </div>
                </div>

                <div className="card card-hover" style={{ cursor: 'pointer' }} onClick={() => setActiveTab('pipeline')}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.75rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#38bdf8' }}>
                      <Layers size={18} />
                      <h4 style={{ fontWeight: 600, fontSize: '0.9375rem' }}>Pipeline Architecture</h4>
                    </div>
                    <span className="badge badge-blue">Phase 2 of 6</span>
                  </div>
                  <p style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)', lineHeight: 1.4 }}>
                    End-to-end sequential pipeline status from verified profile to human approval and portal submission.
                  </p>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem', color: '#38bdf8', fontSize: '0.75rem', marginTop: '1rem', fontWeight: 600 }}>
                    <span>Explore Stages</span>
                    <ArrowRight size={12} />
                  </div>
                </div>

                <div className="card card-hover" style={{ cursor: 'pointer' }} onClick={() => setActiveTab('schemas')}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.75rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#c084fc' }}>
                      <Database size={18} />
                      <h4 style={{ fontWeight: 600, fontSize: '0.9375rem' }}>Relational Schema</h4>
                    </div>
                    <span className="badge badge-purple">13 Models Active</span>
                  </div>
                  <p style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)', lineHeight: 1.4 }}>
                    SQLAlchemy 2.0 + SQLite WAL with candidate profile, experiences, educations, skills, projects, and imports.
                  </p>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem', color: '#c084fc', fontSize: '0.75rem', marginTop: '1rem', fontWeight: 600 }}>
                    <span>Inspect Schemas</span>
                    <ArrowRight size={12} />
                  </div>
                </div>
              </div>
            </div>
          )}

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
