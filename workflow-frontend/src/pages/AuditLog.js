import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import { Eye, RefreshCw, Search } from 'lucide-react';
import { getExecutions, getWorkflows } from '../api/client';

const STATUS_BADGE = {
  pending:     'badge-yellow',
  in_progress: 'badge-blue',
  completed:   'badge-green',
  failed:      'badge-red',
  canceled:    'badge-gray',
};

export default function AuditLog() {
  const [executions, setExecutions] = useState([]);
  const [meta, setMeta] = useState({});
  const [workflows, setWorkflows] = useState([]);
  const [filter, setFilter] = useState({ workflow_id: '', status: '', page: 1 });
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    getWorkflows({ page_size: 100 }).then(r => setWorkflows(r.data.data)).catch(() => {});
  }, []);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const params = { page: filter.page, page_size: 15 };
      if (filter.workflow_id) params.workflow_id = filter.workflow_id;
      if (filter.status) params.status = filter.status;
      const res = await getExecutions(params);
      setExecutions(res.data.data);
      setMeta(res.data.meta);
    } catch (e) { toast.error(e.message); }
    finally { setLoading(false); }
  }, [filter]);

  useEffect(() => { load(); }, [load]);

  const totalPages = Math.ceil((meta.total || 0) / 15);
  const wfName = (id) => workflows.find(w => w.id === id)?.name || id?.slice(0, 12) + '...';
  const dur = (ex) => {
    if (!ex.started_at || !ex.ended_at) return '—';
    const ms = new Date(ex.ended_at) - new Date(ex.started_at);
    return ms < 1000 ? `${ms}ms` : `${(ms/1000).toFixed(1)}s`;
  };

  return (
    <>
      <div className="page-header">
        <div>
          <h1>Audit Log</h1>
          <p style={{ color: 'var(--text3)', fontSize: 13, marginTop: 3 }}>{meta.total || 0} executions total</p>
        </div>
        <button className="btn btn-ghost btn-sm" onClick={load}><RefreshCw size={14} /> Refresh</button>
      </div>

      <div className="page-body">
        <div className="flex gap-2" style={{ marginBottom: 20, flexWrap: 'wrap' }}>
          <select style={{ background: 'var(--bg3)', border: '1px solid var(--border)', borderRadius: 'var(--radius)', color: 'var(--text)', padding: '8px 12px', fontSize: 13.5, minWidth: 200 }}
            value={filter.workflow_id} onChange={e => setFilter(f => ({ ...f, workflow_id: e.target.value, page: 1 }))}>
            <option value="">All Workflows</option>
            {workflows.map(w => <option key={w.id} value={w.id}>{w.name}</option>)}
          </select>
          <select style={{ background: 'var(--bg3)', border: '1px solid var(--border)', borderRadius: 'var(--radius)', color: 'var(--text)', padding: '8px 12px', fontSize: 13.5 }}
            value={filter.status} onChange={e => setFilter(f => ({ ...f, status: e.target.value, page: 1 }))}>
            <option value="">All Statuses</option>
            {['pending','in_progress','completed','failed','canceled'].map(s => <option key={s} value={s}>{s}</option>)}
          </select>
        </div>

        <div className="card">
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Execution ID</th>
                  <th>Workflow</th>
                  <th>Version</th>
                  <th>Status</th>
                  <th>Started By</th>
                  <th>Start Time</th>
                  <th>Duration</th>
                  <th>Steps</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {executions.length === 0 ? (
                  <tr><td colSpan={9}>
                    <div className="empty">
                      <Search />
                      <p>{loading ? 'Loading...' : 'No executions found.'}</p>
                    </div>
                  </td></tr>
                ) : executions.map(ex => (
                  <tr key={ex.id}>
                    <td><span className="mono" style={{ color: 'var(--text2)' }}>{ex.id?.slice(0, 14)}...</span></td>
                    <td style={{ fontWeight: 500 }}>{wfName(ex.workflow_id)}</td>
                    <td><span className="mono" style={{ color: 'var(--text3)' }}>v{ex.workflow_version}</span></td>
                    <td><span className={`badge ${STATUS_BADGE[ex.status] || 'badge-gray'}`}>{ex.status}</span></td>
                    <td style={{ color: 'var(--text2)' }}>{ex.triggered_by}</td>
                    <td style={{ color: 'var(--text3)', fontSize: 12 }}>
                      {new Date(ex.started_at).toLocaleString()}
                    </td>
                    <td style={{ color: 'var(--text2)', fontFamily: 'var(--mono)', fontSize: 12 }}>{dur(ex)}</td>
                    <td><span className="badge badge-gray">{ex.logs?.length || 0}</span></td>
                    <td>
                      <button className="btn btn-ghost btn-sm" onClick={() => navigate(`/executions/${ex.id}`)}>
                        <Eye size={13} /> View
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {totalPages > 1 && (
          <div className="pagination">
            <span>{meta.total} total</span>
            {Array.from({ length: Math.min(totalPages, 8) }, (_, i) => i + 1).map(p => (
              <button key={p} className={p === filter.page ? 'active' : ''} onClick={() => setFilter(f => ({ ...f, page: p }))}>{p}</button>
            ))}
          </div>
        )}
      </div>
    </>
  );
}
