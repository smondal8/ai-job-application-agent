import React, { useEffect, useState, useCallback } from 'react';
import { Header } from './components/Header';
import { Sidebar, NavTab } from './components/Sidebar';
import { HealthStatusCard } from './components/HealthStatusCard';
import { ApplicationDashboardView } from './components/ApplicationDashboardView';
import { ResumeTailoringStudioView } from './components/ResumeTailoringStudioView';
import { JDAnalysisView } from './components/JDAnalysisView';
import { JobDiscoveryView } from './components/JobDiscoveryView';
import { JobDatabaseView } from './components/JobDatabaseView';
import { CandidateProfileView } from './components/CandidateProfileView';
import { PipelineOverview } from './components/PipelineOverview';
import { SchemaViewer } from './components/SchemaViewer';
import { SystemConfigCard } from './components/SystemConfigCard';
import { ErrorLab } from './components/ErrorLab';
import { SystemObservabilityView } from './components/SystemObservabilityView';
import { api } from './services/api';
import { HealthResponse, SystemConfigResponse, PipelineStageInfo } from './types';
import { ArrowRight, Briefcase, Brain, FileText, Activity } from 'lucide-react';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<NavTab>('overview');
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [config, setConfig] = useState<SystemConfigResponse | null>(null);
  const [pipelineStages, setPipelineStages] = useState<PipelineStageInfo[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const [selectedJobIdForTailoring, setSelectedJobIdForTailoring] = useState<number | undefined>(undefined);

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
              <div className="grid-4">
                <div className="card card-hover" style={{ cursor: 'pointer' }} onClick={() => setActiveTab('observability')}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.75rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#34d399' }}>
                      <Activity size={18} />
                      <h4 style={{ fontWeight: 600, fontSize: '0.9375rem' }}>Observability & Backups</h4>
                    </div>
                    <span className="badge badge-green">Phase 11 Active</span>
                  </div>
                  <p style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)', lineHeight: 1.4 }}>
                    Live operation latencies, sensitive data redaction lab, orphan crash recovery, and encrypted backup/restore.
                  </p>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem', color: '#34d399', fontSize: '0.75rem', marginTop: '1rem', fontWeight: 600 }}>
                    <span>Open Observability</span>
                    <ArrowRight size={12} />
                  </div>
                </div>

                <div className="card card-hover" style={{ cursor: 'pointer' }} onClick={() => setActiveTab('applications')}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.75rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#38bdf8' }}>
                      <Briefcase size={18} />
                      <h4 style={{ fontWeight: 600, fontSize: '0.9375rem' }}>Applications & Staging</h4>
                    </div>
                    <span className="badge badge-blue">Phases 7–10 Active</span>
                  </div>
                  <p style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)', lineHeight: 1.4 }}>
                    Application reviews (Phase 7), approval gate (Phase 8), browser prep (Phase 9), and portal adapters (Phase 10).
                  </p>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem', color: '#38bdf8', fontSize: '0.75rem', marginTop: '1rem', fontWeight: 600 }}>
                    <span>Open Dashboard</span>
                    <ArrowRight size={12} />
                  </div>
                </div>

                <div className="card card-hover" style={{ cursor: 'pointer' }} onClick={() => setActiveTab('tailoring')}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.75rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#34d399' }}>
                      <FileText size={18} />
                      <h4 style={{ fontWeight: 600, fontSize: '0.9375rem' }}>Resume Tailoring</h4>
                    </div>
                    <span className="badge badge-green">Phase 6 Active</span>
                  </div>
                  <p style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)', lineHeight: 1.4 }}>
                    Grounded tailoring with atomic fact traceability (<code>source_fact_ids</code>) and deterministic document compiler.
                  </p>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem', color: '#34d399', fontSize: '0.75rem', marginTop: '1rem', fontWeight: 600 }}>
                    <span>Open Tailoring Studio</span>
                    <ArrowRight size={12} />
                  </div>
                </div>

                <div className="card card-hover" style={{ cursor: 'pointer' }} onClick={() => setActiveTab('analysis')}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.75rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#c084fc' }}>
                      <Brain size={18} />
                      <h4 style={{ fontWeight: 600, fontSize: '0.9375rem' }}>JD Analysis & Matching</h4>
                    </div>
                    <span className="badge badge-purple">Phase 5 Active</span>
                  </div>
                  <p style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)', lineHeight: 1.4 }}>
                    Local Ollama LLM (qwen3:8b) for untrusted JD analysis, deterministic + semantic matching, and fit scoring.
                  </p>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem', color: '#c084fc', fontSize: '0.75rem', marginTop: '1rem', fontWeight: 600 }}>
                    <span>Open Match Studio</span>
                    <ArrowRight size={12} />
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'observability' && <SystemObservabilityView />}
          {activeTab === 'applications' && <ApplicationDashboardView />}
          {activeTab === 'tailoring' && <ResumeTailoringStudioView initialJobId={selectedJobIdForTailoring} />}
          {activeTab === 'analysis' && (
            <JDAnalysisView
              onNavigateToTailoring={(jobId) => {
                setSelectedJobIdForTailoring(jobId);
                setActiveTab('tailoring');
              }}
            />
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
