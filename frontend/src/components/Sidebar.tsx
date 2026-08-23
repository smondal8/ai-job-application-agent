import React from 'react';
import {
  LayoutDashboard,
  Compass,
  Briefcase,
  UserCheck,
  Brain,
  GitMerge,
  Database,
  Sliders,
  AlertOctagon,
  Sparkles,
} from 'lucide-react';

export type NavTab = 'overview' | 'analysis' | 'discovery' | 'jobs' | 'profile' | 'pipeline' | 'schemas' | 'config' | 'error-lab';

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
    },
    {
      id: 'analysis',
      label: 'JD Analysis & Matching',
      icon: <Brain size={18} />,
      badge: 'Phase 5',
    },
    {
      id: 'discovery',
      label: 'Job Discovery & Feeds',
      icon: <Compass size={18} />,
      badge: 'Phase 4',
    },
    {
      id: 'jobs',
      label: 'Job DB & Ingestion',
      icon: <Briefcase size={18} />,
      badge: 'Phase 3',
    },
    {
      id: 'profile',
      label: 'Candidate Profile & CV',
      icon: <UserCheck size={18} />,
      badge: 'Phase 2',
    },
    {
      id: 'pipeline',
      label: 'Pipeline Architecture',
      icon: <GitMerge size={18} />,
      badge: '7 Stages',
    },
    {
      id: 'schemas',
      label: 'Database Models',
      icon: <Database size={18} />,
      badge: '17 Tables',
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

  return (
    <aside className="sidebar">
      <div style={{ padding: '1.5rem 1.25rem', borderBottom: '1px solid var(--border-color)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
          <Sparkles size={20} color="#c084fc" />
          <span style={{ fontWeight: 600, fontSize: '0.875rem', letterSpacing: '0.025em' }}>
            Phase 5 Active
          </span>
        </div>
        <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', lineHeight: 1.4 }}>
          Local Ollama LLM (qwen3:8b) on Apple Silicon GPU for JD Analysis & Candidate Matching.
        </p>
      </div>

      <nav style={{ padding: '1rem', flex: 1 }}>
        <div style={{ fontSize: '0.6875rem', fontWeight: 700, textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: '0.75rem', paddingLeft: '0.5rem' }}>
          Navigation
        </div>
        {navItems.map((item) => (
          <button
            key={item.id}
            onClick={() => onSelectTab(item.id)}
            className={`nav-item ${activeTab === item.id ? 'active' : ''}`}
            style={{ width: '100%', border: 'none', background: activeTab === item.id ? 'rgba(192, 132, 252, 0.12)' : 'transparent', textAlign: 'left' }}
          >
            {item.icon}
            <span style={{ flex: 1 }}>{item.label}</span>
            {item.badge && (
              <span
                style={{
                  fontSize: '0.6875rem',
                  padding: '0.125rem 0.375rem',
                  borderRadius: '4px',
                  backgroundColor:
                    item.badge === 'Phase 5'
                      ? 'rgba(192, 132, 252, 0.2)'
                      : item.badge === 'Phase 4'
                      ? 'rgba(56, 189, 248, 0.2)'
                      : item.badge === 'Phase 3'
                      ? 'rgba(56, 189, 248, 0.15)'
                      : item.badge === 'Phase 2'
                      ? 'rgba(52, 211, 153, 0.2)'
                      : '#1e293b',
                  color:
                    item.badge === 'Phase 5'
                      ? '#c084fc'
                      : item.badge === 'Phase 4'
                      ? '#38bdf8'
                      : item.badge === 'Phase 3'
                      ? '#38bdf8'
                      : item.badge === 'Phase 2'
                      ? '#34d399'
                      : 'var(--text-secondary)',
                }}
              >
                {item.badge}
              </span>
            )}
          </button>
        ))}
      </nav>

      <div style={{ padding: '1rem 1.25rem', borderTop: '1px solid var(--border-color)', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
        <div>Branch: <code style={{ color: '#c084fc' }}>feature/phase-05</code></div>
        <div>LLM: <code style={{ color: 'var(--text-secondary)' }}>Ollama (qwen3:8b)</code></div>
      </div>
    </aside>
  );
};
