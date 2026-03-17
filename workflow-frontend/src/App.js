import { BrowserRouter, Routes, Route, NavLink, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { GitBranch, Play, ClipboardList, Zap } from 'lucide-react';
import WorkflowList from './pages/WorkflowList';
import WorkflowEditor from './pages/WorkflowEditor';
import ExecutionPage from './pages/ExecutionPage';
import AuditLog from './pages/AuditLog';
import './index.css';

function Sidebar() {
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
      <div className="sidebar-footer">
        <div className="dot"></div>
        All systems operational
      </div>
    </aside>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <Toaster position="top-right" toastOptions={{
        style: {
          background: '#1e1b2e',
          color: '#f0eeff',
          border: '1px solid #3d3860',
          fontSize: '13.5px',
          borderRadius: '10px',
          boxShadow: '0 8px 32px rgba(0,0,0,0.4)',
        }
      }} />
      <div className="layout">
        <Sidebar />
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
    </BrowserRouter>
  );
}
