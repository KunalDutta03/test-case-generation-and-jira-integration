import { useState, useEffect } from 'react';
import { Settings, Send, CheckCircle, AlertCircle, ExternalLink, Loader } from 'lucide-react';
import toast from 'react-hot-toast';
import { saveJiraConfig, listJiraConfigs, testJiraConnection, injectToJira, getJiraDefaults } from '../api/jira';
import { listTestCases } from '../api/testCases';

export default function JiraPanel({ documentId }) {
  const [configs, setConfigs] = useState([]);
  const [form, setForm] = useState({
    base_url: '', project_key: 'QA', issue_type: 'Task', email: '', api_token: '', labels: ['auto-generated']
  });
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState(null);
  const [saving, setSaving] = useState(false);
  const [injecting, setInjecting] = useState(false);
  const [approvedCount, setApprovedCount] = useState(0);

  useEffect(() => {
    loadDefaults();
    loadConfigs();
  }, []);

  useEffect(() => {
    if (documentId) loadApprovedCount();
  }, [documentId]);

  const loadDefaults = async () => {
    try {
      const res = await getJiraDefaults();
      const d = res.data;
      setForm(f => ({
        ...f,
        base_url: d.jira_base_url || f.base_url,
        email: f.email,
        project_key: d.jira_default_project_key || f.project_key,
        issue_type: d.jira_default_issue_type || f.issue_type,
      }));
    } catch (_) {}
  };

  const loadConfigs = async () => {
    try {
      const res = await listJiraConfigs();
      setConfigs(res.data || []);
      if (res.data?.[0]) {
        const c = res.data[0];
        setForm(f => ({ ...f, base_url: c.base_url, project_key: c.project_key, issue_type: c.issue_type, email: c.email }));
      }
    } catch (_) {}
  };

  const loadApprovedCount = async () => {
    try {
      const res = await listTestCases({ document_id: documentId, status: 'approved' });
      setApprovedCount(res.data.total || 0);
    } catch (_) {}
  };

  const handleTest = async () => {
    setTesting(true); setTestResult(null);
    try {
      const res = await testJiraConnection(form);
      setTestResult(res.data);
    } catch (err) {
      setTestResult({ success: false, message: err.message });
    } finally {
      setTesting(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await saveJiraConfig(form);
      toast.success('Jira configuration saved!');
      loadConfigs();
    } catch (err) {
      toast.error(err.message);
    } finally {
      setSaving(false);
    }
  };

  const handleInject = async () => {
    if (!configs[0]) return toast.error('Save Jira config first');
    if (approvedCount === 0) return toast.error('No approved test cases to inject');
    setInjecting(true);
    try {
      const casesRes = await listTestCases({ document_id: documentId, status: 'approved', limit: 200 });
      const ids = casesRes.data.test_cases.map(c => c.id);
      const res = await injectToJira(ids, configs[0].id);
      const { injected, failed } = res.data;
      if (injected.length > 0) toast.success(`✅ ${injected.length} issues created in Jira!`);
      if (failed.length > 0) toast.error(`⚠️ ${failed.length} issues failed`);
    } catch (err) {
      toast.error(err.message);
    } finally {
      setInjecting(false);
      loadApprovedCount();
    }
  };

  const set = (k, v) => setForm(f => ({ ...f, [k]: v }));

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      {/* Config Form */}
      <div className="card">
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
          <Settings size={20} color="var(--accent)" />
          <h3 style={{ fontSize: 15, fontWeight: 700 }}>Jira Configuration</h3>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
          <div className="form-group" style={{ gridColumn: '1/-1' }}>
            <label className="form-label">Jira Base URL</label>
            <input className="form-input" value={form.base_url} onChange={e => set('base_url', e.target.value)} placeholder="https://yourorg.atlassian.net" />
          </div>
          <div className="form-group">
            <label className="form-label">Email</label>
            <input className="form-input" type="email" value={form.email} onChange={e => set('email', e.target.value)} placeholder="jira@company.com" />
          </div>
          <div className="form-group">
            <label className="form-label">API Token</label>
            <input className="form-input" type="password" value={form.api_token} onChange={e => set('api_token', e.target.value)} placeholder="ATATT3x..." />
          </div>
          <div className="form-group">
            <label className="form-label">Project Key</label>
            <input className="form-input" value={form.project_key} onChange={e => set('project_key', e.target.value)} placeholder="QA" />
          </div>
          <div className="form-group">
            <label className="form-label">Issue Type</label>
            <input className="form-input" value={form.issue_type} onChange={e => set('issue_type', e.target.value)} placeholder="Task" />
          </div>
        </div>

        {testResult && (
          <div style={{ background: testResult.success ? 'var(--success-bg)' : 'var(--danger-bg)', border: `1px solid ${testResult.success ? 'var(--success)' : 'var(--danger)'}`, borderRadius: 8, padding: '10px 14px', fontSize: 13, color: testResult.success ? 'var(--success)' : 'var(--danger)', marginBottom: 12, display: 'flex', gap: 8, alignItems: 'center' }}>
            {testResult.success ? <CheckCircle size={16} /> : <AlertCircle size={16} />}
            {testResult.message}
            {testResult.projects && <span style={{ color: 'var(--text-secondary)', marginLeft: 4 }}>Projects: {testResult.projects.slice(0, 5).join(', ')}</span>}
          </div>
        )}

        <div style={{ display: 'flex', gap: 8 }}>
          <button className="btn btn-ghost" onClick={handleTest} disabled={testing}>
            {testing ? <><div className="spinner" style={{ width: 14, height: 14 }} /> Testing...</> : '🔌 Test Connection'}
          </button>
          <button className="btn btn-primary" onClick={handleSave} disabled={saving}>
            {saving ? <div className="spinner" style={{ width: 14, height: 14 }} /> : '💾 Save Config'}
          </button>
        </div>
      </div>

      {/* Inject Panel */}
      <div className="card">
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
          <Send size={20} color="var(--success)" />
          <h3 style={{ fontSize: 15, fontWeight: 700 }}>Inject to Jira</h3>
        </div>

        <div style={{ background: 'var(--bg-primary)', borderRadius: 8, padding: '12px 16px', fontSize: 13, marginBottom: 16 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ color: 'var(--text-secondary)' }}>Approved test cases (current document)</span>
            <strong style={{ color: approvedCount > 0 ? 'var(--success)' : 'var(--text-muted)' }}>{approvedCount}</strong>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 4 }}>
            <span style={{ color: 'var(--text-secondary)' }}>Active Jira config</span>
            <span style={{ color: configs[0] ? 'var(--success)' : 'var(--danger)' }}>{configs[0] ? configs[0].base_url : 'Not configured'}</span>
          </div>
        </div>

        <button
          className="btn btn-success"
          onClick={handleInject}
          disabled={injecting || approvedCount === 0 || !configs[0]}
          style={{ width: '100%', justifyContent: 'center' }}
        >
          {injecting
            ? <><div className="spinner" style={{ width: 16, height: 16 }} /> Injecting...</>
            : <><ExternalLink size={16} /> Inject {approvedCount} Approved Cases to Jira</>}
        </button>

        {approvedCount === 0 && <p style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 8, textAlign: 'center' }}>Approve test cases in the Review tab first</p>}
      </div>
    </div>
  );
}
