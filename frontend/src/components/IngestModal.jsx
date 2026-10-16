import React, { useState } from 'react';
import { X, Folder, GitBranch, Loader2, CheckCircle2, AlertCircle } from 'lucide-react';

export default function IngestModal({ isOpen, onClose, onRepoIndexed }) {
  const [activeTab, setActiveTab] = useState('local'); // 'local' or 'github'
  const [localPath, setLocalPath] = useState('');
  const [repoName, setRepoName] = useState('');
  const [githubUrl, setGithubUrl] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const [successMsg, setSuccessMsg] = useState('');

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMsg('');
    setSuccessMsg('');
    setIsSubmitting(true);

    try {
      const payload =
        activeTab === 'local'
          ? { source_type: 'local', path_or_url: localPath.trim(), name: repoName.trim() || undefined }
          : { source_type: 'github', path_or_url: githubUrl.trim() };

      const res = await fetch('/api/repos/index', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || 'Indexing failed');
      }

      setSuccessMsg(
        `Successfully indexed "${data.repo.name}" (${data.repo.file_count} files, ${data.repo.chunk_count} chunks)!`
      );
      if (onRepoIndexed) {
        onRepoIndexed(data.repo);
      }
      setTimeout(() => {
        onClose();
      }, 1400);
    } catch (err) {
      setErrorMsg(err.message);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-card" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <span>Ingest & Index Codebase</span>
          <button className="btn btn-icon" onClick={onClose}>
            <X size={16} />
          </button>
        </div>

        {/* Tab Switcher */}
        <div style={{ display: 'flex', borderBottom: '1px solid var(--border-subtle)', background: 'var(--bg-base)' }}>
          <button
            type="button"
            onClick={() => setActiveTab('local')}
            style={{
              flex: 1,
              padding: '10px',
              background: activeTab === 'local' ? 'var(--bg-surface)' : 'transparent',
              color: activeTab === 'local' ? 'var(--accent-primary)' : 'var(--text-secondary)',
              border: 'none',
              borderBottom: activeTab === 'local' ? '2px solid var(--accent-primary)' : 'none',
              fontWeight: 600,
              fontSize: '0.85rem',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '6px',
              cursor: 'pointer',
            }}
          >
            <Folder size={15} />
            <span>Local Directory</span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab('github')}
            style={{
              flex: 1,
              padding: '10px',
              background: activeTab === 'github' ? 'var(--bg-surface)' : 'transparent',
              color: activeTab === 'github' ? 'var(--accent-cyan)' : 'var(--text-secondary)',
              border: 'none',
              borderBottom: activeTab === 'github' ? '2px solid var(--accent-cyan)' : 'none',
              fontWeight: 600,
              fontSize: '0.85rem',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '6px',
              cursor: 'pointer',
            }}
          >
            <GitBranch size={15} />
            <span>GitHub Repository</span>
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="modal-body">
            {errorMsg && (
              <div style={{ padding: '10px 14px', background: 'rgba(244, 63, 94, 0.12)', border: '1px solid var(--accent-rose)', borderRadius: '8px', color: 'var(--accent-rose)', fontSize: '0.82rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <AlertCircle size={15} />
                <span>{errorMsg}</span>
              </div>
            )}

            {successMsg && (
              <div style={{ padding: '10px 14px', background: 'rgba(16, 185, 129, 0.12)', border: '1px solid var(--accent-emerald)', borderRadius: '8px', color: 'var(--accent-emerald)', fontSize: '0.82rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <CheckCircle2 size={15} />
                <span>{successMsg}</span>
              </div>
            )}

            {activeTab === 'local' ? (
              <>
                <div className="form-group">
                  <label className="form-label">Absolute Directory Path</label>
                  <input
                    type="text"
                    className="form-input"
                    placeholder="e.g. C:\Users\patil\OneDrive\Desktop\Repomind\Naive_RAG"
                    value={localPath}
                    onChange={(e) => setLocalPath(e.target.value)}
                    required
                  />
                  <span style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>
                    Any folder on your local machine containing source code.
                  </span>
                </div>

                <div className="form-group">
                  <label className="form-label">Custom Repository Name (Optional)</label>
                  <input
                    type="text"
                    className="form-input"
                    placeholder="e.g. Naive RAG Demo"
                    value={repoName}
                    onChange={(e) => setRepoName(e.target.value)}
                  />
                </div>
              </>
            ) : (
              <div className="form-group">
                <label className="form-label">GitHub Repository URL or Slug</label>
                <input
                  type="text"
                  className="form-input"
                  placeholder="e.g. https://github.com/fastapi/fastapi or owner/repo"
                  value={githubUrl}
                  onChange={(e) => setGithubUrl(e.target.value)}
                  required
                />
                <span style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>
                  Shallow clones and parses the repository into Repomind cache.
                </span>
              </div>
            )}
          </div>

          <div className="modal-footer">
            <button type="button" className="btn btn-secondary" onClick={onClose} disabled={isSubmitting}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary" disabled={isSubmitting}>
              {isSubmitting ? (
                <>
                  <Loader2 size={15} className="animate-spin" style={{ animation: 'spin 1s linear infinite' }} />
                  <span>Indexing Codebase...</span>
                </>
              ) : (
                <span>Start Indexing</span>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
