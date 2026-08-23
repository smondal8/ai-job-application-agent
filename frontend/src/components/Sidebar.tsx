import React from 'react';
import {
  LayoutDashboard,
  GitMerge,
  Database,
  Sliders,
  AlertOctagon,
  ShieldCheck,
} from 'lucide-react';

export type NavTab = 'overview' | 'pipeline' | 'schemas' | 'config' | 'error-lab';

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
      id: 'pipeline',
      label: 'Pipeline Architecture',
      icon: <GitMerge size={18} />,
      badge: '6 Stages',
    },
    {
      id: 'schemas',
      label: 'Database Models',
      icon: <Database size={18} />,
      badge: '7 Tables',
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
          <ShieldCheck size={20} color="#38bdf8" />
          <span style={{ fontWeight: 600, fontSize: '0.875rem', letterSpacing: '0.025em' }}>
            Phase 1 Active
          </span>
        </div>
        <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', lineHeight: 1.4 }}>
          FastAPI + SQLite + Alembic + React/TS foundational control plane.
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
            style={{ width: '100%', border: 'none', background: activeTab === item.id ? 'rgba(56, 189, 248, 0.12)' : 'transparent', textAlign: 'left' }}
          >
            {item.icon}
            <span style={{ flex: 1 }}>{item.label}</span>
            {item.badge && (
              <span style={{ fontSize: '0.6875rem', padding: '0.125rem 0.375rem', borderRadius: '4px', backgroundColor: '#1e293b', color: 'var(--text-secondary)' }}>
                {item.badge}
              </span>
            )}
          </button>
        ))}
      </nav>

      <div style={{ padding: '1rem 1.25rem', borderTop: '1px solid var(--border-color)', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
        <div>Branch: <code style={{ color: '#38bdf8' }}>feature/phase-01</code></div>
        <div>Storage: <code style={{ color: 'var(--text-secondary)' }}>./data/storage</code></div>
      </div>
    </aside>
  );
};
