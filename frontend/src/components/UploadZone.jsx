import { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, File, X, CheckCircle, AlertCircle, Loader } from 'lucide-react';
import toast from 'react-hot-toast';
import { uploadDocument } from '../api/documents';

const ALLOWED_TYPES = {
  'text/plain': ['.txt'],
  'application/pdf': ['.pdf'],
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
  'application/json': ['.json'],
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
  'text/csv': ['.csv'],
};

function FileItem({ file, status, progress, error }) {
  const icons = {
    uploading: <div className="spinner" style={{ width: 16, height: 16 }} />,
    processing: <Loader size={16} className="pulse" color="var(--warning)" />,
    done: <CheckCircle size={16} color="var(--success)" />,
    error: <AlertCircle size={16} color="var(--danger)" />,
  };
  return (
    <div style={{ display: 'flex', gap: 10, alignItems: 'flex-start', padding: '10px 0', borderBottom: '1px solid var(--border)' }}>
      <File size={18} color="var(--text-secondary)" style={{ marginTop: 2, flexShrink: 0 }} />
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontSize: 13, fontWeight: 500, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{file.name}</div>
        <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>{(file.size / 1024).toFixed(1)} KB</div>
        {(status === 'uploading' || status === 'processing') && (
          <div className="progress-bar">
            <div className="progress-fill" style={{ width: `${progress}%` }} />
          </div>
        )}
        {error && <div style={{ fontSize: 11, color: 'var(--danger)', marginTop: 4 }}>{error}</div>}
      </div>
      <div style={{ flexShrink: 0 }}>{icons[status] || null}</div>
    </div>
  );
}

export default function UploadZone({ onUploaded }) {
  const [queue, setQueue] = useState([]);

  const updateItem = (name, updates) =>
    setQueue(q => q.map(i => i.file.name === name ? { ...i, ...updates } : i));

  const processFile = useCallback(async (file) => {
    setQueue(q => [...q, { file, status: 'uploading', progress: 0, error: null }]);
    try {
      await uploadDocument(file, (pct) => updateItem(file.name, { progress: pct }));
      updateItem(file.name, { status: 'done', progress: 100 });
      toast.success(`"${file.name}" uploaded and processing!`);
      onUploaded?.();
    } catch (err) {
      updateItem(file.name, { status: 'error', error: err.message });
      toast.error(`Upload failed: ${err.message}`);
    }
  }, [onUploaded]);

  const onDrop = useCallback((accepted, rejected) => {
    if (rejected.length > 0) {
      toast.error(`${rejected.length} file(s) rejected. Check file type or size.`);
    }
    accepted.forEach(processFile);
  }, [processFile]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: ALLOWED_TYPES,
    maxSize: 50 * 1024 * 1024,
    multiple: true,
  });

  return (
    <div>
      <div {...getRootProps()} className={`upload-zone ${isDragActive ? 'drag-active' : ''}`}>
        <input {...getInputProps()} />
        <Upload size={40} />
        <h3>{isDragActive ? 'Drop files here...' : 'Drag & drop files here'}</h3>
        <p>or click to browse · Supports .txt, .pdf, .docx, .json, .xlsx, .csv · Max 50MB</p>
      </div>

      {queue.length > 0 && (
        <div className="card" style={{ marginTop: 16 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
            <span style={{ fontSize: 13, fontWeight: 600 }}>Upload Queue ({queue.length})</span>
            <button className="btn btn-ghost btn-sm" onClick={() => setQueue([])}>
              <X size={14} /> Clear
            </button>
          </div>
          {queue.map(item => (
            <FileItem key={item.file.name} {...item} />
          ))}
        </div>
      )}
    </div>
  );
}
