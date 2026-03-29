import { useState, useEffect, useCallback } from 'react';
import Editor from '@monaco-editor/react';
import { CheckCircle, XCircle, Edit3, CheckSquare, Square, Trash2, ExternalLink, Filter } from 'lucide-react';
import toast from 'react-hot-toast';
import { listTestCases, updateStatus, editTestCase, bulkUpdateStatus, deleteTestCase } from '../api/testCases';

const DOMAINS = ['', 'Web', 'API', 'Mobile', 'Database', 'Security'];
const STATUSES = ['', 'draft', 'approved', 'rejected', 'pending_edit'];

function GherkinSyntax({ text }) {
  const lines = text.split('\n').map((line, i) => {
    let color = 'var(--text-primary)';
    if (line.trim().startsWith('Feature:')) color = '#a78bfa';
    else if (line.trim().startsWith('Scenario')) color = '#4f8ef7';
    else if (/^\s*(Given|When|Then|And|But)/.test(line)) color = '#22c55e';
    else if (line.trim().startsWith('#')) color = 'var(--text-muted)';
    return <div key={i} style={{ color }}>{line || '\u00A0'}</div>;
  });
  return (
    <pre style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 12, lineHeight: 1.8, background: 'var(--bg-primary)', borderRadius: 8, padding: 14, overflowX: 'auto', maxHeight: 240, overflowY: 'auto', border: '1px solid var(--border)' }}>
      {lines}
    </pre>
  );
}

function TestCaseCard({ tc, selected, onSelect, onApprove, onReject, onEdit, onDelete }) {
  const [editing, setEditing] = useState(false);
  const [editorValue, setEditorValue] = useState(tc.gherkin_text);
  const [saving, setSaving] = useState(false);

  const handleSave = async () => {
    setSaving(true);
    try {
      await editTestCase(tc.id, editorValue);
      toast.success('Test case updated');
      setEditing(false);
      onEdit?.();
    } catch (err) {
      toast.error(err.message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className={`tc-card fade-in ${selected ? 'selected' : ''}`}>
      <div className="tc-card-header">
        <input type="checkbox" className="checkbox" checked={selected} onChange={() => onSelect(tc.id)} />
        <div style={{ flex: 1, minWidth: 0 }}>
          <div className="tc-card-title">{tc.scenario}</div>
          <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>{tc.feature}</div>
        </div>
        <div className="tc-card-meta">
          <span className={`badge badge-${tc.domain}`}>{tc.domain}</span>
          <span className={`badge badge-${tc.status}`}>{tc.status}</span>
          {tc.jira_url && (
            <a href={tc.jira_url} target="_blank" rel="noreferrer" className="jira-link">
              <ExternalLink size={12} /> {tc.jira_key}
            </a>
          )}
        </div>
      </div>

      {!editing && <GherkinSyntax text={tc.gherkin_text} />}

      {editing && (
        <div style={{ border: '1px solid var(--accent)', borderRadius: 8, overflow: 'hidden', marginBottom: 8 }}>
          <Editor
            height="260px"
            defaultLanguage="plaintext"
            theme="vs-dark"
            value={editorValue}
            onChange={setEditorValue}
            options={{ fontSize: 12, minimap: { enabled: false }, lineNumbers: 'off', wordWrap: 'on', scrollBeyondLastLine: false }}
          />
        </div>
      )}

      <div className="tc-actions">
        {!editing && tc.status !== 'approved' && (
          <button className="btn btn-success btn-sm" onClick={() => onApprove(tc.id)}>
            <CheckCircle size={13} /> Approve
          </button>
        )}
        {!editing && tc.status !== 'rejected' && (
          <button className="btn btn-danger btn-sm" onClick={() => onReject(tc.id)}>
            <XCircle size={13} /> Reject
          </button>
        )}
        {!editing ? (
          <button className="btn btn-ghost btn-sm" onClick={() => setEditing(true)}>
            <Edit3 size={13} /> Edit
          </button>
        ) : (
          <>
            <button className="btn btn-primary btn-sm" onClick={handleSave} disabled={saving}>
              {saving ? <div className="spinner" style={{ width: 13, height: 13 }} /> : 'Save'}
            </button>
            <button className="btn btn-ghost btn-sm" onClick={() => { setEditing(false); setEditorValue(tc.gherkin_text); }}>Cancel</button>
          </>
        )}
        <button className="btn btn-ghost btn-sm" onClick={() => onDelete(tc.id)} style={{ marginLeft: 'auto' }}>
          <Trash2 size={13} />
        </button>
      </div>
    </div>
  );
}

export default function TestCaseReview({ documentId, refreshTrigger, onApprovedChange }) {
  const [cases, setCases] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selected, setSelected] = useState(new Set());
  const [filterStatus, setFilterStatus] = useState('');
  const [filterDomain, setFilterDomain] = useState('');

  const fetchCases = useCallback(async () => {
    if (!documentId) return;
    setLoading(true);
    try {
      const res = await listTestCases({ document_id: documentId, status: filterStatus || undefined, domain: filterDomain || undefined });
      setCases(res.data.test_cases || []);
    } catch (err) {
      toast.error(err.message);
    } finally {
      setLoading(false);
    }
  }, [documentId, filterStatus, filterDomain, refreshTrigger]);

  useEffect(() => { fetchCases(); }, [fetchCases]);

  const toggleSelect = (id) => setSelected(s => { const n = new Set(s); n.has(id) ? n.delete(id) : n.add(id); return n; });
  const toggleAll = () => setSelected(selected.size === cases.length ? new Set() : new Set(cases.map(c => c.id)));

  const handleApprove = async (id) => {
    try { await updateStatus(id, 'approved'); toast.success('Approved'); fetchCases(); onApprovedChange?.(); }
    catch (err) { toast.error(err.message); }
  };
  const handleReject = async (id) => {
    try { await updateStatus(id, 'rejected'); toast.success('Rejected'); fetchCases(); onApprovedChange?.(); }
    catch (err) { toast.error(err.message); }
  };
  const handleDelete = async (id) => {
    try { await deleteTestCase(id); toast.success('Deleted'); fetchCases(); }
    catch (err) { toast.error(err.message); }
  };
  const handleBulk = async (status) => {
    if (selected.size === 0) return toast.error('Select test cases first');
    try {
      await bulkUpdateStatus([...selected], status);
      toast.success(`${selected.size} cases ${status}`);
      setSelected(new Set());
      fetchCases();
      onApprovedChange?.();
    } catch (err) { toast.error(err.message); }
  };

  const stats = { approved: 0, rejected: 0, draft: 0, pending_edit: 0 };
  cases.forEach(c => stats[c.status] = (stats[c.status] || 0) + 1);

  if (!documentId) return (
    <div className="empty-state">
      <CheckCircle size={48} />
      <h3>Select a document</h3>
      <p>Choose a document from the left panel and generate test cases to review</p>
    </div>
  );

  return (
    <div>
      {/* Stats */}
      <div className="stats-grid" style={{ gridTemplateColumns: 'repeat(4, 1fr)', marginBottom: 20 }}>
        {[['approved', 'var(--success)', stats.approved], ['rejected', 'var(--danger)', stats.rejected], ['draft', 'var(--info)', stats.draft], ['pending_edit', 'var(--warning)', stats.pending_edit]].map(([s, c, v]) => (
          <div className="stat-card" key={s} style={{ borderLeft: `3px solid ${c}` }}>
            <div className="stat-value" style={{ fontSize: 22, color: c }}>{v}</div>
            <div className="stat-label">{s.replace('_', ' ')}</div>
          </div>
        ))}
      </div>

      {/* Filters & Bulk Actions */}
      <div className="filter-bar">
        <select className="form-select" value={filterStatus} onChange={e => setFilterStatus(e.target.value)}>
          <option value="">All Statuses</option>
          {STATUSES.filter(Boolean).map(s => <option key={s} value={s}>{s}</option>)}
        </select>
        <select className="form-select" value={filterDomain} onChange={e => setFilterDomain(e.target.value)}>
          <option value="">All Domains</option>
          {DOMAINS.filter(Boolean).map(d => <option key={d} value={d}>{d}</option>)}
        </select>
        {selected.size > 0 && (
          <>
            <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>{selected.size} selected</span>
            <button className="btn btn-success btn-sm" onClick={() => handleBulk('approved')}><CheckCircle size={13} /> Bulk Approve</button>
            <button className="btn btn-danger btn-sm" onClick={() => handleBulk('rejected')}><XCircle size={13} /> Bulk Reject</button>
          </>
        )}
        <button className="btn btn-ghost btn-sm" onClick={toggleAll} style={{ marginLeft: 'auto' }}>
          {selected.size === cases.length && cases.length > 0 ? <CheckSquare size={14} /> : <Square size={14} />} Select All
        </button>
      </div>

      {loading && <div style={{ textAlign: 'center', padding: 32 }}><div className="spinner" style={{ margin: 'auto' }} /></div>}

      {!loading && cases.length === 0 && (
        <div className="empty-state">
          <Filter size={40} />
          <h3>No test cases found</h3>
          <p>Generate test cases or adjust your filters</p>
        </div>
      )}

      <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
        {cases.map(tc => (
          <TestCaseCard
            key={tc.id} tc={tc}
            selected={selected.has(tc.id)}
            onSelect={toggleSelect}
            onApprove={handleApprove}
            onReject={handleReject}
            onEdit={fetchCases}
            onDelete={handleDelete}
          />
        ))}
      </div>
    </div>
  );
}
