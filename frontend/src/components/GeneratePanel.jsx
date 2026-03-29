import { useState } from 'react';
import { Zap, Loader } from 'lucide-react';
import toast from 'react-hot-toast';
import { generateTestCases } from '../api/testCases';

const DOMAINS = ['Web', 'API', 'Mobile', 'Database', 'Security'];

export default function GeneratePanel({ document, onGenerated }) {
  const [domain, setDomain] = useState('Web');
  const [count, setCount] = useState(5);
  const [extra, setExtra] = useState('');
  const [loading, setLoading] = useState(false);

  const disabled = !document || document.status !== 'ready' || loading;

  const handleGenerate = async () => {
    setLoading(true);
    try {
      const res = await generateTestCases({
        document_id: document.id,
        domain,
        count,
        extra_context: extra || undefined,
      });
      toast.success(`Generated ${res.data.test_cases.length} test cases!`);
      onGenerated?.();
    } catch (err) {
      toast.error('Generation failed: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card">
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
        <Zap size={20} color="var(--accent)" />
        <h3 style={{ fontSize: 15, fontWeight: 700 }}>Generate Test Cases</h3>
      </div>

      {!document && (
        <div style={{ padding: '12px 0', fontSize: 13, color: 'var(--text-muted)' }}>
          ← Select a document from the list to generate test cases
        </div>
      )}

      {document && document.status !== 'ready' && (
        <div style={{ background: 'var(--warning-bg)', border: '1px solid var(--warning)', borderRadius: 8, padding: '10px 14px', fontSize: 13, color: 'var(--warning)', marginBottom: 16 }}>
          Document is still {document.status}. Please wait for processing to complete.
        </div>
      )}

      {document && (
        <div>
          <div style={{ background: 'var(--bg-primary)', borderRadius: 8, padding: '10px 14px', fontSize: 13, marginBottom: 16, color: 'var(--text-secondary)' }}>
            📄 <strong style={{ color: 'var(--text-primary)' }}>{document.name}</strong> · {document.chunk_count} chunks
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
            <div className="form-group" style={{ marginBottom: 0 }}>
              <label className="form-label">Domain</label>
              <select className="form-select" value={domain} onChange={e => setDomain(e.target.value)}>
                {DOMAINS.map(d => <option key={d} value={d}>{d}</option>)}
              </select>
            </div>
            <div className="form-group" style={{ marginBottom: 0 }}>
              <label className="form-label">Scenario Count: {count}</label>
              <input type="range" min={1} max={50} value={count}
                onChange={e => setCount(+e.target.value)}
                style={{ width: '100%', marginTop: 8, accentColor: 'var(--accent)' }} />
            </div>
          </div>

          <div className="form-group" style={{ marginTop: 12 }}>
            <label className="form-label">Extra Context (optional)</label>
            <textarea className="form-textarea" rows={2}
              placeholder="Add any specific requirements or context..."
              value={extra} onChange={e => setExtra(e.target.value)}
              style={{ minHeight: 64 }} />
          </div>

          <button className="btn btn-primary" onClick={handleGenerate} disabled={disabled} style={{ width: '100%', justifyContent: 'center', marginTop: 4 }}>
            {loading ? <><div className="spinner" style={{ width: 16, height: 16 }} /> Generating...</> : <><Zap size={16} /> Generate {count} Test Cases</>}
          </button>
        </div>
      )}
    </div>
  );
}
