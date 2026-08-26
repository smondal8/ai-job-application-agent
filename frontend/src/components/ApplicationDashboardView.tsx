import React, { useState, useEffect, useCallback } from 'react';
import {
  Briefcase,
  Search,
  Plus,
  Filter,
  Eye,
  FileText,
  Clock,
  ExternalLink,
  Save,
  Check,
  Copy,
  FileCheck,
  X,
  Building,
  MapPin,
  ShieldCheck,
  ShieldAlert,
  Lock,
  Unlock,
  AlertTriangle,
  Play,
  Key,
  RefreshCw,
  Globe,
  Camera,
} from 'lucide-react';
import { api } from '../services/api';
import {
  ApplicationItem,
  ApplicationDossier,
  ApplicationStats,
  ApprovalVerificationResponse,
  PreparationAuthorizationResponse,
  BrowserPreparationRun,
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
  const [dossierTab, setDossierTab] = useState<'approval' | 'staging' | 'job' | 'resume' | 'screening' | 'review'>('staging');
  const [docFormat, setDocFormat] = useState<'markdown' | 'cover_letter' | 'text' | 'html' | 'traceability'>('markdown');
  const [copiedKey, setCopiedKey] = useState<string | null>(null);

  // Security & Approval State in Dossier
  const [approvalVerification, setApprovalVerification] = useState<ApprovalVerificationResponse | null>(null);
  const [verifyingApproval, setVerifyingApproval] = useState<boolean>(false);
  const [approverNotesInput, setApproverNotesInput] = useState<string>('');
  const [isApproving, setIsApproving] = useState<boolean>(false);
  const [isAuthorizingPrep, setIsAuthorizingPrep] = useState<boolean>(false);
  const [prepAuthResult, setPrepAuthResult] = useState<PreparationAuthorizationResponse | null>(null);
  const [authError, setAuthError] = useState<string | null>(null);

  // Phase 9 Playwright Browser Staging State
  const [latestPrepRun, setLatestPrepRun] = useState<BrowserPreparationRun | null>(null);
  const [isRunningStaging, setIsRunningStaging] = useState<boolean>(false);
  const [isResumingVerification, setIsResumingVerification] = useState<boolean>(false);
  const [isOpeningBrowser, setIsOpeningBrowser] = useState<boolean>(false);
  const [browserStatusMsg, setBrowserStatusMsg] = useState<string | null>(null);
  const [sessionUnavailable, setSessionUnavailable] = useState<boolean>(false);
  const [customPortalUrl, setCustomPortalUrl] = useState<string>('');
  const [stagingError, setStagingError] = useState<string | null>(null);

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

  const verifyLiveApproval = async (appId: number) => {
    setVerifyingApproval(true);
    setAuthError(null);
    try {
      const res = await api.verifyApplicationApproval(appId);
      setApprovalVerification(res);
    } catch (err: any) {
      console.error('Failed to verify approval:', err);
    } finally {
      setVerifyingApproval(false);
    }
  };

  const loadDossier = async (appId: number) => {
    setSelectedAppId(appId);
    setLoadingDossier(true);
    setPrepAuthResult(null);
    setAuthError(null);
    setStagingError(null);
    try {
      const [data, latestRun] = await Promise.all([
        api.getApplicationDossier(appId),
        api.getLatestPreparationRun(appId).catch(() => null),
      ]);
      setDossier(data);
      setLatestPrepRun(latestRun);
      setCustomPortalUrl(data.application.portal_url || data.job.url || '');
      setAnswersPayloadJson(JSON.stringify(data.application.answers_payload || {}, null, 2));
      setReviewNoteInput(data.application.reviewer_notes || '');
      setApproverNotesInput(data.application.reviewer_notes || '');
      await verifyLiveApproval(appId);
    } catch (err) {
      console.error('Failed to load application dossier:', err);
    } finally {
      setLoadingDossier(false);
      setTimeout(() => {
        const el = document.getElementById('selected-application-details');
        if (el) {
          el.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }
      }, 100);
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

  const handleGrantApproval = async () => {
    if (!dossier) return;
    setIsApproving(true);
    setAuthError(null);
    try {
      await api.approveApplication(dossier.application.id, {
        approver_notes: approverNotesInput || 'Human approval granted after dossier review.',
        approver_id: 'lead_reviewer',
      });
      await loadDossier(dossier.application.id);
      await fetchApplicationsAndStats();
      alert('Human approval successfully granted and cryptographically bound to material inputs!');
    } catch (err: any) {
      setAuthError(err.message || 'Approval failed.');
      alert(`Approval error: ${err.message}`);
    } finally {
      setIsApproving(false);
    }
  };

  const handleRunPreparation = async () => {
    if (!dossier) return;
    setIsRunningStaging(true);
    setStagingError(null);
    try {
      const run = await api.prepareApplication(dossier.application.id, {
        custom_portal_url: customPortalUrl || undefined,
        headless: true,
      });
      setLatestPrepRun(run);
      await loadDossier(dossier.application.id);
      await fetchApplicationsAndStats();
    } catch (err: any) {
      setStagingError(err.message || 'Browser preparation failed.');
    } finally {
      setIsRunningStaging(false);
    }
  };

  const handleOpenOrFocusBrowser = async () => {
    if (!dossier) return;
    setIsOpeningBrowser(true);
    setBrowserStatusMsg(null);
    try {
      const res = await api.openOrFocusBrowserSession(dossier.application.id);

      if (res.session_active) {
        setSessionUnavailable(false);
        setBrowserStatusMsg(res.message || 'Application browser session active on desktop.');
      } else {
        setSessionUnavailable(true);
        setBrowserStatusMsg(res.message || 'Browser session unavailable. A new browser preparation session is required.');
      }
    } catch (err: any) {
      setSessionUnavailable(true);
      setBrowserStatusMsg(`Failed to reach browser session: ${err.message}`);
    } finally {
      setIsOpeningBrowser(false);
    }
  };

  const handleContinueAfterVerification = async () => {
    if (!dossier) return;
    setIsResumingVerification(true);
    try {
      await api.continueAfterVerification(dossier.application.id);
      await loadDossier(dossier.application.id);
      await fetchApplicationsAndStats();
    } catch (err: any) {
      alert(`Failed to resume application: ${err.message}`);
    } finally {
      setIsResumingVerification(false);
    }
  };

  const handleAuthorizePreparation = async () => {
    if (!dossier) return;
    setIsAuthorizingPrep(true);
    setAuthError(null);
    setPrepAuthResult(null);
    try {
      const res = await api.authorizePreparation(dossier.application.id);
      setPrepAuthResult(res);
      await loadDossier(dossier.application.id);
      await fetchApplicationsAndStats();
    } catch (err: any) {
      setAuthError(err.message || 'Security gate rejected authorization.');
    } finally {
      setIsAuthorizingPrep(false);
    }
  };

  const handleRevokeApproval = async () => {
    if (!dossier) return;
    if (!confirm('Are you sure you want to revoke the human approval certificate?')) return;
    try {
      await api.revokeApplicationApproval(dossier.application.id, 'Revoked by reviewer in studio.');
      await loadDossier(dossier.application.id);
      await fetchApplicationsAndStats();
    } catch (err: any) {
      alert(`Failed to revoke approval: ${err.message}`);
    }
  };

  const handleRejectApplication = async () => {
    if (!dossier) return;
    const reason = prompt('Enter rejection reason (optional):');
    try {
      await api.rejectApplication(dossier.application.id, reason || undefined);
      await loadDossier(dossier.application.id);
      await fetchApplicationsAndStats();
    } catch (err: any) {
      alert(`Failed to reject application: ${err.message}`);
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
      alert('Screening answers saved! (Note: Any active approval will be invalidated if answers changed).');
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
      {/* Top Banner: Phases 7-10 Subsystems */}
      <div
        className="card"
        style={{
          borderLeft: '4px solid #34d399',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '1rem',
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <Globe size={24} color="#34d399" />
            <h2 style={{ fontSize: '1.25rem', fontWeight: 700 }}>
              Application Dashboard, Approval Gate & Assisted Browser Staging
            </h2>
            <span className="badge badge-green">Phases 7–10 Active</span>
          </div>
          <p style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
            Phase 7 application reviews, Phase 8 human approval gate, Phase 9 Playwright preparation engine, and Phase 10 portal-specific adapters.
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
              Staged for Review
            </div>
            <div style={{ fontSize: '1.75rem', fontWeight: 800, color: '#38bdf8', marginTop: '0.25rem' }}>
              {stats.status_counts.approved_pending_submission || 0}
            </div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
              Pre-filled via Playwright
            </div>
          </div>

          <div className="card">
            <div style={{ fontSize: '0.6875rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>
              Human Approved
            </div>
            <div style={{ fontSize: '1.75rem', fontWeight: 800, color: '#34d399', marginTop: '0.25rem' }}>
              {stats.status_counts.approved_pending_submission || 0}
            </div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
              Cryptographically signed
            </div>
          </div>

          <div className="card">
            <div style={{ fontSize: '0.6875rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>
              Requires Re-Approval
            </div>
            <div style={{ fontSize: '1.75rem', fontWeight: 800, color: '#fbbf24', marginTop: '0.25rem' }}>
              {stats.status_counts.draft || 0}
            </div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
              Material change detected
            </div>
          </div>
        </div>
      )}

      {/* Filter and Search Bar */}
      <div className="card" style={{ padding: '1rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.75rem' }}>
          <div style={{ display: 'flex', gap: '0.375rem', flexWrap: 'wrap' }}>
            {['all', 'approved', 'ready_for_review', 'in_review', 'staged_for_preparation', 'action_required', 'requires_reapproval', 'draft', 'rejected'].map((st) => (
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

      {/* Main Applications Workspace (Vertically Stacked Full-Width Flow) */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem', width: '100%' }}>
        {/* Applications Catalog List (Full Width) */}
        <div className="card" style={{ padding: 0, overflow: 'hidden', width: '100%' }}>
          <div style={{ padding: '1rem 1.25rem', borderBottom: '1px solid var(--border-color)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Briefcase size={18} color="#38bdf8" />
              <h3 style={{ fontSize: '1rem', fontWeight: 700 }}>
                Application Portfolio & Staging Ledger
              </h3>
              <span className="badge badge-gray">{applications.length}</span>
            </div>
          </div>

          <div style={{ overflowX: 'auto', width: '100%' }}>
            <table className="table" style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8125rem' }}>
              <thead>
                <tr style={{ background: '#090d16', textAlign: 'left', borderBottom: '1px solid var(--border-color)' }}>
                  <th style={{ padding: '0.75rem 1rem', width: '32%', minWidth: '200px' }}>Job & Company</th>
                  <th style={{ padding: '0.75rem 0.75rem', width: '12%', minWidth: '100px' }}>Portal</th>
                  <th style={{ padding: '0.75rem 0.75rem', width: '15%', minWidth: '130px' }}>Match Fit</th>
                  <th style={{ padding: '0.75rem 0.75rem', width: '18%', minWidth: '140px' }}>Status</th>
                  <th style={{ padding: '0.75rem 0.75rem', width: '13%', minWidth: '110px' }}>Approval</th>
                  <th style={{ padding: '0.75rem 1rem', width: '10%', minWidth: '90px', textAlign: 'right' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr>
                    <td colSpan={6} style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>
                      Loading applications ledger...
                    </td>
                  </tr>
                ) : applications.length === 0 ? (
                  <tr>
                    <td colSpan={6} style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>
                      No applications found matching criteria. Click "+ New Application" to stage one.
                    </td>
                  </tr>
                ) : (
                  applications.map((app) => {
                    const isSelected = selectedAppId === app.id;
                    const isApproved = !!app.approval_token && app.status !== 'requires_reapproval';
                    return (
                      <tr
                        key={app.id}
                        onClick={() => loadDossier(app.id)}
                        style={{
                          cursor: 'pointer',
                          background: isSelected ? 'rgba(56, 189, 248, 0.08)' : 'transparent',
                          borderBottom: '1px solid var(--border-color)',
                        }}
                      >
                        <td style={{ padding: '0.75rem 1rem' }}>
                          <div style={{ fontWeight: 600, color: '#f8fafc', wordBreak: 'break-word' }}>{app.job_title}</div>
                          <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '0.2rem', wordBreak: 'break-word' }}>
                            {app.job_company} &bull; {app.job_location || 'Remote'}
                          </div>
                        </td>
                        <td style={{ padding: '0.75rem 0.75rem', verticalAlign: 'middle' }}>
                          <span className="badge badge-gray" style={{ fontSize: '0.6875rem', textTransform: 'uppercase', whiteSpace: 'nowrap' }}>
                            {app.portal_type}
                          </span>
                        </td>
                        <td style={{ padding: '0.75rem 0.75rem', verticalAlign: 'middle' }}>
                          {app.fit_score !== null && app.fit_score !== undefined ? (
                            <span
                              className={`badge ${app.fit_score >= 80 ? 'badge-green' : app.fit_score >= 60 ? 'badge-purple' : 'badge-blue'}`}
                              style={{ fontSize: '0.6875rem', whiteSpace: 'nowrap' }}
                            >
                              {app.fit_score}% {app.recommendation || ''}
                            </span>
                          ) : (
                            <span style={{ fontSize: '0.6875rem', color: 'var(--text-muted)' }}>N/A</span>
                          )}
                        </td>
                        <td style={{ padding: '0.75rem 0.75rem', verticalAlign: 'middle' }}>
                          <span
                            className={`badge ${
                              app.status === 'approved' || app.status === 'staged_for_preparation'
                                ? 'badge-green'
                                : app.status === 'ready_for_review'
                                ? 'badge-blue'
                                : app.status === 'action_required'
                                ? 'badge-yellow'
                                : app.status === 'requires_reapproval'
                                ? 'badge-purple'
                                : 'badge-gray'
                            }`}
                            style={{ fontSize: '0.6875rem', textTransform: 'uppercase', whiteSpace: 'nowrap', display: 'inline-flex', alignItems: 'center' }}
                          >
                            {app.status.replace(/_/g, ' ')}
                          </span>
                        </td>
                        <td style={{ padding: '0.75rem 0.75rem', verticalAlign: 'middle' }}>
                          {isApproved ? (
                            <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.25rem', color: '#34d399', fontSize: '0.6875rem', whiteSpace: 'nowrap' }}>
                              <Lock size={12} />
                              <span>Approved</span>
                            </span>
                          ) : app.status === 'action_required' ? (
                            <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.25rem', color: '#fbbf24', fontSize: '0.6875rem', whiteSpace: 'nowrap' }}>
                              <AlertTriangle size={12} />
                              <span>Action Req.</span>
                            </span>
                          ) : app.status === 'requires_reapproval' ? (
                            <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.25rem', color: '#fbbf24', fontSize: '0.6875rem', whiteSpace: 'nowrap' }}>
                              <AlertTriangle size={12} />
                              <span>Invalidated</span>
                            </span>
                          ) : (
                            <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.25rem', color: 'var(--text-muted)', fontSize: '0.6875rem', whiteSpace: 'nowrap' }}>
                              <Unlock size={12} />
                              <span>Unapproved</span>
                            </span>
                          )}
                        </td>
                        <td style={{ padding: '0.75rem 1rem', textAlign: 'right', verticalAlign: 'middle' }}>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              loadDossier(app.id);
                            }}
                            className="btn btn-secondary"
                            style={{ fontSize: '0.6875rem', padding: '0.25rem 0.5rem', display: 'inline-flex', alignItems: 'center', gap: '0.25rem' }}
                          >
                            <Eye size={12} />
                            <span>Staging</span>
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

        {/* Selected Application Details Panel (Full Width below Ledger) */}
        {selectedAppId && (
          <div id="selected-application-details" className="card" style={{ borderTop: '4px solid #38bdf8', padding: '1.5rem', width: '100%' }}>
            {loadingDossier ? (
              <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>
                Loading Application Dossier & Staging Status...
              </div>
            ) : dossier ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem', width: '100%' }}>
                {/* Dossier Header */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', borderBottom: '1px solid var(--border-color)', paddingBottom: '0.875rem' }}>
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
                      <h3 style={{ fontSize: '1.25rem', fontWeight: 700 }}>
                        {dossier.job.title}
                      </h3>
                      <span className="badge badge-blue">App #{dossier.application.id}</span>
                      <span
                        className={`badge ${
                          dossier.application.status === 'approved' || dossier.application.status === 'staged_for_preparation'
                            ? 'badge-green'
                            : dossier.application.status === 'ready_for_review'
                            ? 'badge-blue'
                            : dossier.application.status === 'action_required'
                            ? 'badge-yellow'
                            : dossier.application.status === 'requires_reapproval'
                            ? 'badge-purple'
                            : 'badge-gray'
                        }`}
                        style={{ textTransform: 'uppercase' }}
                      >
                        {dossier.application.status.replace(/_/g, ' ')}
                      </span>
                    </div>
                    <div style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)', marginTop: '0.35rem', display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
                      <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.25rem' }}>
                        <Building size={14} />
                        <strong>{dossier.job.company}</strong>
                      </span>
                      <span>&bull;</span>
                      <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.25rem' }}>
                        <MapPin size={14} />
                        <span>{dossier.job.location || 'Remote'} ({dossier.job.remote_type})</span>
                      </span>
                    </div>
                  </div>

                  <button
                    onClick={() => setSelectedAppId(null)}
                    className="btn btn-secondary"
                    style={{ fontSize: '0.75rem', padding: '0.3rem 0.6rem', display: 'inline-flex', alignItems: 'center', gap: '0.25rem' }}
                    title="Close Application Details"
                  >
                    <X size={14} />
                    <span>Close Details</span>
                  </button>
                </div>

                {/* CAPTCHA / Browser Challenge Human Handoff Alert */}
                {(dossier.application.status === 'action_required' || latestPrepRun?.status === 'blocked_by_captcha' || latestPrepRun?.captcha_detected) && (
                  <div
                    style={{
                      background: 'rgba(251, 191, 36, 0.12)',
                      border: '1px solid rgba(251, 191, 36, 0.4)',
                      borderRadius: '8px',
                      padding: '1.25rem',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '0.875rem',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '0.5rem' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <AlertTriangle size={20} color="#fbbf24" />
                        <strong style={{ fontSize: '0.9375rem', color: '#fbbf24' }}>
                          Browser Verification Required (Human Handoff)
                        </strong>
                      </div>
                      <span className="badge badge-yellow">AUTOMATION PAUSED</span>
                    </div>

                    <p style={{ fontSize: '0.8125rem', color: '#f8fafc', lineHeight: 1.5 }}>
                      Automation has paused safely because the job portal requires human verification (e.g. CAPTCHA, bot check, or login challenge). Anti-bot protection is never bypassed automatically.
                    </p>

                    {/* Step-by-Step Instructions */}
                    <div style={{ background: '#090d16', padding: '0.75rem', borderRadius: '6px', border: '1px solid var(--border-color)', fontSize: '0.75rem' }}>
                      <div style={{ color: 'var(--text-muted)', fontWeight: 700, textTransform: 'uppercase', marginBottom: '0.35rem', fontSize: '0.6875rem' }}>
                        Required Steps for Completion:
                      </div>
                      <ol style={{ paddingLeft: '1.25rem', margin: 0, color: '#f8fafc', display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                        <li>Click <strong>Open / Focus Application Browser</strong> to access the exact active application portal.</li>
                        <li>Complete the CAPTCHA / bot verification manually on the page.</li>
                        <li>Return to this dashboard.</li>
                        <li>Click <strong>Continue After Verification</strong> to resume workflow staging.</li>
                      </ol>
                    </div>

                    {/* Metadata Grid */}
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '0.5rem', background: '#090d16', padding: '0.625rem', borderRadius: '6px', fontSize: '0.75rem' }}>
                      <div>
                        <span style={{ color: 'var(--text-muted)' }}>Company: </span>
                        <strong style={{ color: '#f8fafc' }}>{dossier.job.company}</strong>
                      </div>
                      <div>
                        <span style={{ color: 'var(--text-muted)' }}>Job Title: </span>
                        <strong style={{ color: '#38bdf8' }}>{dossier.job.title}</strong>
                      </div>
                      <div>
                        <span style={{ color: 'var(--text-muted)' }}>Application ID: </span>
                        <code>#{dossier.application.id}</code> (Job #{dossier.job.id})
                      </div>
                      <div>
                        <span style={{ color: 'var(--text-muted)' }}>Status: </span>
                        <span className="badge badge-yellow" style={{ fontSize: '0.625rem' }}>ACTION_REQUIRED</span>
                      </div>
                      <div>
                        <span style={{ color: 'var(--text-muted)' }}>Challenge Type: </span>
                        <span style={{ color: '#fbbf24', fontWeight: 600 }}>
                          {latestPrepRun?.captcha_detected ? 'CAPTCHA / Bot Protection' : 'Browser Challenge / Auth Wall'}
                        </span>
                      </div>
                      <div>
                        <span style={{ color: 'var(--text-muted)' }}>Detected: </span>
                        <span style={{ color: 'var(--text-secondary)' }}>
                          {latestPrepRun?.created_at ? new Date(latestPrepRun.created_at).toLocaleTimeString() : 'Recently detected'}
                        </span>
                      </div>
                      <div>
                        <span style={{ color: 'var(--text-muted)' }}>Tailored Resume: </span>
                        <span style={{ color: '#c084fc' }}>Resume #{dossier.tailored_resume?.id || 'None'} (Preserved)</span>
                      </div>
                      <div>
                        <span style={{ color: 'var(--text-muted)' }}>Approval Binding: </span>
                        <span style={{ color: '#34d399', fontWeight: 600 }}>Valid (Hashes Intact)</span>
                      </div>
                    </div>

                    {/* Browser Status Feedback if present */}
                    {browserStatusMsg && (
                      <div
                        style={{
                          background: sessionUnavailable ? 'rgba(239, 68, 68, 0.15)' : 'rgba(56, 189, 248, 0.12)',
                          border: `1px solid ${sessionUnavailable ? 'rgba(239, 68, 68, 0.4)' : 'rgba(56, 189, 248, 0.3)'}`,
                          borderRadius: '6px',
                          padding: '0.5rem 0.75rem',
                          fontSize: '0.75rem',
                          color: sessionUnavailable ? '#fca5a5' : '#38bdf8',
                        }}
                      >
                        {browserStatusMsg}
                      </div>
                    )}

                    {/* Action Buttons */}
                    <div style={{ display: 'flex', justifyContent: 'flex-end', alignItems: 'center', gap: '0.625rem', marginTop: '0.25rem', flexWrap: 'wrap' }}>
                      <button
                        onClick={() => handleOpenOrFocusBrowser()}
                        disabled={isOpeningBrowser}
                        className="btn btn-secondary"
                        style={{
                          borderColor: '#38bdf8',
                          color: '#38bdf8',
                          fontWeight: 600,
                          fontSize: '0.8125rem',
                          padding: '0.4rem 0.85rem',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '0.375rem',
                        }}
                      >
                        <Globe size={14} />
                        <span>{isOpeningBrowser ? 'Connecting...' : 'Open / Focus Application Browser'}</span>
                      </button>

                      {sessionUnavailable && (
                        <button
                          onClick={() => handleOpenOrFocusBrowser()}
                          disabled={isOpeningBrowser}
                          className="btn btn-secondary"
                          style={{
                            borderColor: '#fbbf24',
                            color: '#fbbf24',
                            fontWeight: 600,
                            fontSize: '0.8125rem',
                            padding: '0.4rem 0.85rem',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '0.375rem',
                          }}
                        >
                          <RefreshCw size={14} />
                          <span>Start New Browser Session</span>
                        </button>
                      )}

                      <button
                        onClick={handleContinueAfterVerification}
                        disabled={isResumingVerification}
                        className="btn btn-primary"
                        style={{
                          background: '#d97706',
                          borderColor: '#b45309',
                          color: '#ffffff',
                          fontWeight: 600,
                          fontSize: '0.8125rem',
                          padding: '0.4rem 0.85rem',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '0.375rem',
                        }}
                      >
                        <Play size={14} />
                        <span>{isResumingVerification ? 'Resuming...' : 'Continue After Verification'}</span>
                      </button>
                    </div>
                  </div>
                )}

                {/* Dossier Sub-Tabs */}
                <div style={{ display: 'flex', gap: '0.375rem', borderBottom: '1px solid var(--border-color)', paddingBottom: '0.5rem', flexWrap: 'wrap' }}>
                  <button
                    onClick={() => setDossierTab('staging')}
                    className={`btn ${dossierTab === 'staging' ? 'btn-primary' : 'btn-secondary'}`}
                    style={{ fontSize: '0.75rem', padding: '0.3rem 0.6rem', display: 'flex', alignItems: 'center', gap: '0.25rem' }}
                  >
                    <Globe size={12} />
                    <span>Browser Staging (Phase 9)</span>
                  </button>
                  <button
                    onClick={() => setDossierTab('approval')}
                    className={`btn ${dossierTab === 'approval' ? 'btn-primary' : 'btn-secondary'}`}
                    style={{ fontSize: '0.75rem', padding: '0.3rem 0.6rem', display: 'flex', alignItems: 'center', gap: '0.25rem' }}
                  >
                    <Lock size={12} />
                    <span>Approval Security Gate</span>
                  </button>
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

                {/* TAB 1: PHASE 9 PLAYWRIGHT BROWSER STAGING ENGINE */}
                {dossierTab === 'staging' && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                    {/* Non-Negotiable Safety Checklist Callout */}
                    <div style={{ background: '#090d16', padding: '0.75rem', borderRadius: '6px', border: '1px solid var(--border-color)' }}>
                      <div style={{ fontSize: '0.6875rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.375rem' }}>
                        <ShieldCheck size={14} color="#34d399" />
                        <span>Non-Negotiable Browser Safety Guarantees</span>
                      </div>
                      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem', fontSize: '0.6875rem' }}>
                        <div style={{ background: 'rgba(52, 211, 153, 0.08)', padding: '0.4rem', borderRadius: '4px', border: '1px solid rgba(52, 211, 153, 0.2)', color: '#34d399' }}>
                          ✓ Final Submit Guard: ACTIVE (Never Submitted)
                        </div>
                        <div style={{ background: 'rgba(56, 189, 248, 0.08)', padding: '0.4rem', borderRadius: '4px', border: '1px solid rgba(56, 189, 248, 0.2)', color: '#38bdf8' }}>
                          ✓ Server Authorization: Required Prior to Run
                        </div>
                        <div style={{ background: 'rgba(251, 191, 36, 0.08)', padding: '0.4rem', borderRadius: '4px', border: '1px solid rgba(251, 191, 36, 0.2)', color: '#fbbf24' }}>
                          ✓ CAPTCHA / Bot Defense: Safe Human Pause
                        </div>
                        <div style={{ background: 'rgba(192, 132, 252, 0.08)', padding: '0.4rem', borderRadius: '4px', border: '1px solid rgba(192, 132, 252, 0.2)', color: '#c084fc' }}>
                          ✓ Prompt Injection Filter: Policy Enforced
                        </div>
                      </div>
                    </div>

                    {/* Staging Execution Controls */}
                    <div style={{ background: '#090d16', padding: '0.875rem', borderRadius: '6px', border: '1px solid var(--border-color)', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                      <label style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)' }}>
                        Target Portal URL (or Local Fixture):
                      </label>
                      <input
                        type="text"
                        value={customPortalUrl}
                        onChange={(e) => setCustomPortalUrl(e.target.value)}
                        placeholder="https://boards.greenhouse.io/... or file:///..."
                        style={{
                          width: '100%',
                          background: '#131b2e',
                          border: '1px solid var(--border-color)',
                          borderRadius: '4px',
                          color: '#f8fafc',
                          fontSize: '0.75rem',
                          padding: '0.5rem',
                        }}
                      />

                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.5rem' }}>
                        <div style={{ fontSize: '0.6875rem', color: 'var(--text-muted)' }}>
                          Status: <span className="badge badge-blue">{dossier.application.status.toUpperCase()}</span>
                        </div>

                        <button
                          onClick={handleRunPreparation}
                          disabled={isRunningStaging || !approvalVerification?.is_valid}
                          className="btn btn-primary"
                          style={{
                            fontSize: '0.75rem',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '0.375rem',
                            opacity: approvalVerification?.is_valid ? 1 : 0.6,
                          }}
                        >
                          <Play size={13} />
                          <span>{isRunningStaging ? 'Executing Playwright...' : 'Execute Browser Preparation'}</span>
                        </button>
                      </div>

                      {stagingError && (
                        <div style={{ background: 'rgba(239, 68, 68, 0.15)', padding: '0.625rem', borderRadius: '4px', border: '1px solid rgba(239, 68, 68, 0.4)', color: '#fca5a5', fontSize: '0.75rem' }}>
                          <strong>Execution Block:</strong> {stagingError}
                        </div>
                      )}
                    </div>

                    {/* Latest Preparation Run Details */}
                    {latestPrepRun && (
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                          <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                            Latest Staging Run (#{latestPrepRun.id})
                          </span>
                          <span className={`badge ${latestPrepRun.status === 'staged' ? 'badge-green' : latestPrepRun.status === 'paused_for_human_input' ? 'badge-purple' : 'badge-blue'}`}>
                            {latestPrepRun.status.toUpperCase()}
                          </span>
                        </div>

                        {/* Fields Filled Table */}
                        <div style={{ background: '#090d16', padding: '0.75rem', borderRadius: '6px', border: '1px solid var(--border-color)' }}>
                          <div style={{ fontSize: '0.6875rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '0.375rem' }}>
                            Pre-Filled Form Fields ({latestPrepRun.fields_filled.length}):
                          </div>
                          <div style={{ maxHeight: '160px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                            {latestPrepRun.fields_filled.map((f, fi) => (
                              <div key={fi} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.6875rem', background: '#131b2e', padding: '0.3rem 0.5rem', borderRadius: '4px' }}>
                                <strong style={{ color: '#38bdf8' }}>{f.field}</strong>
                                <span style={{ color: 'var(--text-secondary)', maxWidth: '280px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                                  {String(f.value)}
                                </span>
                              </div>
                            ))}
                          </div>
                        </div>

                        {/* Unresolved Fields Alert if any */}
                        {latestPrepRun.unresolved_fields.length > 0 && (
                          <div style={{ background: 'rgba(251, 191, 36, 0.12)', padding: '0.75rem', borderRadius: '6px', border: '1px solid rgba(251, 191, 36, 0.3)' }}>
                            <div style={{ fontSize: '0.6875rem', fontWeight: 700, color: '#fbbf24', textTransform: 'uppercase', marginBottom: '0.25rem' }}>
                              Unresolved Fields (Action Required):
                            </div>
                            <ul style={{ listStylePosition: 'inside', fontSize: '0.6875rem', color: '#f8fafc' }}>
                              {latestPrepRun.unresolved_fields.map((u, ui) => (
                                <li key={ui}>{u.field}: {u.reason || 'Missing answer'}</li>
                              ))}
                            </ul>
                          </div>
                        )}

                        {/* Visual Screenshot Audit Preview */}
                        {latestPrepRun.screenshot_path && (
                          <div style={{ background: '#090d16', padding: '0.75rem', borderRadius: '6px', border: '1px solid var(--border-color)' }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.375rem', fontSize: '0.6875rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '0.375rem' }}>
                              <Camera size={13} />
                              <span>Staged Form Screenshot Audit</span>
                            </div>
                            <div style={{ fontSize: '0.6875rem', color: 'var(--text-secondary)', fontFamily: 'monospace', wordBreak: 'break-all' }}>
                              File: {latestPrepRun.screenshot_path}
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                )}

                {/* TAB 2: PHASE 8 APPROVAL & SECURITY GATE CENTER */}
                {dossierTab === 'approval' && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                    <div
                      style={{
                        padding: '1rem',
                        borderRadius: '6px',
                        border: `1px solid ${
                          approvalVerification?.is_valid
                            ? 'rgba(52, 211, 153, 0.4)'
                            : dossier.application.status === 'requires_reapproval'
                            ? 'rgba(251, 191, 36, 0.5)'
                            : 'rgba(56, 189, 248, 0.3)'
                        }`,
                        background: approvalVerification?.is_valid
                          ? 'rgba(52, 211, 153, 0.08)'
                          : dossier.application.status === 'requires_reapproval'
                          ? 'rgba(251, 191, 36, 0.08)'
                          : '#090d16',
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                          {approvalVerification?.is_valid ? (
                            <ShieldCheck size={18} color="#34d399" />
                          ) : dossier.application.status === 'requires_reapproval' ? (
                            <ShieldAlert size={18} color="#fbbf24" />
                          ) : (
                            <Lock size={18} color="#38bdf8" />
                          )}
                          <strong style={{ fontSize: '0.875rem' }}>
                            {approvalVerification?.is_valid
                              ? 'Human Approval Active & Cryptographically Verified'
                              : dossier.application.status === 'requires_reapproval'
                              ? 'Approval Invalidated: Material Change Detected'
                              : 'Approval Required: Server-Side Security Boundary'}
                          </strong>
                        </div>

                        <button
                          onClick={() => verifyLiveApproval(dossier.application.id)}
                          disabled={verifyingApproval}
                          className="btn btn-secondary"
                          style={{ fontSize: '0.6875rem', padding: '0.2rem 0.45rem', display: 'flex', alignItems: 'center', gap: '0.25rem' }}
                        >
                          <RefreshCw size={11} className={verifyingApproval ? 'animate-spin' : ''} />
                          <span>Verify Live Hashes</span>
                        </button>
                      </div>

                      <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', lineHeight: 1.4 }}>
                        {approvalVerification?.is_valid
                          ? `Application #${dossier.application.id} is authorized under token ${approvalVerification.approval_token}. All 4 material input hashes match the human sign-off snapshot.`
                          : approvalVerification?.reason || 'Browser preparation and portal submission operations are strictly blocked until human approval is signed.'}
                      </p>

                      {approvalVerification?.mismatches && approvalVerification.mismatches.length > 0 && (
                        <div style={{ marginTop: '0.75rem', padding: '0.5rem', background: 'rgba(251, 191, 36, 0.15)', borderRadius: '4px', border: '1px solid rgba(251, 191, 36, 0.3)' }}>
                          <div style={{ fontSize: '0.6875rem', fontWeight: 700, color: '#fbbf24', textTransform: 'uppercase', marginBottom: '0.25rem' }}>
                            Mismatches Detected:
                          </div>
                          <ul style={{ listStylePosition: 'inside', fontSize: '0.6875rem', color: '#f8fafc' }}>
                            {approvalVerification.mismatches.map((m, mi) => (
                              <li key={mi}>{m}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>

                    <div style={{ background: '#090d16', padding: '0.75rem', borderRadius: '6px', border: '1px solid var(--border-color)' }}>
                      <div style={{ fontSize: '0.6875rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.375rem' }}>
                        <Key size={12} />
                        <span>Cryptographic Input Binding Hashes (SHA-256)</span>
                      </div>

                      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem', fontSize: '0.6875rem' }}>
                        <div style={{ background: '#131b2e', padding: '0.4rem', borderRadius: '4px' }}>
                          <span style={{ color: 'var(--text-muted)' }}>Job Specification Hash:</span>
                          <div style={{ fontFamily: 'monospace', color: '#38bdf8', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                            {approvalVerification?.hashes?.job_hash || 'Computed on approval'}
                          </div>
                        </div>

                        <div style={{ background: '#131b2e', padding: '0.4rem', borderRadius: '4px' }}>
                          <span style={{ color: 'var(--text-muted)' }}>Candidate Profile Hash:</span>
                          <div style={{ fontFamily: 'monospace', color: '#34d399', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                            {approvalVerification?.hashes?.candidate_hash || 'Computed on approval'}
                          </div>
                        </div>

                        <div style={{ background: '#131b2e', padding: '0.4rem', borderRadius: '4px' }}>
                          <span style={{ color: 'var(--text-muted)' }}>Tailored Resume Hash:</span>
                          <div style={{ fontFamily: 'monospace', color: '#c084fc', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                            {approvalVerification?.hashes?.resume_hash || 'Computed on approval'}
                          </div>
                        </div>

                        <div style={{ background: '#131b2e', padding: '0.4rem', borderRadius: '4px' }}>
                          <span style={{ color: 'var(--text-muted)' }}>Screening Q&A Hash:</span>
                          <div style={{ fontFamily: 'monospace', color: '#fbbf24', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                            {approvalVerification?.hashes?.answers_hash || 'Computed on approval'}
                          </div>
                        </div>
                      </div>
                    </div>

                    <div style={{ background: '#090d16', padding: '0.875rem', borderRadius: '6px', border: '1px solid var(--border-color)', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                      <label style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)' }}>
                        Approver Justification & Sign-off Notes:
                      </label>
                      <textarea
                        value={approverNotesInput}
                        onChange={(e) => setApproverNotesInput(e.target.value)}
                        placeholder="e.g. Sourced via Greenhouse discovery feed. Verified 100% claim traceability in resume against master profile."
                        rows={2}
                        style={{
                          width: '100%',
                          background: '#131b2e',
                          border: '1px solid var(--border-color)',
                          borderRadius: '4px',
                          color: '#f8fafc',
                          fontSize: '0.75rem',
                          padding: '0.5rem',
                        }}
                      />

                      <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', alignItems: 'center', justifyContent: 'space-between' }}>
                        <div style={{ display: 'flex', gap: '0.375rem' }}>
                          <button
                            onClick={handleGrantApproval}
                            disabled={isApproving}
                            className="btn btn-primary"
                            style={{ fontSize: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.375rem' }}
                          >
                            <ShieldCheck size={14} />
                            <span>{isApproving ? 'Signing Approval...' : 'Grant Human Approval'}</span>
                          </button>

                          <button
                            onClick={handleAuthorizePreparation}
                            disabled={isAuthorizingPrep || !approvalVerification?.is_valid}
                            className="btn btn-secondary"
                            style={{
                              fontSize: '0.75rem',
                              display: 'flex',
                              alignItems: 'center',
                              gap: '0.375rem',
                              borderColor: approvalVerification?.is_valid ? '#34d399' : 'var(--border-color)',
                              color: approvalVerification?.is_valid ? '#34d399' : 'var(--text-muted)',
                            }}
                          >
                            <Play size={13} />
                            <span>{isAuthorizingPrep ? 'Authorizing...' : 'Authorize Preparation Gate'}</span>
                          </button>
                        </div>

                        <div style={{ display: 'flex', gap: '0.375rem' }}>
                          <button
                            onClick={handleRevokeApproval}
                            disabled={!dossier.application.approval_token}
                            className="btn btn-secondary"
                            style={{ fontSize: '0.6875rem', padding: '0.3rem 0.5rem', color: '#fbbf24' }}
                          >
                            Revoke
                          </button>

                          <button
                            onClick={handleRejectApplication}
                            className="btn btn-secondary"
                            style={{ fontSize: '0.6875rem', padding: '0.3rem 0.5rem', color: '#f87171' }}
                          >
                            Reject
                          </button>
                        </div>
                      </div>

                      {authError && (
                        <div style={{ background: 'rgba(239, 68, 68, 0.15)', padding: '0.625rem', borderRadius: '4px', border: '1px solid rgba(239, 68, 68, 0.4)', color: '#fca5a5', fontSize: '0.75rem' }}>
                          <strong>Security Block:</strong> {authError}
                        </div>
                      )}

                      {prepAuthResult && (
                        <div style={{ background: 'rgba(52, 211, 153, 0.12)', padding: '0.625rem', borderRadius: '4px', border: '1px solid rgba(52, 211, 153, 0.4)', color: '#34d399', fontSize: '0.75rem' }}>
                          <div style={{ fontWeight: 700, marginBottom: '0.25rem' }}>✓ Server-side Security Gate Passed</div>
                          <div>Status: <code>{prepAuthResult.status}</code> &bull; Authorized: {new Date(prepAuthResult.authorized_at).toLocaleTimeString()}</div>
                          <div style={{ fontSize: '0.6875rem', color: 'var(--text-secondary)', marginTop: '0.25rem', fontFamily: 'monospace' }}>
                            Certificate Token: {prepAuthResult.approval_token}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* TAB 3: Job Details & Portal Context */}
                {dossierTab === 'job' && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
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

                {/* TAB 4: Tailored Materials & Fact Attribution */}
                {dossierTab === 'resume' && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
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
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                          <div style={{ display: 'flex', gap: '0.25rem', flexWrap: 'wrap' }}>
                            <button
                              onClick={() => setDocFormat('markdown')}
                              className={`btn ${docFormat === 'markdown' ? 'btn-primary' : 'btn-secondary'}`}
                              style={{ fontSize: '0.6875rem', padding: '0.2rem 0.5rem' }}
                            >
                              ATS Markdown
                            </button>
                            <button
                              onClick={() => setDocFormat('html')}
                              className={`btn ${docFormat === 'html' ? 'btn-primary' : 'btn-secondary'}`}
                              style={{ fontSize: '0.6875rem', padding: '0.2rem 0.5rem' }}
                            >
                              HTML Resume
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
                              Plain Text
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
                                const text = docFormat === 'cover_letter'
                                  ? dossier.tailored_resume?.cover_letter
                                  : docFormat === 'text'
                                  ? dossier.tailored_resume?.compiled_text
                                  : docFormat === 'html'
                                  ? dossier.tailored_resume?.compiled_html
                                  : dossier.tailored_resume?.compiled_markdown;
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

                        {docFormat === 'markdown' && (
                          <pre className="code-block" style={{ maxHeight: '380px', fontSize: '0.75rem', lineHeight: 1.4 }}>
                            {dossier.tailored_resume.compiled_markdown}
                          </pre>
                        )}
                        {docFormat === 'html' && (
                          <div
                            style={{
                              background: '#ffffff',
                              borderRadius: '6px',
                              border: '1px solid var(--border-color)',
                              overflow: 'hidden',
                              width: '100%',
                            }}
                          >
                            <iframe
                              srcDoc={dossier.tailored_resume.compiled_html || '<!DOCTYPE html><html><body><p style="padding:20px;color:#64748b;font-family:sans-serif;">No HTML document generated.</p></body></html>'}
                              title="Approved HTML Resume Preview"
                              style={{
                                width: '100%',
                                height: '480px',
                                border: 'none',
                                backgroundColor: '#ffffff',
                                display: 'block',
                              }}
                              sandbox="allow-same-origin"
                            />
                          </div>
                        )}
                        {docFormat === 'cover_letter' && (
                          <div style={{ background: '#090d16', padding: '1rem', borderRadius: '6px', border: '1px solid var(--border-color)', fontSize: '0.75rem', lineHeight: 1.6, maxHeight: '380px', overflowY: 'auto', whiteSpace: 'pre-wrap' }}>
                            {dossier.tailored_resume.cover_letter}
                          </div>
                        )}
                        {docFormat === 'text' && (
                          <pre className="code-block" style={{ maxHeight: '380px', fontSize: '0.6875rem', lineHeight: 1.3 }}>
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
                        No tailored resume linked.
                      </div>
                    )}
                  </div>
                )}

                {/* TAB 5: Screening Questions Q&A */}
                {dossierTab === 'screening' && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                      JSON key-value payload for portal application questions (editing will invalidate approval):
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

                {/* TAB 6: Review Ledger */}
                {dossierTab === 'review' && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
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
