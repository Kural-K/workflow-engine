import { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, NavLink, Navigate, useNavigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { GitBranch, Play, ClipboardList, LogOut } from 'lucide-react';
import toast from 'react-hot-toast';
import Login from './pages/Login';
import WorkflowList from './pages/WorkflowList';
import WorkflowEditor from './pages/WorkflowEditor';
import ExecutionPage from './pages/ExecutionPage';
import AuditLog from './pages/AuditLog';
import './index.css';

function Sidebar({ user, onLogout }) {
  const links = [
    { to: '/workflows', icon: <GitBranch />, label: 'Workflows' },
    { to: '/executions', icon: <Play />, label: 'Run Workflow' },
    { to: '/audit', icon: <ClipboardList />, label: 'Audit Log' },
  ];
  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <div className="logo-icon">⚡</div>
        <span>FlowEngine</span>
      </div>
      <nav className="sidebar-nav">
        <div className="nav-section-label">Navigation</div>
        {links.map(l => (
          <NavLink key={l.to} to={l.to} className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}>
            {l.icon} {l.label}
          </NavLink>
        ))}
      </nav>
      {/* User info + logout */}
      <div style={{ padding: '12px 14px', borderTop: '1px solid var(--border)' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 9 }}>
            <div style={{
              width: 30, height: 30, borderRadius: '50%',
              background: 'linear-gradient(135deg, var(--accent), var(--pink))',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: 13, fontWeight: 700, color: '#fff', flexShrink: 0,
            }}>
              {user?.username?.[0]?.toUpperCase()}
            </div>
            <div>
              <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text)' }}>{user?.username}</div>
              <div style={{ fontSize: 11, color: 'var(--text3)' }}>{user?.role}</div>
            </div>
          </div>
          <button onClick={onLogout} style={{
            background: 'none', border: 'none',
            color: 'var(--text3)', cursor: 'pointer', padding: 4,
            display: 'flex', alignItems: 'center',
            borderRadius: 6, transition: 'all 0.15s',
          }}
            onMouseEnter={e => { e.currentTarget.style.background = 'rgba(248,113,113,0.1)'; e.currentTarget.style.color = 'var(--red)'; }}
            onMouseLeave={e => { e.currentTarget.style.background = 'none'; e.currentTarget.style.color = 'var(--text3)'; }}
            title="Logout"
          >
            <LogOut size={15} />
          </button>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 7, fontSize: 11, color: 'var(--text3)' }}>
          <div style={{ width: 7, height: 7, borderRadius: '50%', background: 'var(--green)', boxShadow: '0 0 8px var(--green)', flexShrink: 0 }} />
          All systems operational
        </div>
      </div>
    </aside>
  );
}

function AppLayout({ user, onLogout }) {
  return (
    <div className="layout">
      <Sidebar user={user} onLogout={onLogout} />
      <main className="main">
        <Routes>
          <Route path="/" element={<Navigate to="/workflows" replace />} />
          <Route path="/workflows" element={<WorkflowList />} />
          <Route path="/workflows/:id/edit" element={<WorkflowEditor />} />
          <Route path="/workflows/new" element={<WorkflowEditor />} />
          <Route path="/executions" element={<ExecutionPage />} />
          <Route path="/executions/:id" element={<ExecutionPage />} />
          <Route path="/audit" element={<AuditLog />} />
        </Routes>
      </main>
    </div>
  );
}

export default function App() {
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem('fe_user');
    return saved ? JSON.parse(saved) : null;
  });

  const handleLogin = (u) => setUser(u);

  const handleLogout = () => {
    localStorage.removeItem('fe_user');
    setUser(null);
    toast.success('Logged out successfully!');
  };

  return (
    <BrowserRouter>
      <Toaster position="top-right" toastOptions={{
        style: {
          background: '#1e1b2e', color: '#f0eeff',
          border: '1px solid #3d3860', fontSize: '13.5px',
          borderRadius: '10px', boxShadow: '0 8px 32px rgba(0,0,0,0.4)',
        }
      }} />
      {!user ? (
        <Routes>
          <Route path="*" element={<Login onLogin={handleLogin} />} />
        </Routes>
      ) : (
        <AppLayout user={user} onLogout={handleLogout} />
      )}
    </BrowserRouter>
  );
}
