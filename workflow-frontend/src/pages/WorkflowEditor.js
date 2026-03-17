import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import { ArrowLeft, Plus, Trash2, Edit2, ChevronDown, ChevronUp, GripVertical, Save } from 'lucide-react';
import { getWorkflow, createWorkflow, updateWorkflow, createStep, updateStep, deleteStep, createRule, updateRule, deleteRule } from '../api/client';

const STEP_TYPES = ['task', 'approval', 'notification'];
const STEP_TYPE_COLOR = { task: 'badge-blue', approval: 'badge-yellow', notification: 'badge-green' };

function RuleModal({ rule, steps, stepId, onSave, onClose }) {
  const [form, setForm] = useState(rule || { condition: '', next_step_id: '', priority: 10 });
  const set = (k, v) => setForm(f => ({ ...f, [k]: v }));

  const handleSave = async () => {
    if (!form.condition.trim()) return toast.error('Condition is required');
    try {
      if (rule?.id) await updateRule(rule.id, form);
      else await createRule(stepId, { ...form, next_step_id: form.next_step_id || null });
      onSave();
    } catch (e) { toast.error(e.message); }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h2>{rule?.id ? 'Edit Rule' : 'Add Rule'}</h2>
          <button className="btn btn-ghost btn-sm" onClick={onClose}>✕</button>
        </div>
        <div className="modal-body">
          <div className="form-group">
            <label>Condition</label>
            <input value={form.condition} onChange={e => set('condition', e.target.value)}
              placeholder='e.g. amount > 100 && country == "US" or DEFAULT' />
            <span style={{ fontSize: 11, color: 'var(--text3)' }}>
              Supports: ==, !=, &lt;, &gt;, &lt;=, &gt;=, &amp;&amp;, ||, contains(), startsWith(), endsWith(), DEFAULT
            </span>
          </div>
          <div className="form-group">
            <label>Next Step (leave empty to end workflow)</label>
            <select value={form.next_step_id || ''} onChange={e => set('next_step_id', e.target.value || null)}>
              <option value="">— End Workflow —</option>
              {steps.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
            </select>
          </div>
          <div className="form-group">
            <label>Priority (lower = evaluated first)</label>
            <input type="number" value={form.priority} onChange={e => set('priority', parseInt(e.target.value))} min={1} />
          </div>
        </div>
        <div className="modal-footer">
          <button className="btn btn-ghost" onClick={onClose}>Cancel</button>
          <button className="btn btn-primary" onClick={handleSave}>Save Rule</button>
        </div>
      </div>
    </div>
  );
}

function StepModal({ step, workflowId, onSave, onClose }) {
  const [form, setForm] = useState(step || { name: '', step_type: 'task', order: 0, metadata: {} });
  const [metaStr, setMetaStr] = useState(JSON.stringify(step?.metadata || {}, null, 2));
  const set = (k, v) => setForm(f => ({ ...f, [k]: v }));

  const handleSave = async () => {
    if (!form.name.trim()) return toast.error('Step name is required');
    let meta = {};
    try { meta = JSON.parse(metaStr); } catch { return toast.error('Metadata is not valid JSON'); }
    const payload = { ...form, metadata: meta };
    try {
      if (step?.id) await updateStep(step.id, payload);
      else await createStep(workflowId, payload);
      onSave();
    } catch (e) { toast.error(e.message); }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h2>{step?.id ? 'Edit Step' : 'Add Step'}</h2>
          <button className="btn btn-ghost btn-sm" onClick={onClose}>✕</button>
        </div>
        <div className="modal-body">
          <div className="form-group">
            <label>Step Name</label>
            <input value={form.name} onChange={e => set('name', e.target.value)} placeholder="e.g. Manager Approval" />
          </div>
          <div className="form-group">
            <label>Type</label>
            <select value={form.step_type} onChange={e => set('step_type', e.target.value)}>
              {STEP_TYPES.map(t => <option key={t} value={t}>{t.charAt(0).toUpperCase() + t.slice(1)}</option>)}
            </select>
          </div>
          <div className="form-group">
            <label>Order</label>
            <input type="number" value={form.order} onChange={e => set('order', parseInt(e.target.value))} min={0} />
          </div>
          <div className="form-group">
            <label>Metadata (JSON)</label>
            <textarea value={metaStr} onChange={e => setMetaStr(e.target.value)} rows={4}
              placeholder='{"assignee_email": "manager@example.com"}' style={{ fontFamily: 'var(--mono)', fontSize: 12 }} />
          </div>
        </div>
        <div className="modal-footer">
          <button className="btn btn-ghost" onClick={onClose}>Cancel</button>
          <button className="btn btn-primary" onClick={handleSave}>Save Step</button>
        </div>
      </div>
    </div>
  );
}

function StepCard({ step, allSteps, workflowId, onRefresh, isStart, onSetStart }) {
  const [expanded, setExpanded] = useState(false);
  const [rules, setRules] = useState(step.rules || []);
  const [editingRule, setEditingRule] = useState(null);
  const [editingStep, setEditingStep] = useState(false);
  const [addingRule, setAddingRule] = useState(false);

  const refreshRules = async () => {
    const { getRules } = await import('../api/client');
    const res = await getRules(step.id);
    setRules(res.data);
    onRefresh();
  };

  const handleDeleteStep = async () => {
    if (!window.confirm(`Delete step "${step.name}"?`)) return;
    try { await deleteStep(step.id); onRefresh(); } catch (e) { toast.error(e.message); }
  };

  const handleDeleteRule = async (ruleId) => {
    try { await deleteRule(ruleId); refreshRules(); } catch (e) { toast.error(e.message); }
  };

  const getStepName = (id) => allSteps.find(s => s.id === id)?.name || (id ? id.slice(0, 8) + '...' : '— End —');

  return (
    <div className="card" style={{ marginBottom: 10 }}>
      <div style={{ padding: '12px 16px', display: 'flex', alignItems: 'center', gap: 12 }}>
        <GripVertical size={16} style={{ color: 'var(--text3)', flexShrink: 0 }} />
        <div style={{ flex: 1, minWidth: 0 }}>
          <div className="flex gap-2">
            <span style={{ fontWeight: 600, fontSize: 14 }}>{step.name}</span>
            <span className={`badge ${STEP_TYPE_COLOR[step.step_type]}`}>{step.step_type}</span>
            {isStart && <span className="badge badge-purple">Start</span>}
          </div>
          <div style={{ color: 'var(--text3)', fontSize: 12, marginTop: 2 }}>
            Order: {step.order} · {rules.length} rule{rules.length !== 1 ? 's' : ''}
          </div>
        </div>
        <div className="flex gap-2">
          {!isStart && (
            <button className="btn btn-ghost btn-sm" onClick={() => onSetStart(step.id)}>Set Start</button>
          )}
          <button className="btn btn-ghost btn-sm" onClick={() => setEditingStep(true)}><Edit2 size={13} /></button>
          <button className="btn btn-danger btn-sm" onClick={handleDeleteStep}><Trash2 size={13} /></button>
          <button className="btn btn-ghost btn-sm" onClick={() => setExpanded(e => !e)}>
            {expanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
          </button>
        </div>
      </div>

      {expanded && (
        <div style={{ borderTop: '1px solid var(--border)', padding: '14px 16px' }}>
          <div className="flex gap-2" style={{ marginBottom: 10, justifyContent: 'space-between' }}>
            <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--text2)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Rules</span>
            <button className="btn btn-ghost btn-sm" onClick={() => setAddingRule(true)}><Plus size={13} /> Add Rule</button>
          </div>
          {rules.length === 0 ? (
            <div style={{ color: 'var(--text3)', fontSize: 13, padding: '8px 0' }}>No rules yet. Add a DEFAULT rule at minimum.</div>
          ) : (
            <table style={{ width: '100%', fontSize: 13 }}>
              <thead>
                <tr>
                  <th style={{ width: 60 }}>Priority</th>
                  <th>Condition</th>
                  <th>Next Step</th>
                  <th style={{ width: 80 }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {[...rules].sort((a,b) => a.priority - b.priority).map(r => (
                  <tr key={r.id}>
                    <td><span className="mono">{r.priority}</span></td>
                    <td><code style={{ fontFamily: 'var(--mono)', fontSize: 12, color: 'var(--accent)', background: 'rgba(79,142,247,0.08)', padding: '2px 6px', borderRadius: 4 }}>{r.condition}</code></td>
                    <td style={{ color: r.next_step_id ? 'var(--text)' : 'var(--text3)' }}>{getStepName(r.next_step_id)}</td>
                    <td>
                      <div className="flex gap-2">
                        <button className="btn btn-ghost btn-sm" onClick={() => setEditingRule(r)}><Edit2 size={12} /></button>
                        <button className="btn btn-danger btn-sm" onClick={() => handleDeleteRule(r.id)}><Trash2 size={12} /></button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      {editingStep && <StepModal step={step} workflowId={workflowId} onSave={() => { setEditingStep(false); onRefresh(); }} onClose={() => setEditingStep(false)} />}
      {(addingRule || editingRule) && (
        <RuleModal
          rule={editingRule}
          steps={allSteps}
          stepId={step.id}
          onSave={() => { setAddingRule(false); setEditingRule(null); refreshRules(); }}
          onClose={() => { setAddingRule(false); setEditingRule(null); }}
        />
      )}
    </div>
  );
}

export default function WorkflowEditor() {
  const { id } = useParams();
  const navigate = useNavigate();
  const isNew = !id || id === 'new';
  const [workflow, setWorkflow] = useState({ name: '', description: '', input_schema: {}, start_step_id: null, is_active: true });
  const [steps, setSteps] = useState([]);
  const [schemaStr, setSchemaStr] = useState('{}');
  const [addingStep, setAddingStep] = useState(false);
  const [saving, setSaving] = useState(false);

  const loadWorkflow = async () => {
    if (isNew) return;
    try {
      const res = await getWorkflow(id);
      setWorkflow(res.data);
      setSteps(res.data.steps || []);
      setSchemaStr(JSON.stringify(res.data.input_schema || {}, null, 2));
    } catch (e) { toast.error(e.message); }
  };

  useEffect(() => { loadWorkflow(); }, [id]);

  const handleSave = async () => {
    if (!workflow.name.trim()) return toast.error('Workflow name is required');
    let schema = {};
    try { schema = JSON.parse(schemaStr); } catch { return toast.error('Input schema is not valid JSON'); }
    setSaving(true);
    try {
      if (isNew) {
        const res = await createWorkflow({ ...workflow, input_schema: schema });
        toast.success('Workflow created!');
        navigate(`/workflows/${res.data.id}/edit`);
      } else {
        await updateWorkflow(id, { ...workflow, input_schema: schema });
        toast.success('Workflow saved!');
        loadWorkflow();
      }
    } catch (e) { toast.error(e.message); }
    finally { setSaving(false); }
  };

  const handleSetStart = async (stepId) => {
    try {
      await updateWorkflow(id, { start_step_id: stepId });
      setWorkflow(w => ({ ...w, start_step_id: stepId }));
      toast.success('Start step updated');
    } catch (e) { toast.error(e.message); }
  };

  return (
    <>
      <div className="page-header">
        <div className="flex gap-2">
          <button className="btn btn-ghost btn-sm" onClick={() => navigate('/workflows')}><ArrowLeft size={14} /></button>
          <div>
            <h1>{isNew ? 'New Workflow' : workflow.name}</h1>
            {!isNew && <span style={{ color: 'var(--text3)', fontSize: 12 }}>v{workflow.version} · {steps.length} steps</span>}
          </div>
        </div>
        <button className="btn btn-primary" onClick={handleSave} disabled={saving}>
          <Save size={14} /> {saving ? 'Saving...' : 'Save Workflow'}
        </button>
      </div>

      <div className="page-body">
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24, marginBottom: 28 }}>
          <div className="card" style={{ padding: 20 }}>
            <div style={{ fontWeight: 700, fontFamily: 'var(--mono)', fontSize: 13, marginBottom: 16, color: 'var(--text2)' }}>WORKFLOW INFO</div>
            <div className="form-group">
              <label>Name</label>
              <input value={workflow.name} onChange={e => setWorkflow(w => ({ ...w, name: e.target.value }))} placeholder="e.g. Expense Approval" />
            </div>
            <div className="form-group">
              <label>Description</label>
              <textarea value={workflow.description || ''} onChange={e => setWorkflow(w => ({ ...w, description: e.target.value }))} rows={2} placeholder="What does this workflow do?" />
            </div>
            <div className="form-group" style={{ marginBottom: 0 }}>
              <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer' }}>
                <input type="checkbox" checked={workflow.is_active} onChange={e => setWorkflow(w => ({ ...w, is_active: e.target.checked }))} style={{ width: 'auto', accentColor: 'var(--accent)' }} />
                Active
              </label>
            </div>
          </div>

          <div className="card" style={{ padding: 20 }}>
            <div style={{ fontWeight: 700, fontFamily: 'var(--mono)', fontSize: 13, marginBottom: 4, color: 'var(--text2)' }}>INPUT SCHEMA</div>
            <div style={{ fontSize: 12, color: 'var(--text3)', marginBottom: 12 }}>Define fields users must provide when running this workflow.</div>
            <textarea
              value={schemaStr}
              onChange={e => setSchemaStr(e.target.value)}
              rows={8}
              style={{ fontFamily: 'var(--mono)', fontSize: 12 }}
              placeholder={'{\n  "amount": {"type": "number", "required": true},\n  "country": {"type": "string", "required": true}\n}'}
            />
          </div>
        </div>

        {!isNew && (
          <div>
            <div className="flex gap-2" style={{ justifyContent: 'space-between', marginBottom: 14 }}>
              <div>
                <div style={{ fontWeight: 700, fontFamily: 'var(--mono)', fontSize: 13, color: 'var(--text2)' }}>STEPS</div>
                {workflow.start_step_id && (
                  <div style={{ fontSize: 12, color: 'var(--text3)', marginTop: 3 }}>
                    Start: {steps.find(s => s.id === workflow.start_step_id)?.name || workflow.start_step_id}
                  </div>
                )}
              </div>
              <button className="btn btn-ghost btn-sm" onClick={() => setAddingStep(true)}><Plus size={13} /> Add Step</button>
            </div>

            {steps.length === 0 ? (
              <div className="card">
                <div className="empty">
                  <Plus size={32} />
                  <p>No steps yet. Add your first step to get started.</p>
                </div>
              </div>
            ) : [...steps].sort((a, b) => a.order - b.order).map(step => (
              <StepCard
                key={step.id}
                step={step}
                allSteps={steps}
                workflowId={id}
                onRefresh={loadWorkflow}
                isStart={workflow.start_step_id === step.id}
                onSetStart={handleSetStart}
              />
            ))}
          </div>
        )}

        {isNew && (
          <div className="card" style={{ padding: 24, textAlign: 'center', color: 'var(--text3)' }}>
            <p>Save the workflow first, then add steps.</p>
          </div>
        )}
      </div>

      {addingStep && (
        <StepModal workflowId={id} onSave={() => { setAddingStep(false); loadWorkflow(); }} onClose={() => setAddingStep(false)} />
      )}
    </>
  );
}
