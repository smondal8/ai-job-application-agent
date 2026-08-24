import React, { useState, useEffect, useCallback } from 'react';
import {
  Briefcase,
  Search,
  Plus,
  Filter,
  Eye,
  FileText,
  Clock,
  Sparkles,
  ExternalLink,
  Save,
  Check,
  Copy,
  FileCheck,
  X,
  Building,
  MapPin,
  ShieldCheck,
} from 'lucide-react';
import { api } from '../services/api';
import {
  ApplicationItem,
  ApplicationDossier,
  ApplicationStats,
  Job,
} from '../types';

export const ApplicationDashboardView: React.FC = () => {
  const [applications, setApplications] = useState<ApplicationItem[]>([]);
  const [stats, setStats] = useState<ApplicationStats | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [selectedAppId, setSelectedAppId] = useState<number | null>(null);
  const [dossier, setDossier] = useState<ApplicationDossier | null>(null);
  const [loadingDossier, setLoadingDossier] = useState<boolean>(false);

  // Filters
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [portalFilter, setPortalFilter] = useState<string>('all');
  const [searchTerm, setSearchTerm] = useState<string>('');

  // Create Application Modal State
  const [isCreateModalOpen, setIsCreateModalOpen] = useState<boolean>(false);
  const [catalogJobs, setCatalogJobs] = useState<Job[]>([]);
  const [selectedNewJobId, setSelectedNewJobId] = useState<number | null>(null);
  const [newAppPortalType, setNewAppPortalType] = useState<string>('generic');
  const [newAppNotes, setNewAppNotes] = useState<string>('');
  const [isCreating, setIsCreating] = useState<boolean>(false);

  // Dossier Active Tab
  const [dossierTab, setDossierTab] = useState<'job' | 'resume' | 'screening' | 'review'>('job');
  const [docFormat, setDocFormat] = useState<'markdown' | 'cover_letter' | 'text' | 'html' | 'traceability'>('markdown');
  const [copiedKey, setCopiedKey] = useState<string | null>(null);

  // Review Form in Dossier
  const [reviewNoteInput, setReviewNoteInput] = useState<string>('');
  const [isSubmittingReview, setIsSubmittingReview] = useState<boolean>(false);

  // Screening Q&A in Dossier
  const [answersPayloadJson, setAnswersPayloadJson] = useState<string>('{}');
  const [isSavingAnswers, setIsSavingAnswers] = useState<boolean>(false);

  const fetchApplicationsAndStats = useCallback(async () => {
    setLoading(true);
    try {
      const [listData, statsData] = await Promise.all([
        api.getApplications({
          status: statusFilter,
          portal_type: portalFilter,
          search: searchTerm || undefined,
          page: 1,
          page_size: 50,
        }),
        api.getApplicationStats(),
      ]);
      setApplications(listData.items);
      setStats(statsData);
    } catch (err) {
      console.error('Failed to fetch applications:', err);
    } finally {
      setLoading(false);
    }
  }, [statusFilter, portalFilter, searchTerm]);

  useEffect(() => {
    fetchApplicationsAndStats();
  }, [fetchApplicationsAndStats]);

  const loadDossier = async (appId: number) => {
    setSelectedAppId(appId);
    setLoadingDossier(true);
    try {
      const data = await api.getApplicationDossier(appId);
      setDossier(data);
      setAnswersPayloadJson(JSON.stringify(data.application.answers_payload || {}, null, 2));
      setReviewNoteInput(data.application.reviewer_notes || '');
    } catch (err) {
      console.error('Failed to load application dossier:', err);
    } finally {
      setLoadingDossier(false);
    }
  };

  const handleOpenCreateModal = async () => {
    try {
      const jobsRes = await api.getJobs({ page: 1, page_size: 50 });
      setCatalogJobs(jobsRes.items);
      if (jobsRes.items.length > 0) {
        setSelectedNewJobId(jobsRes.items[0].id);
      }
      setIsCreateModalOpen(true);
    } catch (err) {
      console.error('Failed to fetch catalog jobs:', err);
    }
  };

  const handleCreateApplication = async () => {
    if (!selectedNewJobId) return;
    setIsCreating(true);
    try {
      const newApp = await api.createApplication({
        job_id: selectedNewJobId,
        portal_type: newAppPortalType,
        submission_notes: newAppNotes || undefined,
      });
      setIsCreateModalOpen(false);
      setNewAppNotes('');
      await fetchApplicationsAndStats();
      loadDossier(newApp.id);
    } catch (err: any) {
      alert(`Failed to create application: ${err.message}`);
    } finally {
      setIsCreating(false);
    }
  };

  const handleSaveAnswers = async () => {
    if (!dossier) return;
    setIsSavingAnswers(true);
    try {
      let parsed = {};
      try {
        parsed = JSON.parse(answersPayloadJson);
      } catch {
        alert('Invalid JSON in screening answers payload.');
        setIsSavingAnswers(false);
        return;
      }
      await api.updateApplication(dossier.application.id, {
        answers_payload: parsed,
      });
      await loadDossier(dossier.application.id);
      alert('Screening answers saved successfully!');
    } catch (err: any) {
      alert(`Failed to save answers: ${err.message}`);
    } finally {
      setIsSavingAnswers(false);
    }
  };

  const handleAddReviewNote = async () => {
    if (!dossier || !reviewNoteInput.trim()) return;
    setIsSubmittingReview(true);
    try {
      await api.addApplicationReview(dossier.application.id, {
        reviewer_notes: reviewNoteInput,
        decision: 'pending',
      });
      await loadDossier(dossier.application.id);
      await fetchApplicationsAndStats();
      alert('Review note recorded in dossier ledger!');
    } catch (err: any) {
      alert(`Failed to record review: ${err.message}`);
    } finally {
      setIsSubmittingReview(false);
    }
  };

  const handleSwitchResume = async (resumeId: number) => {
    if (!dossier) return;
    try {
      await api.linkResumeToApplication(dossier.application.id, resumeId);
      await loadDossier(dossier.application.id);
      await fetchApplicationsAndStats();
    } catch (err: any) {
      alert(`Failed to link resume: ${err.message}`);
    }
  };

  const handleCopy = (text: string, key: string) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(key);
    setTimeout(() => setCopiedKey(null), 2500);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Top Banner: Phase 7 Subsystem */}
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
            <Briefcase size={24} color="#38bdf8" />
            <h2 style={{ fontSize: '1.25rem', fontWeight: 700 }}>
              Central Application Dashboard & Review Studio
            </h2>
            <span className="badge badge-blue">Phase 7 Active</span>
          </div>
          <p style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
            Unified application management, multi-entity dossier read/review workflows, and job & tailored resume version linking.
          </p>
        </div>

        <button
          onClick={handleOpenCreateModal}
          className="btn btn-primary"
          style={{ fontSize: '0.8125rem', display: 'flex', alignItems: 'center', gap: '0.375rem' }}
        >
          <Plus size={16} />
          <span>New Application</span>
        </button>
      </div>

      {/* Executive Metric Overview */}
      {stats && (
        <div className="grid-4">
          <div className="card">
            <div style={{ fontSize: '0.6875rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>
              Total Applications
            </div>
            <div style={{ fontSize: '1.75rem', fontWeight: 800, color: '#f8fafc', marginTop: '0.25rem' }}>
              {stats.total_applications}
            </div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
              Across all job portals
            </div>
          </div>

          <div className="card">
            <div style={{ fontSize: '0.6875rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>
              Ready for Review
            </div>
            <div style={{ fontSize: '1.75rem', fontWeight: 800, color: '#38bdf8', marginTop: '0.25rem' }}>
              {stats.status_counts.ready_for_review || 0}
            </div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
              Tailored resume linked
            </div>
          </div>

          <div className="card">
            <div style={{ fontSize: '0.6875rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>
              In Review / Staging
            </div>
            <div style={{ fontSize: '1.75rem', fontWeight: 800, color: '#c084fc', marginTop: '0.25rem' }}>
              {(stats.status_counts.in_review || 0) + (stats.status_counts.draft || 0)}
            </div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
              Dossier under evaluation
            </div>
          </div>

          <div className="card">
            <div style={{ fontSize: '0.6875rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>
              Submitted / Completed
            </div>
            <div style={{ fontSize: '1.75rem', fontWeight: 800, color: '#34d399', marginTop: '0.25rem' }}>
              {stats.status_counts.submitted || 0}
            </div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
              Completed portal submissions
            </div>
          </div>
        </div>
      )}

      {/* Filter and Search Bar */}
      <div className="card" style={{ padding: '1rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.75rem' }}>
          {/* Status Tabs */}
          <div style={{ display: 'flex', gap: '0.375rem', flexWrap: 'wrap' }}>
            {['all', 'ready_for_review', 'in_review', 'draft', 'submitted'].map((st) => (
              <button
                key={st}
                onClick={() => setStatusFilter(st)}
                className={`btn ${statusFilter === st ? 'btn-primary' : 'btn-secondary'}`}
                style={{ fontSize: '0.75rem', padding: '0.3rem 0.65rem' }}
              >
                {st.replace(/_/g, ' ').toUpperCase()}
              </button>
            ))}
          </div>

          {/* Search & Portal Filter */}
          <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', flexWrap: 'wrap' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.375rem', background: '#090d16', padding: '0.3rem 0.6rem', borderRadius: '6px', border: '1px solid var(--border-color)' }}>
              <Search size={14} color="var(--text-muted)" />
              <input
                type="text"
                placeholder="Search role or company..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                style={{ background: 'transparent', border: 'none', color: '#f8fafc', fontSize: '0.75rem', outline: 'none', width: '160px' }}
              />
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '0.375rem' }}>
              <Filter size={14} color="var(--text-muted)" />
              <select
                value={portalFilter}
                onChange={(e) => setPortalFilter(e.target.value)}
                style={{ background: '#090d16', border: '1px solid var(--border-color)', borderRadius: '6px', color: '#f8fafc', fontSize: '0.75rem', padding: '0.35rem 0.5rem' }}
              >
                <option value="all">All Portals</option>
                <option value="greenhouse">Greenhouse</option>
                <option value="lever">Lever</option>
                <option value="workday">Workday</option>
                <option value="ashby">Ashby</option>
                <option value="generic">Generic</option>
              </select>
            </div>
          </div>
        </div>
      </div>

      {/* Main Table + Dossier Split Layout */}
      <div style={{ display: 'grid', gridTemplateColumns: selectedAppId ? '1fr 1.3fr' : '1fr', gap: '1.5rem', alignItems: 'start' }}>
        {/* Applications Catalog Table */}
        <div className="card" style={{ padding: '0', overflow: 'hidden' }}>
          <div style={{ padding: '1rem', borderBottom: '1px solid var(--border-color)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h3 style={{ fontSize: '0.9375rem', fontWeight: 700 }}>
              Job Applications ({applications.length})
            </h3>
            {loading && <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Loading...</span>}
          </div>

          <div style={{ overflowX: 'auto' }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Target Position & Company</th>
                  <th>Portal</th>
                  <th>Match Score</th>
                  <th>Status</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {applications.length === 0 ? (
                  <tr>
                    <td colSpan={6} style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>
                      No applications found matching the selected filters. Click "New Application" to create one.
                    </td>
                  </tr>
                ) : (
                  applications.map((app) => {
                    const isSelected = selectedAppId === app.id;
                    return (
                      <tr
                        key={app.id}
                        onClick={() => loadDossier(app.id)}
                        style={{
                          cursor: 'pointer',
                          backgroundColor: isSelected ? 'rgba(56, 189, 248, 0.1)' : 'transparent',
                        }}
                      >
                        <td>
                          <code style={{ color: '#38bdf8' }}>#{app.id}</code>
                        </td>
                        <td>
                          <div>
                            <strong style={{ color: '#f8fafc', fontSize: '0.8125rem' }}>{app.job_title}</strong>
                            <div style={{ fontSize: '0.6875rem', color: 'var(--text-secondary)' }}>
                              {app.job_company} &bull; {app.job_remote_type}
                            </div>
                          </div>
                        </td>
                        <td>
                          <span className="badge badge-gray" style={{ textTransform: 'uppercase', fontSize: '0.625rem' }}>
                            {app.portal_type}
                          </span>
                        </td>
                        <td>
                          {app.fit_score !== null && app.fit_score !== undefined ? (
                            <span
                              className={`badge ${app.fit_score >= 80 ? 'badge-green' : app.fit_score >= 60 ? 'badge-purple' : 'badge-blue'}`}
                              style={{ fontSize: '0.6875rem' }}
                            >
                              {app.fit_score}% {app.recommendation || ''}
                            </span>
                          ) : (
                            <span style={{ fontSize: '0.6875rem', color: 'var(--text-muted)' }}>N/A</span>
                          )}
                        </td>
                        <td>
                          <span
                            className={`badge ${app.status === 'submitted' ? 'badge-green' : app.status === 'ready_for_review' ? 'badge-blue' : app.status === 'in_review' ? 'badge-purple' : 'badge-gray'}`}
                            style={{ fontSize: '0.6875rem', textTransform: 'uppercase' }}
                          >
                            {app.status.replace(/_/g, ' ')}
                          </span>
                        </td>
                        <td>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              loadDossier(app.id);
                            }}
                            className="btn btn-secondary"
                            style={{ fontSize: '0.6875rem', padding: '0.25rem 0.5rem', display: 'flex', alignItems: 'center', gap: '0.25rem' }}
                          >
                            <Eye size={12} />
                            <span>Dossier</span>
                          </button>
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Selected Application Dossier Drawer */}
        {selectedAppId && (
          <div className="card" style={{ borderTop: '4px solid #38bdf8', padding: '1.25rem', position: 'sticky', top: '1rem' }}>
            {loadingDossier ? (
              <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>
                Loading Application Dossier...
              </div>
            ) : dossier ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                {/* Dossier Header */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', borderBottom: '1px solid var(--border-color)', paddingBottom: '0.875rem' }}>
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <h3 style={{ fontSize: '1.125rem', fontWeight: 700 }}>
                        {dossier.job.title}
                      </h3>
                      <span className="badge badge-blue">App #{dossier.application.id}</span>
                    </div>
                    <div style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)', marginTop: '0.25rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <Building size={14} />
                      <span>{dossier.job.company}</span>
                      <span>&bull;</span>
                      <MapPin size={14} />
                      <span>{dossier.job.location || 'Remote'} ({dossier.job.remote_type})</span>
                    </div>
                  </div>

                  <button
                    onClick={() => setSelectedAppId(null)}
                    style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}
                  >
                    <X size={18} />
                  </button>
                </div>

                {/* Dossier Sub-Tabs */}
                <div style={{ display: 'flex', gap: '0.375rem', borderBottom: '1px solid var(--border-color)', paddingBottom: '0.5rem' }}>
                  <button
                    onClick={() => setDossierTab('job')}
                    className={`btn ${dossierTab === 'job' ? 'btn-primary' : 'btn-secondary'}`}
                    style={{ fontSize: '0.75rem', padding: '0.3rem 0.6rem' }}
                  >
                    <Briefcase size={12} />
                    <span>Job & Posting</span>
                  </button>
                  <button
                    onClick={() => setDossierTab('resume')}
                    className={`btn ${dossierTab === 'resume' ? 'btn-primary' : 'btn-secondary'}`}
                    style={{ fontSize: '0.75rem', padding: '0.3rem 0.6rem' }}
                  >
                    <FileText size={12} />
                    <span>Tailored Materials</span>
                  </button>
                  <button
                    onClick={() => setDossierTab('screening')}
                    className={`btn ${dossierTab === 'screening' ? 'btn-primary' : 'btn-secondary'}`}
                    style={{ fontSize: '0.75rem', padding: '0.3rem 0.6rem' }}
                  >
                    <FileCheck size={12} />
                    <span>Screening Q&A</span>
                  </button>
                  <button
                    onClick={() => setDossierTab('review')}
                    className={`btn ${dossierTab === 'review' ? 'btn-primary' : 'btn-secondary'}`}
                    style={{ fontSize: '0.75rem', padding: '0.3rem 0.6rem' }}
                  >
                    <Clock size={12} />
                    <span>Review Ledger</span>
                  </button>
                </div>

                {/* TAB 1: Job Details & Portal Context */}
                {dossierTab === 'job' && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                    {/* Key Attributes */}
                    <div className="grid-3" style={{ background: '#090d16', padding: '0.75rem', borderRadius: '6px', border: '1px solid var(--border-color)' }}>
                      <div>
                        <div style={{ fontSize: '0.625rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>Portal Type</div>
                        <div style={{ fontSize: '0.8125rem', fontWeight: 700, color: '#38bdf8', marginTop: '0.125rem', textTransform: 'uppercase' }}>
                          {dossier.application.portal_type}
                        </div>
                      </div>
                      <div>
                        <div style={{ fontSize: '0.625rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>Match Fit</div>
                        <div style={{ fontSize: '0.8125rem', fontWeight: 700, color: '#34d399', marginTop: '0.125rem' }}>
                          {dossier.analysis ? `${dossier.analysis.fit_score}% (${dossier.analysis.fit_level})` : 'Not Analyzed'}
                        </div>
                      </div>
                      <div>
                        <div style={{ fontSize: '0.625rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>Candidate Profile</div>
                        <div style={{ fontSize: '0.8125rem', fontWeight: 700, color: '#f8fafc', marginTop: '0.125rem' }}>
                          {dossier.candidate?.full_name || 'Primary Profile'}
                        </div>
                      </div>
                    </div>

                    {/* External Portal Link */}
                    {dossier.application.portal_url && (
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', background: 'rgba(56, 189, 248, 0.08)', padding: '0.625rem 0.875rem', borderRadius: '6px', border: '1px solid rgba(56, 189, 248, 0.2)' }}>
                        <div style={{ fontSize: '0.75rem', color: '#38bdf8', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: '340px' }}>
                          {dossier.application.portal_url}
                        </div>
                        <a
                          href={dossier.application.portal_url}
                          target="_blank"
                          rel="noreferrer"
                          className="btn btn-secondary"
                          style={{ fontSize: '0.6875rem', padding: '0.2rem 0.5rem', display: 'flex', alignItems: 'center', gap: '0.25rem', textDecoration: 'none' }}
                        >
                          <span>Open Portal</span>
                          <ExternalLink size={11} />
                        </a>
                      </div>
                    )}

                    {/* Job Description Summary */}
                    <div>
                      <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '0.375rem', textTransform: 'uppercase' }}>
                        Job Description
                      </div>
                      <div
                        style={{
                          background: '#090d16',
                          padding: '0.875rem',
                          borderRadius: '6px',
                          border: '1px solid var(--border-color)',
                          fontSize: '0.75rem',
                          lineHeight: 1.5,
                          maxHeight: '260px',
                          overflowY: 'auto',
                          color: 'var(--text-secondary)',
                          whiteSpace: 'pre-wrap',
                        }}
                      >
                        {dossier.job.description_clean || dossier.job.description_raw || 'No description text recorded.'}
                      </div>
                    </div>
                  </div>
                )}

                {/* TAB 2: Tailored Materials & Fact Attribution */}
                {dossierTab === 'resume' && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                    {/* Resume Version Switcher */}
                    {dossier.available_resumes.length > 0 && (
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', background: '#090d16', padding: '0.5rem 0.75rem', borderRadius: '6px', border: '1px solid var(--border-color)' }}>
                        <label style={{ fontSize: '0.6875rem', color: 'var(--text-muted)', fontWeight: 600 }}>Linked Resume Version:</label>
                        <select
                          value={dossier.tailored_resume?.id || ''}
                          onChange={(e) => handleSwitchResume(parseInt(e.target.value, 10))}
                          style={{ background: '#131b2e', border: '1px solid var(--border-color)', borderRadius: '4px', color: '#f8fafc', fontSize: '0.75rem', padding: '0.25rem 0.5rem' }}
                        >
                          {dossier.available_resumes.map((r) => (
                            <option key={r.id} value={r.id}>
                              Resume #{r.id} ({r.prompt_version} &bull; {r.validation_status})
                            </option>
                          ))}
                        </select>
                      </div>
                    )}

                    {dossier.tailored_resume ? (
                      <div>
                        {/* Format Switcher */}
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                          <div style={{ display: 'flex', gap: '0.25rem' }}>
                            <button
                              onClick={() => setDocFormat('markdown')}
                              className={`btn ${docFormat === 'markdown' ? 'btn-primary' : 'btn-secondary'}`}
                              style={{ fontSize: '0.6875rem', padding: '0.2rem 0.5rem' }}
                            >
                              Markdown
                            </button>
                            <button
                              onClick={() => setDocFormat('cover_letter')}
                              className={`btn ${docFormat === 'cover_letter' ? 'btn-primary' : 'btn-secondary'}`}
                              style={{ fontSize: '0.6875rem', padding: '0.2rem 0.5rem' }}
                            >
                              Cover Letter
                            </button>
                            <button
                              onClick={() => setDocFormat('text')}
                              className={`btn ${docFormat === 'text' ? 'btn-primary' : 'btn-secondary'}`}
                              style={{ fontSize: '0.6875rem', padding: '0.2rem 0.5rem' }}
                            >
                              Text
                            </button>
                            <button
                              onClick={() => setDocFormat('traceability')}
                              className={`btn ${docFormat === 'traceability' ? 'btn-primary' : 'btn-secondary'}`}
                              style={{ fontSize: '0.6875rem', padding: '0.2rem 0.5rem' }}
                            >
                              Fact Matrix
                            </button>
                          </div>

                          <div style={{ display: 'flex', gap: '0.25rem' }}>
                            <button
                              onClick={() => {
                                const text = docFormat === 'cover_letter' ? dossier.tailored_resume?.cover_letter : dossier.tailored_resume?.compiled_markdown;
                                handleCopy(text || '', 'dossier_doc');
                              }}
                              className="btn btn-secondary"
                              style={{ fontSize: '0.6875rem', padding: '0.2rem 0.5rem' }}
                            >
                              {copiedKey === 'dossier_doc' ? <Check size={11} color="#34d399" /> : <Copy size={11} />}
                              <span>{copiedKey === 'dossier_doc' ? 'Copied' : 'Copy'}</span>
                            </button>
                          </div>
                        </div>

                        {/* Document Content */}
                        {docFormat === 'markdown' && (
                          <pre className="code-block" style={{ maxHeight: '300px', fontSize: '0.75rem', lineHeight: 1.4 }}>
                            {dossier.tailored_resume.compiled_markdown}
                          </pre>
                        )}
                        {docFormat === 'cover_letter' && (
                          <div style={{ background: '#090d16', padding: '1rem', borderRadius: '6px', border: '1px solid var(--border-color)', fontSize: '0.75rem', lineHeight: 1.6, maxHeight: '300px', overflowY: 'auto', whiteSpace: 'pre-wrap' }}>
                            {dossier.tailored_resume.cover_letter}
                          </div>
                        )}
                        {docFormat === 'text' && (
                          <pre className="code-block" style={{ maxHeight: '300px', fontSize: '0.6875rem', lineHeight: 1.3 }}>
                            {dossier.tailored_resume.compiled_text}
                          </pre>
                        )}
                        {docFormat === 'traceability' && (
                          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', maxHeight: '300px', overflowY: 'auto' }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.375rem', fontSize: '0.75rem', color: '#34d399' }}>
                              <ShieldCheck size={14} />
                              <span>Validation: {dossier.tailored_resume.validation_status.toUpperCase()} ({dossier.tailored_resume.validation_details?.traceability_score || 100}% Traceable)</span>
                            </div>
                            {dossier.tailored_resume.traceability_matrix && Object.entries(dossier.tailored_resume.traceability_matrix).map(([fid, claims], i) => (
                              <div key={i} style={{ background: '#090d16', padding: '0.5rem', borderRadius: '4px', border: '1px solid var(--border-color)', fontSize: '0.6875rem' }}>
                                <code style={{ color: '#38bdf8' }}>{fid}</code>
                                <ul style={{ listStylePosition: 'inside', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
                                  {claims.map((c, ci) => (
                                    <li key={ci}>{c}</li>
                                  ))}
                                </ul>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    ) : (
                      <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)', fontSize: '0.8125rem' }}>
                        No tailored resume version linked yet. Navigate to Phase 6 Studio to tailor a resume.
                      </div>
                    )}
                  </div>
                )}

                {/* TAB 3: Screening Questions Q&A */}
                {dossierTab === 'screening' && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                      JSON key-value payload for portal application questions (e.g. sponsorship, notice period, portfolio):
                    </div>
                    <textarea
                      value={answersPayloadJson}
                      onChange={(e) => setAnswersPayloadJson(e.target.value)}
                      rows={8}
                      style={{
                        width: '100%',
                        background: '#090d16',
                        border: '1px solid var(--border-color)',
                        borderRadius: '6px',
                        color: '#f8fafc',
                        fontFamily: 'monospace',
                        fontSize: '0.75rem',
                        padding: '0.625rem',
                      }}
                    />
                    <button
                      onClick={handleSaveAnswers}
                      disabled={isSavingAnswers}
                      className="btn btn-primary"
                      style={{ alignSelf: 'flex-end', fontSize: '0.75rem', padding: '0.35rem 0.75rem', display: 'flex', alignItems: 'center', gap: '0.25rem' }}
                    >
                      <Save size={13} />
                      <span>{isSavingAnswers ? 'Saving...' : 'Save Screening Answers'}</span>
                    </button>
                  </div>
                )}

                {/* TAB 4: Review Ledger & Notes Workflow */}
                {dossierTab === 'review' && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                    {/* Phase 8 State Machine Placeholder Callout */}
                    <div style={{ background: 'rgba(192, 132, 252, 0.08)', padding: '0.75rem', borderRadius: '6px', border: '1px solid rgba(192, 132, 252, 0.3)' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.375rem', fontSize: '0.75rem', fontWeight: 600, color: '#c084fc', marginBottom: '0.25rem' }}>
                        <Sparkles size={14} />
                        <span>Phase 8 State Machine Boundary</span>
                      </div>
                      <p style={{ fontSize: '0.6875rem', color: 'var(--text-secondary)', lineHeight: 1.4 }}>
                        Application review notes and dossiers are logged here. Final approval transitions and browser submission staging are governed by Phase 8.
                      </p>
                    </div>

                    {/* Add Review Note Form */}
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                      <label style={{ fontSize: '0.6875rem', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase' }}>
                        Add Review Note / Assessment:
                      </label>
                      <textarea
                        value={reviewNoteInput}
                        onChange={(e) => setReviewNoteInput(e.target.value)}
                        placeholder="e.g. Profile alignment verified against Spotify requirements. Cover letter customized."
                        rows={3}
                        style={{
                          width: '100%',
                          background: '#090d16',
                          border: '1px solid var(--border-color)',
                          borderRadius: '6px',
                          color: '#f8fafc',
                          fontSize: '0.75rem',
                          padding: '0.5rem',
                        }}
                      />
                      <button
                        onClick={handleAddReviewNote}
                        disabled={isSubmittingReview || !reviewNoteInput.trim()}
                        className="btn btn-primary"
                        style={{ alignSelf: 'flex-end', fontSize: '0.75rem', padding: '0.35rem 0.75rem' }}
                      >
                        {isSubmittingReview ? 'Recording...' : 'Record Review Note'}
                      </button>
                    </div>

                    {/* Review History Timeline */}
                    <div>
                      <div style={{ fontSize: '0.6875rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '0.375rem' }}>
                        Review History ({dossier.reviews.length})
                      </div>
                      {dossier.reviews.length === 0 ? (
                        <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>No review notes recorded yet.</p>
                      ) : (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                          {dossier.reviews.map((rev) => (
                            <div key={rev.id} style={{ background: '#090d16', padding: '0.625rem', borderRadius: '4px', border: '1px solid var(--border-color)' }}>
                              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.6875rem', color: 'var(--text-muted)', marginBottom: '0.25rem' }}>
                                <span className="badge badge-purple">{rev.decision}</span>
                                <span>{rev.created_at ? new Date(rev.created_at).toLocaleDateString() : ''}</span>
                              </div>
                              <p style={{ fontSize: '0.75rem', color: '#f8fafc' }}>{rev.reviewer_notes}</p>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            ) : null}
          </div>
        )}
      </div>

      {/* Modal: Create Application */}
      {isCreateModalOpen && (
        <div
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.75)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
            padding: '1rem',
          }}
        >
          <div
            className="card"
            style={{
              width: '100%',
              maxWidth: '520px',
              backgroundColor: '#0f172a',
              border: '1px solid var(--border-color)',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Plus size={20} color="#38bdf8" />
                <h3 style={{ fontSize: '1.125rem', fontWeight: 700 }}>New Application Entry</h3>
              </div>
              <button
                onClick={() => setIsCreateModalOpen(false)}
                style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}
              >
                <X size={18} />
              </button>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div>
                <label style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)', display: 'block', marginBottom: '0.375rem' }}>
                  Target Job Position:
                </label>
                <select
                  value={selectedNewJobId || ''}
                  onChange={(e) => setSelectedNewJobId(parseInt(e.target.value, 10))}
                  style={{
                    width: '100%',
                    padding: '0.5rem',
                    background: '#090d16',
                    border: '1px solid var(--border-color)',
                    borderRadius: '6px',
                    color: '#f8fafc',
                    fontSize: '0.8125rem',
                  }}
                >
                  {catalogJobs.map((j) => (
                    <option key={j.id} value={j.id}>
                      #{j.id} — {j.title} at {j.company} ({j.remote_type || 'unspecified'})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)', display: 'block', marginBottom: '0.375rem' }}>
                  Portal Type:
                </label>
                <select
                  value={newAppPortalType}
                  onChange={(e) => setNewAppPortalType(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '0.5rem',
                    background: '#090d16',
                    border: '1px solid var(--border-color)',
                    borderRadius: '6px',
                    color: '#f8fafc',
                    fontSize: '0.8125rem',
                  }}
                >
                  <option value="generic">Generic Portal</option>
                  <option value="greenhouse">Greenhouse</option>
                  <option value="lever">Lever</option>
                  <option value="workday">Workday</option>
                  <option value="ashby">Ashby</option>
                </select>
              </div>

              <div>
                <label style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)', display: 'block', marginBottom: '0.375rem' }}>
                  Initial Submission Notes (Optional):
                </label>
                <textarea
                  value={newAppNotes}
                  onChange={(e) => setNewAppNotes(e.target.value)}
                  placeholder="e.g. Sourced via Greenhouse discovery feed. Referral from engineering lead."
                  rows={3}
                  style={{
                    width: '100%',
                    padding: '0.5rem',
                    background: '#090d16',
                    border: '1px solid var(--border-color)',
                    borderRadius: '6px',
                    color: '#f8fafc',
                    fontSize: '0.8125rem',
                  }}
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.5rem', marginTop: '0.5rem' }}>
                <button
                  onClick={() => setIsCreateModalOpen(false)}
                  className="btn btn-secondary"
                  style={{ fontSize: '0.8125rem' }}
                >
                  Cancel
                </button>
                <button
                  onClick={handleCreateApplication}
                  disabled={isCreating || !selectedNewJobId}
                  className="btn btn-primary"
                  style={{ fontSize: '0.8125rem' }}
                >
                  {isCreating ? 'Creating Application...' : 'Create Application'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
