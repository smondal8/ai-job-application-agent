import React, { useState, useEffect, useCallback } from 'react';
import {
  ShieldCheck,
  AlertTriangle,
  FileUp,
  Plus,
  Trash2,
  Check,
  X,
  ExternalLink,
  Bot,
  User,
  RefreshCw,
} from 'lucide-react';
import { api } from '../services/api';
import {
  CandidateProfile,
  VerifiedGroundTruthContextResponse,
  RawResumeImport,
} from '../types';

export const CandidateProfileView: React.FC = () => {
  const [profile, setProfile] = useState<CandidateProfile | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [activeSubTab, setActiveSubTab] = useState<
    'overview' | 'experience' | 'education' | 'skills' | 'projects' | 'importer'
  >('overview');

  // Ground Truth Context Modal
  const [showGroundTruthModal, setShowGroundTruthModal] = useState<boolean>(false);
  const [groundTruthContext, setGroundTruthContext] = useState<VerifiedGroundTruthContextResponse | null>(null);
  const [loadingGroundTruth, setLoadingGroundTruth] = useState<boolean>(false);

  // Edit Profile Form State
  const [editProfileForm, setEditProfileForm] = useState({
    full_name: '',
    email: '',
    phone: '',
    location: '',
    headline: '',
    summary: '',
    linkedin_url: '',
    github_url: '',
    portfolio_url: '',
  });

  // Add Experience Form State
  const [newExpForm, setNewExpForm] = useState({
    company: '',
    position: '',
    location: '',
    start_date: '',
    end_date: '',
    is_current: false,
    description: '',
    highlightsText: '',
    skillsText: '',
  });

  // Add Education Form State
  const [newEduForm, setNewEduForm] = useState({
    institution: '',
    degree: '',
    field_of_study: '',
    start_date: '',
    end_date: '',
    gpa: '',
  });

  // Add Skill Form State
  const [newSkillForm, setNewSkillForm] = useState({
    name: '',
    category: 'languages',
    proficiency: 'intermediate',
  });
  const [bulkSkillsText, setBulkSkillsText] = useState('');

  // Add Project Form State
  const [newProjectForm, setNewProjectForm] = useState({
    name: '',
    description: '',
    url: '',
    technologiesText: '',
    highlightsText: '',
  });

  // Importer Form State
  const [rawTextToImport, setRawTextToImport] = useState('');
  const [importLabel, setImportLabel] = useState('Pasted Candidate Resume');
  const [lastRawImport, setLastRawImport] = useState<RawResumeImport | null>(null);
  const [importing, setImporting] = useState(false);
  const [fetchError, setFetchError] = useState<string | null>(null);
  const [isInitializing, setIsInitializing] = useState(false);

  const syncProfileState = useCallback((data: CandidateProfile) => {
    setProfile(data);
    setEditProfileForm({
      full_name: data.full_name || '',
      email: data.email || '',
      phone: data.phone || '',
      location: data.location || '',
      headline: data.headline || '',
      summary: data.summary || '',
      linkedin_url: data.linkedin_url || '',
      github_url: data.github_url || '',
      portfolio_url: data.portfolio_url || '',
    });
  }, []);

  const fetchProfile = useCallback(async () => {
    setLoading(true);
    setFetchError(null);
    try {
      const data = await api.getPrimaryProfile();
      syncProfileState(data);
    } catch (err: any) {
      console.error('Failed to load candidate profile:', err);
      setFetchError(err.message || 'Failed to load candidate profile.');
    } finally {
      setLoading(false);
    }
  }, [syncProfileState]);

  const handleInitializeProfile = async () => {
    setIsInitializing(true);
    setFetchError(null);
    try {
      let data: CandidateProfile;
      try {
        data = await api.getPrimaryProfile();
      } catch {
        data = await api.createProfile({
          full_name: 'Candidate Name',
          email: 'candidate@example.com',
          headline: 'Software Engineer',
          summary: '',
        });
      }
      syncProfileState(data);
    } catch (err: any) {
      alert(`Initialization failed: ${err.message}`);
      setFetchError(err.message);
    } finally {
      setIsInitializing(false);
    }
  };

  useEffect(() => {
    fetchProfile();
  }, [fetchProfile]);

  const handleVerifyAll = async () => {
    if (!profile) return;
    try {
      const updated = await api.verifyProfile(profile.id, true);
      setProfile(updated);
    } catch (err) {
      console.error('Failed to verify profile:', err);
    }
  };

  const handleUpdateProfileBasics = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!profile) return;
    try {
      const updated = await api.updateProfile(profile.id, editProfileForm);
      syncProfileState(updated);
      alert('Candidate profile updated successfully.');
    } catch (err: any) {
      alert(`Error updating profile: ${err.message}`);
    }
  };

  const handleFetchGroundTruthContext = async () => {
    if (!profile) return;
    setLoadingGroundTruth(true);
    setShowGroundTruthModal(true);
    try {
      const ctx = await api.getVerifiedGroundTruthContext(profile.id);
      setGroundTruthContext(ctx);
    } catch (err: any) {
      console.error('Failed to load verified context:', err);
    } finally {
      setLoadingGroundTruth(false);
    }
  };

  // --- Handlers: Experience ---
  const handleAddExperience = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!profile || !newExpForm.company || !newExpForm.position) return;
    try {
      const highlights = newExpForm.highlightsText
        .split('\n')
        .map((s) => s.trim())
        .filter(Boolean);
      const skills_used = newExpForm.skillsText
        .split(',')
        .map((s) => s.trim())
        .filter(Boolean);

      await api.addExperience(profile.id, {
        company: newExpForm.company,
        position: newExpForm.position,
        location: newExpForm.location || null,
        start_date: newExpForm.start_date || '2022',
        end_date: newExpForm.is_current ? null : newExpForm.end_date || null,
        is_current: newExpForm.is_current,
        description: newExpForm.description || null,
        highlights,
        skills_used,
      });

      setNewExpForm({
        company: '',
        position: '',
        location: '',
        start_date: '',
        end_date: '',
        is_current: false,
        description: '',
        highlightsText: '',
        skillsText: '',
      });
      fetchProfile();
    } catch (err: any) {
      alert(`Error adding experience: ${err.message}`);
    }
  };

  const handleToggleExpVerification = async (expId: number, currentStatus: boolean) => {
    try {
      await api.toggleExperienceVerification(expId, !currentStatus);
      fetchProfile();
    } catch (err) {
      console.error('Failed to toggle experience verification:', err);
    }
  };

  const handleDeleteExp = async (expId: number) => {
    if (!confirm('Delete this work experience?')) return;
    try {
      await api.deleteExperience(expId);
      fetchProfile();
    } catch (err) {
      console.error('Failed to delete experience:', err);
    }
  };

  // --- Handlers: Education ---
  const handleAddEducation = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!profile || !newEduForm.institution || !newEduForm.degree) return;
    try {
      await api.addEducation(profile.id, {
        institution: newEduForm.institution,
        degree: newEduForm.degree,
        field_of_study: newEduForm.field_of_study || null,
        start_date: newEduForm.start_date || null,
        end_date: newEduForm.end_date || null,
        gpa: newEduForm.gpa || null,
      });
      setNewEduForm({
        institution: '',
        degree: '',
        field_of_study: '',
        start_date: '',
        end_date: '',
        gpa: '',
      });
      fetchProfile();
    } catch (err: any) {
      alert(`Error adding education: ${err.message}`);
    }
  };

  const handleToggleEduVerification = async (eduId: number, currentStatus: boolean) => {
    try {
      await api.toggleEducationVerification(eduId, !currentStatus);
      fetchProfile();
    } catch (err) {
      console.error('Failed to toggle education verification:', err);
    }
  };

  const handleDeleteEdu = async (eduId: number) => {
    if (!confirm('Delete this education record?')) return;
    try {
      await api.deleteEducation(eduId);
      fetchProfile();
    } catch (err) {
      console.error('Failed to delete education:', err);
    }
  };

  // --- Handlers: Skills ---
  const handleAddSkill = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!profile || !newSkillForm.name) return;
    try {
      await api.addSkill(profile.id, newSkillForm);
      setNewSkillForm({ name: '', category: 'languages', proficiency: 'intermediate' });
      fetchProfile();
    } catch (err: any) {
      alert(`Error adding skill: ${err.message}`);
    }
  };

  const handleBulkAddSkills = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!profile || !bulkSkillsText.trim()) return;
    try {
      const skillTokens = bulkSkillsText.split(/[,|\n]/).map((s) => s.trim()).filter(Boolean);
      const skillsPayload = skillTokens.map((name) => ({
        name,
        category: 'general',
        proficiency: 'intermediate',
      }));
      await api.addSkillsBulk(profile.id, skillsPayload);
      setBulkSkillsText('');
      fetchProfile();
    } catch (err: any) {
      alert(`Error bulk adding skills: ${err.message}`);
    }
  };

  const handleToggleSkillVerification = async (skillId: number, currentStatus: boolean) => {
    try {
      await api.toggleSkillVerification(skillId, !currentStatus);
      fetchProfile();
    } catch (err) {
      console.error('Failed to toggle skill verification:', err);
    }
  };

  const handleDeleteSkill = async (skillId: number) => {
    try {
      await api.deleteSkill(skillId);
      fetchProfile();
    } catch (err) {
      console.error('Failed to delete skill:', err);
    }
  };

  // --- Handlers: Projects ---
  const handleAddProject = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!profile || !newProjectForm.name) return;
    try {
      const technologies = newProjectForm.technologiesText
        .split(',')
        .map((s) => s.trim())
        .filter(Boolean);
      const highlights = newProjectForm.highlightsText
        .split('\n')
        .map((s) => s.trim())
        .filter(Boolean);

      await api.addProject(profile.id, {
        name: newProjectForm.name,
        description: newProjectForm.description || null,
        url: newProjectForm.url || null,
        technologies,
        highlights,
      });

      setNewProjectForm({
        name: '',
        description: '',
        url: '',
        technologiesText: '',
        highlightsText: '',
      });
      fetchProfile();
    } catch (err: any) {
      alert(`Error adding project: ${err.message}`);
    }
  };

  const handleToggleProjectVerification = async (projId: number, currentStatus: boolean) => {
    try {
      await api.toggleProjectVerification(projId, !currentStatus);
      fetchProfile();
    } catch (err) {
      console.error('Failed to toggle project verification:', err);
    }
  };

  const handleDeleteProject = async (projId: number) => {
    if (!confirm('Delete this project?')) return;
    try {
      await api.deleteProject(projId);
      fetchProfile();
    } catch (err) {
      console.error('Failed to delete project:', err);
    }
  };

  // --- Handlers: Raw Importer ---
  const handleImportText = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!rawTextToImport.trim()) return;
    setImporting(true);
    try {
      const rawImp = await api.importRawResumeText(
        rawTextToImport,
        importLabel,
        profile?.id
      );
      setLastRawImport(rawImp);
    } catch (err: any) {
      alert(`Import failed: ${err.message}`);
    } finally {
      setImporting(false);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setImporting(true);
    try {
      const rawImp = await api.uploadRawResumeFile(file, profile?.id);
      setLastRawImport(rawImp);
    } catch (err: any) {
      alert(`Upload failed: ${err.message}`);
    } finally {
      setImporting(false);
    }
  };

  const handleApplyImportToProfile = async (importId: number) => {
    if (!profile) return;
    try {
      const updated = await api.applyImportToProfile(importId, profile.id);
      syncProfileState(updated);
      alert('Draft facts applied to candidate profile as UNVERIFIED facts. Please review and verify each section.');
      setActiveSubTab('experience');
    } catch (err: any) {
      alert(`Failed to apply import: ${err.message}`);
    }
  };

  if (loading) {
    return (
      <div className="card" style={{ padding: '3rem', textAlign: 'center' }}>
        <RefreshCw size={28} className="animate-spin" style={{ margin: '0 auto 0.75rem', color: 'var(--text-muted)' }} />
        <p style={{ color: 'var(--text-secondary)' }}>Loading Candidate Master Profile...</p>
      </div>
    );
  }

  // Case A: Database/schema/backend error state
  if (fetchError) {
    return (
      <div
        className="card"
        style={{
          padding: '2.5rem',
          textAlign: 'center',
          maxWidth: '640px',
          margin: '2rem auto',
          borderLeft: '4px solid #ef4444',
        }}
      >
        <AlertTriangle size={40} color="#ef4444" style={{ margin: '0 auto 1rem' }} />
        <h3 style={{ fontSize: '1.25rem', fontWeight: 700, marginBottom: '0.5rem', color: '#f8fafc' }}>
          Backend / Database Connection Error
        </h3>
        <p style={{ color: 'var(--text-secondary)', marginBottom: '1rem', fontSize: '0.875rem', lineHeight: 1.5 }}>
          Failed to load candidate profile from backend. If the database was recently created or reset, ensure schema migrations have been applied with <code>./scripts/migrate.sh</code> or <code>alembic upgrade head</code>.
        </p>
        <div
          style={{
            background: 'rgba(239, 68, 68, 0.1)',
            border: '1px solid rgba(239, 68, 68, 0.3)',
            borderRadius: '6px',
            padding: '0.75rem',
            marginBottom: '1.5rem',
            fontSize: '0.75rem',
            color: '#fca5a5',
            textAlign: 'left',
            fontFamily: 'monospace',
            wordBreak: 'break-word',
          }}
        >
          {fetchError}
        </div>
        <button
          onClick={fetchProfile}
          className="btn btn-primary"
          style={{ display: 'inline-flex', alignItems: 'center', gap: '0.5rem' }}
        >
          <RefreshCw size={15} />
          <span>Retry Connection</span>
        </button>
      </div>
    );
  }

  // Case B: Valid empty profile state (Onboarding)
  if (!profile) {
    return (
      <div
        className="card"
        style={{
          padding: '2.5rem',
          textAlign: 'center',
          maxWidth: '640px',
          margin: '2rem auto',
          borderTop: '4px solid var(--primary-color)',
        }}
      >
        <User size={40} color="var(--primary-color)" style={{ margin: '0 auto 1rem' }} />
        <h3 style={{ fontSize: '1.25rem', fontWeight: 700, marginBottom: '0.5rem' }}>
          Welcome to Candidate Profile Studio
        </h3>
        <p style={{ color: 'var(--text-secondary)', marginBottom: '1.5rem', fontSize: '0.875rem', lineHeight: 1.5 }}>
          No candidate master profile found in database. Initialize a default candidate profile to start managing verified facts, analyzing job descriptions, and generating tailored application materials.
        </p>
        <button
          onClick={handleInitializeProfile}
          disabled={isInitializing}
          className="btn btn-primary"
          style={{ display: 'inline-flex', alignItems: 'center', gap: '0.5rem' }}
        >
          <RefreshCw size={16} className={isInitializing ? 'animate-spin' : ''} />
          <span>{isInitializing ? 'Initializing Profile...' : 'Initialize Master Profile'}</span>
        </button>
      </div>
    );
  }

  const verifiedFactsCount =
    (profile.is_verified ? 1 : 0) +
    profile.experiences.filter((e) => e.is_verified).length +
    profile.educations.filter((e) => e.is_verified).length +
    profile.skills.filter((s) => s.is_verified).length +
    profile.projects.filter((p) => p.is_verified).length;

  const totalFactsCount =
    1 +
    profile.experiences.length +
    profile.educations.length +
    profile.skills.length +
    profile.projects.length;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Top Banner & Human Verification Status */}
      <div
        className="card"
        style={{
          borderLeft: `4px solid ${profile.is_verified ? '#10b981' : '#f59e0b'}`,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '1rem',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div
            style={{
              width: '48px',
              height: '48px',
              borderRadius: '50%',
              backgroundColor: profile.is_verified ? 'rgba(16, 185, 129, 0.15)' : 'rgba(245, 158, 11, 0.15)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              border: `1px solid ${profile.is_verified ? 'rgba(16, 185, 129, 0.3)' : 'rgba(245, 158, 11, 0.3)'}`,
            }}
          >
            {profile.is_verified ? <ShieldCheck size={28} color="#34d399" /> : <AlertTriangle size={28} color="#fbbf24" />}
          </div>

          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
              <h2 style={{ fontSize: '1.25rem', fontWeight: 700 }}>{profile.full_name}</h2>
              <span className={`badge ${profile.is_verified ? 'badge-green' : 'badge-yellow'}`}>
                {profile.is_verified ? '✓ VERIFIED GROUND TRUTH' : '⚠ UNVERIFIED DRAFT FACTS'}
              </span>
            </div>
            <p style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
              {profile.headline || 'Master Candidate Profile'} · {profile.email} · {profile.location || 'Location Not Specified'}
            </p>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textAlign: 'right' }}>
            <div>Verified Facts: <strong style={{ color: '#34d399' }}>{verifiedFactsCount} / {totalFactsCount}</strong></div>
            <div>LLM Access: <strong>{profile.is_verified ? 'Enabled' : 'Restricted'}</strong></div>
          </div>

          {!profile.is_verified && (
            <button onClick={handleVerifyAll} className="btn btn-primary" style={{ fontSize: '0.8125rem' }}>
              <Check size={14} />
              <span>Verify & Approve All</span>
            </button>
          )}

          <button onClick={handleFetchGroundTruthContext} className="btn btn-secondary" style={{ fontSize: '0.8125rem' }}>
            <Bot size={14} />
            <span>LLM Context Preview</span>
          </button>
        </div>
      </div>

      {/* Navigation Sub-Tabs */}
      <div style={{ display: 'flex', gap: '0.5rem', borderBottom: '1px solid var(--border-color)', paddingBottom: '0.5rem', flexWrap: 'wrap' }}>
        {[
          { id: 'overview', label: '👤 Profile & Basics' },
          { id: 'experience', label: `💼 Experience (${profile.experiences.length})` },
          { id: 'education', label: `🎓 Education (${profile.educations.length})` },
          { id: 'skills', label: `⚡ Skills (${profile.skills.length})` },
          { id: 'projects', label: `🚀 Projects (${profile.projects.length})` },
          { id: 'importer', label: '📄 Resume Importer (Untrusted Drafts)' },
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

      {/* SUB-TAB 1: Profile & Basics */}
      {activeSubTab === 'overview' && (
        <div className="card">
          <h3 style={{ fontSize: '1.125rem', fontWeight: 600, marginBottom: '1.25rem' }}>
            Basic Candidate Information
          </h3>

          <form onSubmit={handleUpdateProfileBasics} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div className="grid-2">
              <div>
                <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.25rem' }}>Full Name *</label>
                <input
                  type="text"
                  value={editProfileForm.full_name}
                  onChange={(e) => setEditProfileForm({ ...editProfileForm, full_name: e.target.value })}
                  style={{ width: '100%', padding: '0.5rem', background: '#090d16', border: '1px solid var(--border-color)', borderRadius: '6px', color: '#f8fafc' }}
                  required
                />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.25rem' }}>Email Address *</label>
                <input
                  type="email"
                  value={editProfileForm.email}
                  onChange={(e) => setEditProfileForm({ ...editProfileForm, email: e.target.value })}
                  style={{ width: '100%', padding: '0.5rem', background: '#090d16', border: '1px solid var(--border-color)', borderRadius: '6px', color: '#f8fafc' }}
                  required
                />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.25rem' }}>Phone Number</label>
                <input
                  type="text"
                  value={editProfileForm.phone}
                  onChange={(e) => setEditProfileForm({ ...editProfileForm, phone: e.target.value })}
                  placeholder="+1 (555) 000-0000"
                  style={{ width: '100%', padding: '0.5rem', background: '#090d16', border: '1px solid var(--border-color)', borderRadius: '6px', color: '#f8fafc' }}
                />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.25rem' }}>Location / Timezone</label>
                <input
                  type="text"
                  value={editProfileForm.location}
                  onChange={(e) => setEditProfileForm({ ...editProfileForm, location: e.target.value })}
                  placeholder="San Francisco, CA"
                  style={{ width: '100%', padding: '0.5rem', background: '#090d16', border: '1px solid var(--border-color)', borderRadius: '6px', color: '#f8fafc' }}
                />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.25rem' }}>Professional Headline</label>
                <input
                  type="text"
                  value={editProfileForm.headline}
                  onChange={(e) => setEditProfileForm({ ...editProfileForm, headline: e.target.value })}
                  placeholder="Staff Distributed Systems & AI Engineer"
                  style={{ width: '100%', padding: '0.5rem', background: '#090d16', border: '1px solid var(--border-color)', borderRadius: '6px', color: '#f8fafc' }}
                />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.25rem' }}>LinkedIn Profile URL</label>
                <input
                  type="url"
                  value={editProfileForm.linkedin_url}
                  onChange={(e) => setEditProfileForm({ ...editProfileForm, linkedin_url: e.target.value })}
                  placeholder="https://linkedin.com/in/username"
                  style={{ width: '100%', padding: '0.5rem', background: '#090d16', border: '1px solid var(--border-color)', borderRadius: '6px', color: '#f8fafc' }}
                />
              </div>
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.25rem' }}>Professional Summary</label>
              <textarea
                value={editProfileForm.summary}
                onChange={(e) => setEditProfileForm({ ...editProfileForm, summary: e.target.value })}
                rows={4}
                style={{ width: '100%', padding: '0.5rem', background: '#090d16', border: '1px solid var(--border-color)', borderRadius: '6px', color: '#f8fafc' }}
                placeholder="High-level overview of core expertise..."
              />
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem' }}>
              <button type="submit" className="btn btn-primary">
                Save Profile Changes
              </button>
            </div>
          </form>
        </div>
      )}

      {/* SUB-TAB 2: Work Experience */}
      {activeSubTab === 'experience' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {profile.experiences.length === 0 ? (
              <div className="card" style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>
                No work experiences added yet. Add one below or import via resume.
              </div>
            ) : (
              profile.experiences.map((exp) => (
                <div key={exp.id} className="card">
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '0.5rem' }}>
                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <h4 style={{ fontSize: '1.125rem', fontWeight: 600 }}>{exp.position}</h4>
                        <span style={{ color: 'var(--text-secondary)' }}>at</span>
                        <strong style={{ color: 'var(--accent-blue)' }}>{exp.company}</strong>
                      </div>
                      <div style={{ fontSize: '0.8125rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
                        {exp.start_date} – {exp.is_current ? 'Present' : exp.end_date || 'N/A'} {exp.location && `· ${exp.location}`}
                      </div>
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <button
                        onClick={() => handleToggleExpVerification(exp.id, exp.is_verified)}
                        className={`btn ${exp.is_verified ? 'btn-secondary' : 'btn-primary'}`}
                        style={{ fontSize: '0.75rem', padding: '0.25rem 0.625rem' }}
                      >
                        {exp.is_verified ? (
                          <span style={{ color: '#34d399', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                            <Check size={12} /> Verified Fact
                          </span>
                        ) : (
                          <span style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                            <AlertTriangle size={12} /> Verify Fact
                          </span>
                        )}
                      </button>

                      <button
                        onClick={() => handleDeleteExp(exp.id)}
                        className="btn btn-danger"
                        style={{ fontSize: '0.75rem', padding: '0.25rem 0.5rem' }}
                      >
                        <Trash2 size={14} />
                      </button>
                    </div>
                  </div>

                  {exp.description && (
                    <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', marginTop: '0.75rem' }}>
                      {exp.description}
                    </p>
                  )}

                  {exp.highlights && exp.highlights.length > 0 && (
                    <ul style={{ listStylePosition: 'inside', fontSize: '0.8125rem', color: 'var(--text-secondary)', marginTop: '0.75rem' }}>
                      {exp.highlights.map((h, i) => (
                        <li key={i} style={{ marginBottom: '0.25rem' }}>{h}</li>
                      ))}
                    </ul>
                  )}

                  {exp.skills_used && exp.skills_used.length > 0 && (
                    <div style={{ display: 'flex', gap: '0.375rem', flexWrap: 'wrap', marginTop: '0.75rem' }}>
                      {exp.skills_used.map((skill, i) => (
                        <span key={i} style={{ fontSize: '0.6875rem', padding: '0.125rem 0.375rem', background: '#090d16', border: '1px solid var(--border-color)', borderRadius: '4px', color: '#94a3b8' }}>
                          {skill}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              ))
            )}
          </div>

          {/* Add Experience Form */}
          <div className="card">
            <h4 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '1rem' }}>
              Add Work Experience
            </h4>
            <form onSubmit={handleAddExperience} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div className="grid-2">
                <div>
                  <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-muted)' }}>Company *</label>
                  <input
                    type="text"
                    value={newExpForm.company}
                    onChange={(e) => setNewExpForm({ ...newExpForm, company: e.target.value })}
                    required
                    style={{ width: '100%', padding: '0.5rem', background: '#090d16', border: '1px solid var(--border-color)', borderRadius: '6px', color: '#f8fafc' }}
                  />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-muted)' }}>Position / Title *</label>
                  <input
                    type="text"
                    value={newExpForm.position}
                    onChange={(e) => setNewExpForm({ ...newExpForm, position: e.target.value })}
                    required
                    style={{ width: '100%', padding: '0.5rem', background: '#090d16', border: '1px solid var(--border-color)', borderRadius: '6px', color: '#f8fafc' }}
                  />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-muted)' }}>Start Date</label>
                  <input
                    type="text"
                    placeholder="2022-01"
                    value={newExpForm.start_date}
                    onChange={(e) => setNewExpForm({ ...newExpForm, start_date: e.target.value })}
                    style={{ width: '100%', padding: '0.5rem', background: '#090d16', border: '1px solid var(--border-color)', borderRadius: '6px', color: '#f8fafc' }}
                  />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-muted)' }}>End Date</label>
                  <input
                    type="text"
                    placeholder="2024-03 (or check Current)"
                    value={newExpForm.end_date}
                    disabled={newExpForm.is_current}
                    onChange={(e) => setNewExpForm({ ...newExpForm, end_date: e.target.value })}
                    style={{ width: '100%', padding: '0.5rem', background: '#090d16', border: '1px solid var(--border-color)', borderRadius: '6px', color: '#f8fafc' }}
                  />
                </div>
              </div>

              <div>
                <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.8125rem', cursor: 'pointer' }}>
                  <input
                    type="checkbox"
                    checked={newExpForm.is_current}
                    onChange={(e) => setNewExpForm({ ...newExpForm, is_current: e.target.checked })}
                  />
                  <span>Currently working in this role</span>
                </label>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.25rem' }}>
                  Key Achievements & Highlights (1 per line)
                </label>
                <textarea
                  rows={3}
                  value={newExpForm.highlightsText}
                  onChange={(e) => setNewExpForm({ ...newExpForm, highlightsText: e.target.value })}
                  placeholder="Led migration of monolith to microservices...&#10;Decreased P99 latency by 45%..."
                  style={{ width: '100%', padding: '0.5rem', background: '#090d16', border: '1px solid var(--border-color)', borderRadius: '6px', color: '#f8fafc' }}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.25rem' }}>
                  Technologies Used (comma separated)
                </label>
                <input
                  type="text"
                  value={newExpForm.skillsText}
                  onChange={(e) => setNewExpForm({ ...newExpForm, skillsText: e.target.value })}
                  placeholder="Python, FastAPI, Redis, Docker"
                  style={{ width: '100%', padding: '0.5rem', background: '#090d16', border: '1px solid var(--border-color)', borderRadius: '6px', color: '#f8fafc' }}
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                <button type="submit" className="btn btn-primary">
                  <Plus size={14} />
                  <span>Save Experience</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* SUB-TAB 3: Education */}
      {activeSubTab === 'education' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {profile.educations.length === 0 ? (
              <div className="card" style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>
                No education records. Add one below.
              </div>
            ) : (
              profile.educations.map((edu) => (
                <div key={edu.id} className="card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <h4 style={{ fontSize: '1rem', fontWeight: 600 }}>{edu.degree}</h4>
                    <div style={{ fontSize: '0.875rem', color: 'var(--accent-blue)' }}>{edu.institution}</div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
                      {edu.field_of_study && `Field: ${edu.field_of_study} · `}
                      {edu.start_date && `${edu.start_date} – ${edu.end_date || 'Present'}`}
                      {edu.gpa && ` · GPA: ${edu.gpa}`}
                    </div>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <button
                      onClick={() => handleToggleEduVerification(edu.id, edu.is_verified)}
                      className={`btn ${edu.is_verified ? 'btn-secondary' : 'btn-primary'}`}
                      style={{ fontSize: '0.75rem', padding: '0.25rem 0.625rem' }}
                    >
                      {edu.is_verified ? (
                        <span style={{ color: '#34d399', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                          <Check size={12} /> Verified Fact
                        </span>
                      ) : (
                        <span>Verify Fact</span>
                      )}
                    </button>

                    <button onClick={() => handleDeleteEdu(edu.id)} className="btn btn-danger" style={{ fontSize: '0.75rem', padding: '0.25rem 0.5rem' }}>
                      <Trash2 size={14} />
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>

          <div className="card">
            <h4 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '1rem' }}>Add Education</h4>
            <form onSubmit={handleAddEducation} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div className="grid-2">
                <div>
                  <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-muted)' }}>Institution / University *</label>
                  <input
                    type="text"
                    value={newEduForm.institution}
                    onChange={(e) => setNewEduForm({ ...newEduForm, institution: e.target.value })}
                    required
                    style={{ width: '100%', padding: '0.5rem', background: '#090d16', border: '1px solid var(--border-color)', borderRadius: '6px', color: '#f8fafc' }}
                  />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-muted)' }}>Degree / Certificate *</label>
                  <input
                    type="text"
                    placeholder="B.S. Computer Science"
                    value={newEduForm.degree}
                    onChange={(e) => setNewEduForm({ ...newEduForm, degree: e.target.value })}
                    required
                    style={{ width: '100%', padding: '0.5rem', background: '#090d16', border: '1px solid var(--border-color)', borderRadius: '6px', color: '#f8fafc' }}
                  />
                </div>
              </div>
              <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                <button type="submit" className="btn btn-primary">
                  <Plus size={14} />
                  <span>Save Education</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* SUB-TAB 4: Skills Inventory */}
      {activeSubTab === 'skills' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          {/* Skill chips */}
          <div className="card">
            <h4 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '1rem' }}>
              Candidate Skills Inventory
            </h4>

            {profile.skills.length === 0 ? (
              <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>No skills added yet.</p>
            ) : (
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                {profile.skills.map((skill) => (
                  <div
                    key={skill.id}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.375rem',
                      padding: '0.375rem 0.625rem',
                      borderRadius: '6px',
                      backgroundColor: '#090d16',
                      border: `1px solid ${skill.is_verified ? '#10b981' : 'var(--border-color)'}`,
                      fontSize: '0.8125rem',
                    }}
                  >
                    <span style={{ fontWeight: 600 }}>{skill.name}</span>
                    <span style={{ fontSize: '0.6875rem', color: 'var(--text-muted)' }}>({skill.category})</span>
                    
                    <button
                      onClick={() => handleToggleSkillVerification(skill.id, skill.is_verified)}
                      style={{ background: 'none', border: 'none', cursor: 'pointer', color: skill.is_verified ? '#34d399' : '#fbbf24', padding: '0 2px' }}
                      title={skill.is_verified ? 'Verified Fact (Click to unverify)' : 'Unverified Draft (Click to verify)'}
                    >
                      {skill.is_verified ? <Check size={12} /> : <AlertTriangle size={12} />}
                    </button>

                    <button
                      onClick={() => handleDeleteSkill(skill.id)}
                      style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#64748b', padding: '0 2px' }}
                    >
                      <X size={12} />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Add Single Skill */}
          <div className="card">
            <h4 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '0.75rem' }}>Add Single Skill</h4>
            <form onSubmit={handleAddSkill} style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
              <input
                type="text"
                value={newSkillForm.name}
                onChange={(e) => setNewSkillForm({ ...newSkillForm, name: e.target.value })}
                placeholder="Skill Name (e.g. PyTorch, Rust)"
                style={{ flex: 1, minWidth: '180px', padding: '0.5rem', background: '#090d16', border: '1px solid var(--border-color)', borderRadius: '6px', color: '#f8fafc' }}
                required
              />
              <select
                value={newSkillForm.category}
                onChange={(e) => setNewSkillForm({ ...newSkillForm, category: e.target.value })}
                style={{ padding: '0.5rem', background: '#090d16', border: '1px solid var(--border-color)', borderRadius: '6px', color: '#f8fafc' }}
              >
                <option value="languages">Languages</option>
                <option value="frameworks">Frameworks & Libs</option>
                <option value="cloud_devops">Cloud & DevOps</option>
                <option value="databases">Databases</option>
                <option value="general">General</option>
              </select>
              <button type="submit" className="btn btn-secondary">
                <Plus size={14} />
                <span>Add Skill</span>
              </button>
            </form>
          </div>

          {/* Quick Bulk Add Skills */}
          <div className="card">
            <h4 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '0.5rem' }}>Quick Bulk Add Skills</h4>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.75rem' }}>
              Paste comma-separated or newline-separated technical competencies:
            </p>
            <form onSubmit={handleBulkAddSkills} style={{ display: 'flex', gap: '0.75rem' }}>
              <input
                type="text"
                value={bulkSkillsText}
                onChange={(e) => setBulkSkillsText(e.target.value)}
                placeholder="Python, FastAPI, PyTorch, React, TypeScript, Docker, PostgreSQL"
                style={{ flex: 1, padding: '0.5rem', background: '#090d16', border: '1px solid var(--border-color)', borderRadius: '6px', color: '#f8fafc' }}
              />
              <button type="submit" className="btn btn-primary">
                Bulk Add
              </button>
            </form>
          </div>
        </div>
      )}

      {/* SUB-TAB 5: Projects */}
      {activeSubTab === 'projects' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          <div className="grid-2">
            {profile.projects.map((p) => (
              <div key={p.id} className="card">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.5rem' }}>
                  <h4 style={{ fontSize: '1.125rem', fontWeight: 600 }}>{p.name}</h4>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <button
                      onClick={() => handleToggleProjectVerification(p.id, p.is_verified)}
                      className={`btn ${p.is_verified ? 'btn-secondary' : 'btn-primary'}`}
                      style={{ fontSize: '0.6875rem', padding: '0.2rem 0.5rem' }}
                    >
                      {p.is_verified ? '✓ Verified' : 'Verify'}
                    </button>
                    <button onClick={() => handleDeleteProject(p.id)} className="btn btn-danger" style={{ fontSize: '0.6875rem', padding: '0.2rem 0.4rem' }}>
                      <Trash2 size={12} />
                    </button>
                  </div>
                </div>
                {p.url && (
                  <a href={p.url} target="_blank" rel="noreferrer" style={{ fontSize: '0.75rem', color: '#38bdf8', textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '0.25rem', marginBottom: '0.5rem' }}>
                    <span>{p.url}</span>
                    <ExternalLink size={10} />
                  </a>
                )}
                {p.description && <p style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)' }}>{p.description}</p>}
              </div>
            ))}
          </div>

          <div className="card">
            <h4 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '1rem' }}>Add Project</h4>
            <form onSubmit={handleAddProject} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div className="grid-2">
                <div>
                  <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-muted)' }}>Project Name *</label>
                  <input
                    type="text"
                    value={newProjectForm.name}
                    onChange={(e) => setNewProjectForm({ ...newProjectForm, name: e.target.value })}
                    required
                    style={{ width: '100%', padding: '0.5rem', background: '#090d16', border: '1px solid var(--border-color)', borderRadius: '6px', color: '#f8fafc' }}
                  />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-muted)' }}>Project URL</label>
                  <input
                    type="url"
                    value={newProjectForm.url}
                    onChange={(e) => setNewProjectForm({ ...newProjectForm, url: e.target.value })}
                    placeholder="https://github.com/username/project"
                    style={{ width: '100%', padding: '0.5rem', background: '#090d16', border: '1px solid var(--border-color)', borderRadius: '6px', color: '#f8fafc' }}
                  />
                </div>
              </div>
              <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                <button type="submit" className="btn btn-primary">
                  <Plus size={14} />
                  <span>Save Project</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* SUB-TAB 6: Resume Importer */}
      {activeSubTab === 'importer' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          <div className="card" style={{ borderLeft: '4px solid #38bdf8' }}>
            <h3 style={{ fontSize: '1.125rem', fontWeight: 600, marginBottom: '0.5rem' }}>
              Untrusted Resume Importer & Ingestion Engine
            </h3>
            <p style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
              Imported resumes are securely saved in local storage (never in Git) and parsed into draft candidate facts.
              <strong> Security Policy:</strong> All imported facts are strictly tagged as <code>UNTRUSTED_DRAFT</code> and will NOT be exposed to the LLM until explicitly reviewed and verified by you.
            </p>
          </div>

          <div className="grid-2">
            {/* Paste Raw Text */}
            <div className="card">
              <h4 style={{ fontSize: '0.9375rem', fontWeight: 600, marginBottom: '0.75rem' }}>
                Paste Resume Text or Markdown
              </h4>
              <form onSubmit={handleImportText} style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                <input
                  type="text"
                  value={importLabel}
                  onChange={(e) => setImportLabel(e.target.value)}
                  placeholder="Label (e.g. Master Tech Resume 2026)"
                  style={{ width: '100%', padding: '0.5rem', background: '#090d16', border: '1px solid var(--border-color)', borderRadius: '6px', color: '#f8fafc' }}
                />
                <textarea
                  rows={8}
                  value={rawTextToImport}
                  onChange={(e) => setRawTextToImport(e.target.value)}
                  placeholder="Paste free-form resume text, markdown, or JSON resume standard..."
                  style={{ width: '100%', padding: '0.5rem', background: '#090d16', border: '1px solid var(--border-color)', borderRadius: '6px', color: '#f8fafc', fontFamily: 'monospace', fontSize: '0.75rem' }}
                />
                <button type="submit" disabled={importing || !rawTextToImport.trim()} className="btn btn-primary">
                  <FileUp size={14} />
                  <span>{importing ? 'Parsing...' : 'Parse Untrusted Text'}</span>
                </button>
              </form>
            </div>

            {/* Upload File */}
            <div className="card">
              <h4 style={{ fontSize: '0.9375rem', fontWeight: 600, marginBottom: '0.75rem' }}>
                Upload Resume Document
              </h4>
              <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '1rem' }}>
                Accepted extensions: <code>.txt</code>, <code>.md</code>, <code>.json</code>, <code>.pdf</code>, <code>.docx</code>.
              </p>
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
                  <input type="file" onChange={handleFileUpload} style={{ display: 'none' }} />
                </label>
              </div>
            </div>
          </div>

          {/* Parsed Draft Fact Preview */}
          {lastRawImport && (
            <div className="card" style={{ borderTop: '3px solid #fbbf24' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem', flexWrap: 'wrap', gap: '0.5rem' }}>
                <div>
                  <h4 style={{ fontSize: '1rem', fontWeight: 700 }}>
                    Parsed Draft Preview: {lastRawImport.filename}
                  </h4>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                    SHA-256: <code>{lastRawImport.file_hash.slice(0, 16)}...</code> · Status: <span className="badge badge-yellow">Untrusted Draft</span>
                  </div>
                </div>

                <button
                  onClick={() => handleApplyImportToProfile(lastRawImport.id)}
                  className="btn btn-primary"
                >
                  <span>Apply to Candidate Profile (As Unverified)</span>
                </button>
              </div>

              <pre className="code-block" style={{ maxHeight: '250px', overflowY: 'auto' }}>
                {JSON.stringify(lastRawImport.parsed_data, null, 2)}
              </pre>
            </div>
          )}
        </div>
      )}

      {/* MODAL: Verified LLM Ground Truth Context Preview */}
      {showGroundTruthModal && (
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
              maxWidth: '800px',
              width: '100%',
              maxHeight: '90vh',
              overflowY: 'auto',
              backgroundColor: '#0f172a',
              border: '1px solid #38bdf8',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#38bdf8' }}>
                <Bot size={22} />
                <h3 style={{ fontSize: '1.125rem', fontWeight: 700 }}>
                  Downstream LLM Verified Ground Truth Service Boundary
                </h3>
              </div>
              <button onClick={() => setShowGroundTruthModal(false)} className="btn btn-secondary" style={{ padding: '0.25rem 0.5rem' }}>
                <X size={16} />
              </button>
            </div>

            <p style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)', marginBottom: '1rem' }}>
              This is the exact deterministic context delivered to downstream LLM modules. Any unverified fact is strictly filtered out.
            </p>

            {loadingGroundTruth ? (
              <p style={{ color: 'var(--text-muted)' }}>Querying authoritative service boundary...</p>
            ) : groundTruthContext ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                  <span className="badge badge-green">Verified Experiences: {groundTruthContext.stats.verified_experiences_count}</span>
                  <span className="badge badge-green">Verified Skills: {groundTruthContext.stats.verified_skills_count}</span>
                  <span className="badge badge-green">Verified Educations: {groundTruthContext.stats.verified_educations_count}</span>
                </div>

                <pre className="code-block" style={{ maxHeight: '400px', overflowY: 'auto', whiteSpace: 'pre-wrap' }}>
                  {groundTruthContext.formatted_llm_prompt_context}
                </pre>
              </div>
            ) : null}
          </div>
        </div>
      )}
    </div>
  );
};
