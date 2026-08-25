import React from 'react';
import {
  LayoutDashboard,
  Briefcase,
  FileText,
  Brain,
  Compass,
  Building,
  UserCheck,
  GitMerge,
  Database,
  Sliders,
  AlertOctagon,
  Sparkles,
  Activity,
} from 'lucide-react';

export type NavTab = 'overview' | 'observability' | 'applications' | 'tailoring' | 'analysis' | 'discovery' | 'jobs' | 'profile' | 'pipeline' | 'schemas' | 'config' | 'error-lab';

interface SidebarProps {
  activeTab: NavTab;
  onSelectTab: (tab: NavTab) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ activeTab, onSelectTab }) => {
  const navItems: { id: NavTab; label: string; icon: React.ReactNode; badge?: string }[] = [
    {
      id: 'overview',
      label: 'System Overview',
      icon: <LayoutDashboard size={18} />,
      badge: 'Phase 1',
    },
    {
      id: 'profile',
      label: 'Candidate Profile & CV',
      icon: <UserCheck size={18} />,
      badge: 'Phase 2',
    },
    {
      id: 'jobs',
      label: 'Job DB & Ingestion',
      icon: <Building size={18} />,
      badge: 'Phase 3',
    },
    {
      id: 'discovery',
      label: 'Job Discovery & Feeds',
      icon: <Compass size={18} />,
      badge: 'Phase 4',
    },
    {
      id: 'analysis',
      label: 'JD Analysis & Matching',
      icon: <Brain size={18} />,
      badge: 'Phase 5',
    },
    {
      id: 'tailoring',
      label: 'Resume Tailoring Studio',
      icon: <FileText size={18} />,
      badge: 'Phase 6',
    },
    {
      id: 'applications',
      label: 'Applications & Staging',
      icon: <Briefcase size={18} />,
      badge: 'Phases 7–10',
    },
    {
      id: 'observability',
      label: 'Observability & Backups',
      icon: <Activity size={18} />,
      badge: 'Phase 11',
    },
    {
      id: 'pipeline',
      label: 'Pipeline Architecture',
      icon: <GitMerge size={18} />,
      badge: '12 Stages',
    },
    {
      id: 'schemas',
      label: 'Database Models',
      icon: <Database size={18} />,
      badge: '19 Tables',
    },
    {
      id: 'config',
      label: 'Configuration',
      icon: <Sliders size={18} />,
    },
    {
      id: 'error-lab',
      label: 'Error Contract Lab',
      icon: <AlertOctagon size={18} />,
    },
  ];

  const getBadgeStyle = (badge?: string) => {
    if (!badge) return {};
    if (badge === 'Phase 1' || badge === 'Phase 2' || badge === 'Phase 6' || badge === 'Phase 12') {
      return { backgroundColor: 'rgba(52, 211, 153, 0.18)', color: '#34d399' };
    }
    if (badge === 'Phases 7–10' || badge === 'Phase 11' || badge === 'Phase 4' || badge === 'Phase 3') {
      return { backgroundColor: 'rgba(56, 189, 248, 0.18)', color: '#38bdf8' };
    }
    if (badge === 'Phase 5') {
      return { backgroundColor: 'rgba(192, 132, 252, 0.18)', color: '#c084fc' };
    }
    return { backgroundColor: 'rgba(148, 163, 184, 0.12)', color: 'var(--text-secondary)' };
  };

  return (
    <aside className="sidebar">
      <div style={{ padding: '1.5rem 1.25rem', borderBottom: '1px solid var(--border-color)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
          <Sparkles size={20} color="#34d399" />
          <span style={{ fontWeight: 600, fontSize: '0.875rem', letterSpacing: '0.025em' }}>
            Phase 12 Complete (v1.0.0)
          </span>
        </div>
        <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', lineHeight: 1.4 }}>
          Full System Stabilization, End-to-End Test Verification, Negative Security Guarantees & Production Runbooks.
        </p>
      </div>

      <nav style={{ padding: '0.75rem', flex: 1 }}>
        <div style={{ fontSize: '0.6875rem', fontWeight: 700, textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: '0.625rem', paddingLeft: '0.5rem' }}>
          Navigation
        </div>
        {navItems.map((item) => (
          <button
            key={item.id}
            onClick={() => onSelectTab(item.id)}
            className={`nav-item ${activeTab === item.id ? 'active' : ''}`}
            title={item.label}
            style={{
              width: '100%',
              border: 'none',
              background: activeTab === item.id ? 'rgba(52, 211, 153, 0.12)' : 'transparent',
              textAlign: 'left',
              display: 'flex',
              alignItems: 'center',
              gap: '0.625rem',
            }}
          >
            {item.icon}
            <span style={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{item.label}</span>
            {item.badge && (
              <span
                style={{
                  fontSize: '0.6875rem',
                  padding: '0.125rem 0.375rem',
                  borderRadius: '4px',
                  whiteSpace: 'nowrap',
                  flexShrink: 0,
                  fontWeight: 600,
                  ...getBadgeStyle(item.badge),
                }}
              >
                {item.badge}
              </span>
            )}
          </button>
        ))}
      </nav>

      <div style={{ padding: '1rem 1.25rem', borderTop: '1px solid var(--border-color)', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
        <div>Branch: <code style={{ color: '#34d399' }}>feature/phase-12</code></div>
        <div>LLM: <code style={{ color: 'var(--text-secondary)' }}>Ollama (qwen3:8b)</code></div>
      </div>
    </aside>
  );
};
