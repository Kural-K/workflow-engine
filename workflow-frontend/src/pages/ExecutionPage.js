import { useState, useEffect } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import toast from 'react-hot-toast';
import { Play, ChevronDown, ChevronUp, CheckCircle, XCircle, Clock, AlertTriangle, ThumbsUp, RefreshCw, XOctagon } from 'lucide-react';
import { getWorkflows, getWorkflow, executeWorkflow, getExecution, approveStep, cancelExecution, retryExecution } from '../api/client';

const STATUS_CONFIG = {
  pending:     { color: 'var(--yellow)', icon: <Clock size={14} />, badge: 'badge-yellow' },
  in_progress: { color: 'var(--accent)', icon: <RefreshCw size={14} />, badge: 'badge-blue' },
  completed:   { color: 'var(--green)', icon: <CheckCircle size={14} />, badge: 'badge-green' },
  failed:      { color: 'var(--red)', icon: <XCircle size={14} />, badge: 'badge-red' },
  canceled:    { color: 'var(--text3)', icon: <XOctagon size={14} />, badge: 'badge-gray' },
};

function LogEntry({ log }) {
  const [open, setOpen] = useState(log.status !== 'completed');
  const cfg = STATUS_CONFIG[log.status] || STATUS_CONFIG.pending;

  return (
    <div className="log-entry">
      <div className="log-header" onClick={() => setOpen(o => !o)}>
        <div className="flex gap-2" style={{ flex: 1 }}>
          <span style={{ color: cfg.color }}>{cfg.icon}</span>
          <span style={{ fontWeight: 600, fontSize: 13.5 }}>{log.step_name}</span>
          <span className={`badge ${cfg.badge}`}>{log.status}</span>
          <span className="badge badge-gray">{log.step_type}</span>
        </div>
        <div className="flex gap-2" style={{ color: 'var(--text3)', fontSize: 12 }}>
          {log.started_at && <span>{new Date(log.started_at).toLocaleTimeString()}</span>}
          {open ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
        </div>
      </div>
      {open && (
        <div className="log-body">
          {log.evaluated_rules?.length > 0 && (
            <div style={{ marginBottom: 12 }}>
              <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text3)', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: 8 }}>Rules Evaluated</div>
              {log.evaluated_rules.map((r, i) => (
                <div key={i} className="rule-row">
                  <div className={`rule-check ${r.result ? 'pass' : 'fail'}`}>{r.result ? '✓' : '✗'}</div>
                  <div>
                    <code style={{ fontFamily: 'var(--mono)', fontSize: 12, color: r.result ? 'var(--green)' : 'var(--text2)' }}>{r.rule}</code>
                    {r.error && <div style={{ color: 'var(--red)', fontSize: 12, marginTop: 2 }}>{r.error}</div>}
                  </div>
                </div>
              ))}
            </div>
          )}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: 10, fontSize: 12.5 }}>
            {log.selected_next_step && (
              <div><span style={{ color: 'var(--text3)' }}>Next Step: </span><span style={{ color: 'var(--accent)' }}>{log.selected_next_step}</span></div>
            )}
            {log.approver_id && (
              <div><span style={{ color: 'var(--text3)' }}>Approver: </span><span>{log.approver_id}</span></div>
            )}
            {log.error_message && (
              <div style={{ gridColumn: '1/-1' }}><span style={{ color: 'var(--red)' }}>Error: {log.error_message}</span></div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default function ExecutionPage() {
  const { id } = useParams();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  const [workflows, setWorkflows] = useState([]);
  const [selectedWf, setSelectedWf] = useState(searchParams.get('workflow') || '');
  const [wfDetail, setWfDetail] = useState(null);
  const [inputData, setInputData] = useState('{}');
  const [execution, setExecution] = useState(null);
  const [loading, setLoading] = useState(false);
  const [approverId, setApproverId] = useState('user-001');

  useEffect(() => {
    getWorkflows({ page_size: 100 }).then(r => setWorkflows(r.data.data)).catch(() => {});
  }, []);

  useEffect(() => {
    if (selectedWf) {
      getWorkflow(selectedWf).then(r => {
        setWfDetail(r.data);
        const schema = r.data.input_schema || {};
        const example = {};
        Object.entries(schema).forEach(([k, v]) => {
          example[k] = v.type === 'number' ? 100 : v.allowed_values?.[0] || '';
        });
        setInputData(JSON.stringify(example, null, 2));
      }).catch(() => {});
    }
  }, [selectedWf]);

  useEffect(() => {
    if (id) {
      getExecution(id).then(r => setExecution(r.data)).catch(e => toast.error(e.message));
    }
  }, [id]);

  const handleExecute = async () => {
    if (!selectedWf) return toast.error('Select a workflow');
    let data = {};
    try { data = JSON.parse(inputData); } catch { return toast.error('Input data is not valid JSON'); }
    setLoading(true);
    try {
      const res = await executeWorkflow(selectedWf, { data, triggered_by: approverId });
      setExecution(res.data);
      navigate(`/executions/${res.data.id}`);
      toast.success('Execution started!');
    } catch (e) {
      toast.error(e.message);
    } finally { setLoading(false); }
  };

  const handleApprove = async () => {
    try {
      const res = await approveStep(execution.id, { approver_id: approverId });
      setExecution(res.data);
      toast.success('Step approved!');
    } catch (e) { toast.error(e.message); }
  };

  const handleCancel = async () => {
    try { const r = await cancelExecution(execution.id); setExecution(r.data); toast.success('Canceled'); } catch (e) { toast.error(e.message); }
  };

  const handleRetry = async () => {
    try { const r = await retryExecution(execution.id); setExecution(r.data); toast.success('Retrying...'); } catch (e) { toast.error(e.message); }
  };

  const currentStep = wfDetail?.steps?.find(s => s.id === execution?.current_step_id);
  const needsApproval = execution?.status === 'in_progress' && currentStep?.step_type === 'approval';
  const cfg = execution ? STATUS_CONFIG[execution.status] : null;

  return (
    <>
      <div className="page-header">
        <h1>Run Workflow</h1>
      </div>

      <div className="page-body" style={{ display: 'grid', gridTemplateColumns: '400px 1fr', gap: 24, alignItems: 'start' }}>
        {/* Left: setup panel */}
        <div>
          <div className="card" style={{ padding: 20 }}>
            <div style={{ fontWeight: 700, fontFamily: 'var(--mono)', fontSize: 13, color: 'var(--text2)', marginBottom: 16 }}>EXECUTION SETUP</div>

            <div className="form-group">
              <label>Select Workflow</label>
              <select value={selectedWf} onChange={e => { setSelectedWf(e.target.value); setExecution(null); navigate('/executions'); }}>
                <option value="">— Choose workflow —</option>
                {workflows.map(w => <option key={w.id} value={w.id}>{w.name} (v{w.version})</option>)}
              </select>
            </div>

            {wfDetail && Object.keys(wfDetail.input_schema || {}).length > 0 && (
              <div style={{ marginBottom: 14, padding: 12, background: 'var(--bg3)', borderRadius: 'var(--radius)', border: '1px solid var(--border)' }}>
                <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text3)', marginBottom: 8, textTransform: 'uppercase' }}>Schema</div>
                {Object.entries(wfDetail.input_schema).map(([k, v]) => (
                  <div key={k} style={{ fontSize: 12.5, color: 'var(--text2)', display: 'flex', justifyContent: 'space-between', padding: '3px 0' }}>
                    <span style={{ color: 'var(--text)' }}>{k}</span>
                    <span style={{ color: 'var(--text3)' }}>{v.type}{v.required ? ' *' : ''}{v.allowed_values ? ` [${v.allowed_values.join('|')}]` : ''}</span>
                  </div>
                ))}
              </div>
            )}

            <div className="form-group">
              <label>Input Data (JSON)</label>
              <textarea value={inputData} onChange={e => setInputData(e.target.value)} rows={7}
                style={{ fontFamily: 'var(--mono)', fontSize: 12 }} />
            </div>

            <div className="form-group" style={{ marginBottom: 16 }}>
              <label>Your User ID</label>
              <input value={approverId} onChange={e => setApproverId(e.target.value)} placeholder="user-001" />
            </div>

            <button className="btn btn-primary" style={{ width: '100%', justifyContent: 'center' }}
              onClick={handleExecute} disabled={loading || !selectedWf}>
              <Play size={15} /> {loading ? 'Starting...' : 'Start Execution'}
            </button>
          </div>
        </div>

        {/* Right: execution result */}
        <div>
          {!execution ? (
            <div className="card">
              <div className="empty">
                <Play />
                <p>Configure and run a workflow to see execution results here.</p>
              </div>
            </div>
          ) : (
            <>
              <div className="card" style={{ padding: 18, marginBottom: 16 }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
                  <div className="flex gap-2">
                    <span style={{ color: cfg?.color }}>{cfg?.icon}</span>
                    <span style={{ fontWeight: 700, fontSize: 15, fontFamily: 'var(--mono)' }}>
                      {execution.status.toUpperCase()}
                    </span>
                  </div>
                  <div className="flex gap-2">
                    {execution.status === 'in_progress' && (
                      <button className="btn btn-danger btn-sm" onClick={handleCancel}><XOctagon size={13} /> Cancel</button>
                    )}
                    {execution.status === 'failed' && (
                      <button className="btn btn-ghost btn-sm" onClick={handleRetry}><RefreshCw size={13} /> Retry</button>
                    )}
                  </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))', gap: 10, fontSize: 12.5 }}>
                  <div><span style={{ color: 'var(--text3)' }}>ID: </span><span className="mono">{execution.id?.slice(0,16)}...</span></div>
                  <div><span style={{ color: 'var(--text3)' }}>Version: </span><span>v{execution.workflow_version}</span></div>
                  <div><span style={{ color: 'var(--text3)' }}>By: </span><span>{execution.triggered_by}</span></div>
                  <div><span style={{ color: 'var(--text3)' }}>Retries: </span><span>{execution.retries}</span></div>
                  {execution.started_at && <div><span style={{ color: 'var(--text3)' }}>Started: </span><span>{new Date(execution.started_at).toLocaleTimeString()}</span></div>}
                </div>

                {needsApproval && (
                  <div style={{ marginTop: 14, padding: 14, background: 'rgba(247,195,79,0.08)', border: '1px solid rgba(247,195,79,0.2)', borderRadius: 'var(--radius)' }}>
                    <div className="flex gap-2" style={{ marginBottom: 8 }}>
                      <AlertTriangle size={15} style={{ color: 'var(--yellow)', flexShrink: 0 }} />
                      <span style={{ fontWeight: 600, color: 'var(--yellow)', fontSize: 13 }}>
                        Awaiting Approval: {currentStep?.name}
                      </span>
                    </div>
                    <p style={{ fontSize: 12.5, color: 'var(--text2)', marginBottom: 12 }}>
                      This step requires manual approval to continue.
                    </p>
                    <button className="btn btn-success" onClick={handleApprove}>
                      <ThumbsUp size={14} /> Approve as {approverId}
                    </button>
                  </div>
                )}
              </div>

              <div>
                <div style={{ fontWeight: 700, fontFamily: 'var(--mono)', fontSize: 13, color: 'var(--text2)', marginBottom: 12 }}>EXECUTION LOG</div>
                {execution.logs?.length === 0 ? (
                  <div style={{ color: 'var(--text3)', fontSize: 13 }}>No logs yet.</div>
                ) : execution.logs?.map((log, i) => <LogEntry key={i} log={log} />)}
              </div>
            </>
          )}
        </div>
      </div>
    </>
  );
}
