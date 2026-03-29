import { useState } from 'react';
import { Toaster } from 'react-hot-toast';
import { UploadCloud, FileText, CheckCircle, Send } from 'lucide-react';
import UploadZone from './components/UploadZone';
import DocumentList from './components/DocumentList';
import GeneratePanel from './components/GeneratePanel';
import TestCaseReview from './components/TestCaseReview';
import JiraPanel from './components/JiraPanel';
import './index.css';

const TABS = [
  { id: 'upload', label: 'Upload', icon: UploadCloud },
  { id: 'review', label: 'Review', icon: CheckCircle },
  { id: 'jira', label: 'Jira', icon: Send },
];

export default function App() {
  const [activeTab, setActiveTab] = useState('upload');
  const [selectedDoc, setSelectedDoc] = useState(null);
  const [docRefresh, setDocRefresh] = useState(0);
  const [tcRefresh, setTcRefresh] = useState(0);

  const handleUploaded = () => setDocRefresh(n => n + 1);
  const handleGenerated = () => setTcRefresh(n => n + 1);

  return (
    <div className="app-layout">
      <Toaster position="top-right" toastOptions={{ duration: 4000 }} />

      {/* Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-logo">
          <h1>🚀 TestOrbit</h1>
          <p>AI-Powered QA</p>
        </div>
        <nav className="sidebar-nav">
          {TABS.map(tab => (
            <button
              key={tab.id}
              className={`nav-item ${activeTab === tab.id ? 'active' : ''}`}
              onClick={() => setActiveTab(tab.id)}
            >
              <tab.icon size={18} />
              {tab.label}
            </button>
          ))}
        </nav>

        {/* Selected doc indicator */}
        {selectedDoc && (
          <div style={{ padding: '12px 16px', borderTop: '1px solid var(--border)', fontSize: 12 }}>
            <div style={{ color: 'var(--text-muted)', marginBottom: 4 }}>ACTIVE DOCUMENT</div>
            <div style={{ color: 'var(--text-primary)', fontWeight: 600, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{selectedDoc.name}</div>
            <span className={`badge badge-${selectedDoc.status}`} style={{ marginTop: 6 }}>{selectedDoc.status}</span>
          </div>
        )}
      </aside>

      {/* Main */}
      <main className="main-content">
        {/* ── Upload Tab ── */}
        {activeTab === 'upload' && (
          <>
            <div className="page-header">
              <h2>Document Management</h2>
              <p>Upload documents to extract requirements and generate Gherkin test cases via RAG pipeline</p>
            </div>
            <div className="page-body">
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24, alignItems: 'start' }}>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
                  <UploadZone onUploaded={handleUploaded} />
                  <GeneratePanel document={selectedDoc} onGenerated={handleGenerated} />
                </div>
                <DocumentList
                  selectedDoc={selectedDoc}
                  onSelect={setSelectedDoc}
                  refreshTrigger={docRefresh}
                />
              </div>
            </div>
          </>
        )}

        {/* ── Review Tab ── */}
        {activeTab === 'review' && (
          <>
            <div className="page-header">
              <h2>QA Review Dashboard</h2>
              <p>Review, approve, reject, and edit generated Gherkin test cases
                {selectedDoc && <> · <strong style={{ color: 'var(--accent)' }}>{selectedDoc.name}</strong></>}
              </p>
            </div>
            <div className="page-body">
              {!selectedDoc && (
                <div style={{ background: 'var(--warning-bg)', border: '1px solid var(--warning)', borderRadius: 10, padding: '14px 18px', fontSize: 13, color: 'var(--warning)', marginBottom: 20, display: 'flex', gap: 8, alignItems: 'center' }}>
                  ⚠️ No document selected. Go to the Upload tab, select a document, then come back here.
                </div>
              )}
              <TestCaseReview
                documentId={selectedDoc?.id}
                refreshTrigger={tcRefresh}
                onApprovedChange={() => {}}
              />
            </div>
          </>
        )}

        {/* ── Jira Tab ── */}
        {activeTab === 'jira' && (
          <>
            <div className="page-header">
              <h2>Jira Integration</h2>
              <p>Configure Jira and inject approved test cases as issues</p>
            </div>
            <div className="page-body" style={{ maxWidth: 640 }}>
              <JiraPanel documentId={selectedDoc?.id} />
            </div>
          </>
        )}
      </main>
    </div>
  );
}
