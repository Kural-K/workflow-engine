import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import { Plus, Search, Edit2, Trash2, Play, GitBranch, RefreshCw, Layers, CheckCircle, Activity } from 'lucide-react';
import { getWorkflows, deleteWorkflow, getExecutions } from '../api/client';

const STATUS_BADGE = { true: ['badge-green','Active'], false: ['badge-gray','Inactive'] };

export default function WorkflowList() {
  const [workflows, setWorkflows] = useState([]);
  const [meta, setMeta] = useState({});
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);
  const [execStats, setExecStats] = useState({ total: 0, completed: 0 });
  const navigate = useNavigate();

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [wfRes, exRes] = await Promise.all([
        getWorkflows({ search, page, page_size: 10 }),
        getExecutions({ page_size: 1 })
      ]);
      setWorkflows(wfRes.data.data);
      setMeta(wfRes.data.meta);
      setExecStats({ total: exRes.data.meta.total || 0 });
    } catch (e) { toast.error(e.message); }
    finally { setLoading(false); }
  }, [search, page]);

  useEffect(() => { load(); }, [load]);

  const handleDelete = async (id, name) => {
    if (!window.confirm(`Delete "${name}"? This cannot be undone.`)) return;
    try { await deleteWorkflow(id); toast.success('Workflow deleted'); load(); }
    catch (e) { toast.error(e.message); }
  };

  const totalPages = Math.ceil((meta.total || 0) / (meta.page_size || 10));

  return (
    <>
      <div className="page-header">
        <div>
          <h1>Workflows</h1>
          <p style={{ color: 'var(--text3)', fontSize: 13, marginTop: 2 }}>
            Design, manage and execute your automation workflows
          </p>
        </div>
        <div className="flex gap-2">
          <button className="btn btn-ghost btn-sm" onClick={load}>
            <RefreshCw size={14} className={loading ? 'spin' : ''} /> Refresh
          </button>
          <button className="btn btn-primary" onClick={() => navigate('/workflows/new')}>
            <Plus size={15} /> New Workflow
          </button>
        </div>
      </div>

      <div className="page-body">
        {/* Stats */}
        <div className="stats-bar">
          <div className="stat-card">
            <div className="stat-icon" style={{ background: 'rgba(124,58,237,0.15)' }}>
              <GitBranch size={20} style={{ color: 'var(--accent3)' }} />
            </div>
            <div>
              <div className="stat-value">{meta.total || 0}</div>
              <div className="stat-label">Total Workflows</div>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-icon" style={{ background: 'rgba(52,211,153,0.12)' }}>
              <CheckCircle size={20} style={{ color: 'var(--green)' }} />
            </div>
            <div>
              <div className="stat-value">{workflows.filter(w => w.is_active).length}</div>
              <div className="stat-label">Active</div>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-icon" style={{ background: 'rgba(96,165,250,0.12)' }}>
              <Activity size={20} style={{ color: 'var(--blue)' }} />
            </div>
            <div>
              <div className="stat-value">{execStats.total}</div>
              <div className="stat-label">Total Executions</div>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-icon" style={{ background: 'rgba(251,191,36,0.12)' }}>
              <Layers size={20} style={{ color: 'var(--yellow)' }} />
            </div>
            <div>
              <div className="stat-value">{workflows.reduce((a, w) => a + (w.step_count || 0), 0)}</div>
              <div className="stat-label">Total Steps</div>
            </div>
          </div>
        </div>

        <div className="flex gap-2" style={{ marginBottom: 16 }}>
          <div className="search-bar" style={{ flex: 1, maxWidth: 380 }}>
            <Search />
            <input placeholder="Search workflows..." value={search}
              onChange={e => { setSearch(e.target.value); setPage(1); }} />
          </div>
        </div>

        <div className="card">
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Steps</th>
                  <th>Version</th>
                  <th>Status</th>
                  <th>Updated</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {workflows.length === 0 ? (
                  <tr><td colSpan={6}>
                    <div className="empty">
                      <GitBranch />
                      <p>{loading ? 'Loading workflows...' : 'No workflows yet.\nCreate your first one!'}</p>
                      {!loading && <button className="btn btn-primary btn-sm" onClick={() => navigate('/workflows/new')}><Plus size={13} /> Create Workflow</button>}
                    </div>
                  </td></tr>
                ) : workflows.map(w => {
                  const [cls, label] = STATUS_BADGE[w.is_active] || STATUS_BADGE[false];
                  return (
                    <tr key={w.id}>
                      <td>
                        <div style={{ fontWeight: 600, fontSize: 14 }}>{w.name}</div>
                        {w.description && <div style={{ color: 'var(--text3)', fontSize: 12, marginTop: 2 }}>{w.description}</div>}
                      </td>
                      <td><span className="badge badge-purple">{w.step_count || 0} steps</span></td>
                      <td><span className="mono" style={{ color: 'var(--text2)', background: 'var(--bg3)', padding: '3px 8px', borderRadius: 6, border: '1px solid var(--border)' }}>v{w.version}</span></td>
                      <td><span className={`badge ${cls}`}>{label}</span></td>
                      <td style={{ color: 'var(--text3)', fontSize: 12 }}>{new Date(w.updated_at).toLocaleDateString()}</td>
                      <td>
                        <div className="flex gap-2">
                          <button className="btn btn-ghost btn-sm" onClick={() => navigate(`/workflows/${w.id}/edit`)}><Edit2 size={13} /> Edit</button>
                          <button className="btn btn-success btn-sm" onClick={() => navigate(`/executions?workflow=${w.id}`)}><Play size={13} /> Run</button>
                          <button className="btn btn-danger btn-sm" onClick={() => handleDelete(w.id, w.name)}><Trash2 size={13} /></button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>

        {totalPages > 1 && (
          <div className="pagination">
            <span>{meta.total} total</span>
            {Array.from({ length: totalPages }, (_, i) => i + 1).map(p => (
              <button key={p} className={p === page ? 'active' : ''} onClick={() => setPage(p)}>{p}</button>
            ))}
          </div>
        )}
      </div>
    </>
  );
}
