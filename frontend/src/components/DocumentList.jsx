import { useEffect, useState } from 'react';
import { Trash2, RefreshCw, Eye, FileText, FileSpreadsheet, File } from 'lucide-react';
import toast from 'react-hot-toast';
import { listDocuments, deleteDocument, previewDocument } from '../api/documents';

function StatusBadge({ status }) {
  return <span className={`badge badge-${status}`}>{status}</span>;
}

function TypeIcon({ type }) {
  if (['.pdf'].includes(type)) return <File size={16} color="#ef4444" />;
  if (['.xlsx', '.xls', '.csv'].includes(type)) return <FileSpreadsheet size={16} color="#22c55e" />;
  return <FileText size={16} color="var(--accent)" />;
}

export default function DocumentList({ selectedDoc, onSelect, onRefresh, refreshTrigger }) {
  const [docs, setDocs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [preview, setPreview] = useState(null);

  const fetchDocs = async () => {
    setLoading(true);
    try {
      const res = await listDocuments();
      const newDocs = res.data.documents || [];
      setDocs(newDocs);
      
      // Sync selected doc if it was updated
      if (selectedDoc) {
        const updated = newDocs.find(d => d.id === selectedDoc.id);
        if (updated && (updated.status !== selectedDoc.status || updated.chunk_count !== selectedDoc.chunk_count)) {
          onSelect(updated);
        }
      }
    } catch (err) {
      toast.error('Failed to load documents: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchDocs(); }, [refreshTrigger]);

  // Poll if any document is processing
  useEffect(() => {
    const hasProcessing = docs.some(d => d.status === 'processing');
    if (hasProcessing) {
      const timer = setTimeout(() => {
        fetchDocs();
      }, 3000);
      return () => clearTimeout(timer);
    }
  }, [docs]);

  const handleDelete = async (e, id, name) => {
    e.stopPropagation();
    if (!confirm(`Delete "${name}" and all its test cases?`)) return;
    try {
      await deleteDocument(id);
      toast.success('Document deleted');
      setDocs(d => d.filter(doc => doc.id !== id));
      if (selectedDoc?.id === id) onSelect(null);
    } catch (err) {
      toast.error(err.message);
    }
  };

  const handlePreview = async (e, id) => {
    e.stopPropagation();
    try {
      const res = await previewDocument(id);
      setPreview(res.data.preview_text);
    } catch (err) {
      toast.error(err.message);
    }
  };

  if (loading) return (
    <div style={{ textAlign: 'center', padding: 40 }}>
      <div className="spinner" style={{ margin: 'auto' }} />
      <p style={{ marginTop: 12, color: 'var(--text-muted)', fontSize: 13 }}>Loading documents...</p>
    </div>
  );

  if (docs.length === 0) return (
    <div className="empty-state">
      <FileText size={48} />
      <h3>No documents yet</h3>
      <p>Upload a document above to get started</p>
    </div>
  );

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <span style={{ fontSize: 13, color: 'var(--text-secondary)' }}>{docs.length} document{docs.length !== 1 ? 's' : ''}</span>
        <button className="btn btn-ghost btn-sm" onClick={fetchDocs}><RefreshCw size={14} /> Refresh</button>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        {docs.map(doc => (
          <div
            key={doc.id}
            className={`card ${selectedDoc?.id === doc.id ? 'selected' : ''}`}
            style={{ cursor: 'pointer', padding: 14 }}
            onClick={() => onSelect(doc)}
          >
            <div style={{ display: 'flex', alignItems: 'flex-start', gap: 10 }}>
              <TypeIcon type={doc.file_type} />
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontSize: 13, fontWeight: 600, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{doc.name}</div>
                <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>
                  {(doc.file_size / 1024).toFixed(1)} KB · {doc.chunk_count} chunks · {new Date(doc.uploaded_at).toLocaleDateString()}
                </div>
              </div>
              <StatusBadge status={doc.status} />
            </div>
            <div style={{ display: 'flex', gap: 6, marginTop: 10 }}>
              <button className="btn btn-ghost btn-sm" onClick={e => handlePreview(e, doc.id)}>
                <Eye size={13} /> Preview
              </button>
              <button className="btn btn-danger btn-sm" onClick={e => handleDelete(e, doc.id, doc.name)}>
                <Trash2 size={13} /> Delete
              </button>
            </div>
          </div>
        ))}
      </div>

      {preview && (
        <div className="modal-overlay" onClick={() => setPreview(null)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <span className="modal-title">Document Preview</span>
              <button className="btn btn-ghost btn-sm btn-icon" onClick={() => setPreview(null)}>✕</button>
            </div>
            <div style={{ background: 'var(--bg-primary)', borderRadius: 8, padding: 16, fontSize: 12, fontFamily: 'JetBrains Mono, monospace', whiteSpace: 'pre-wrap', maxHeight: 400, overflowY: 'auto', lineHeight: 1.7 }}>
              {preview}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
