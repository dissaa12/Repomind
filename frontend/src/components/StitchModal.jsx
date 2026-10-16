import React, { useState, useEffect } from 'react';
import { X, Palette, Sparkles, CheckCircle2, RefreshCw, ExternalLink, Layers, Layout } from 'lucide-react';

export default function StitchModal({ isOpen, onClose }) {
  const [projectId, setProjectId] = useState('repomind-stitch-v1');
  const [apiKey, setApiKey] = useState('');
  const [stitchStatus, setStitchStatus] = useState(null);
  const [syncResult, setSyncResult] = useState(null);
  const [isSyncing, setIsSyncing] = useState(false);
  const [msg, setMsg] = useState('');

  useEffect(() => {
    if (isOpen) {
      fetchStatus();
    }
  }, [isOpen]);

  const fetchStatus = async () => {
    try {
      const res = await fetch('/api/stitch/status');
      if (res.ok) {
        const data = await res.json();
        setStitchStatus(data);
        if (data.project_id) setProjectId(data.project_id);
      }
    } catch (e) {
      console.error('Error fetching stitch status:', e);
    }
  };

  const handleSync = async (e) => {
    e.preventDefault();
    setIsSyncing(true);
    setMsg('');

    try {
      const res = await fetch('/api/stitch/sync', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          project_id: projectId.trim(),
          api_key: apiKey.trim() || undefined,
        }),
      });

      const data = await res.json();
      if (res.ok) {
        setSyncResult(data.design_system);
        setMsg(`Successfully synced with Stitch project "${data.project_id}"!`);
      }
    } catch (err) {
      setMsg(`Sync failed: ${err.message}`);
    } finally {
      setIsSyncing(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-card" style={{ maxWidth: '640px' }} onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Palette size={18} color="var(--accent-cyan)" />
            <span>Google Stitch UI Studio & MCP Sync</span>
          </div>
          <button className="btn btn-icon" onClick={onClose}>
            <X size={16} />
          </button>
        </div>

        <div className="modal-body" style={{ maxHeight: '75vh', overflowY: 'auto' }}>
          {/* Status banner */}
          <div
            style={{
              padding: '12px 16px',
              borderRadius: '8px',
              background: 'rgba(6, 182, 212, 0.08)',
              border: '1px solid rgba(6, 182, 212, 0.25)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              fontSize: '0.85rem',
            }}
          >
            <div>
              <div style={{ fontWeight: 600, color: 'var(--accent-cyan)' }}>
                Google Stitch MCP: Connected via <code style={{ color: '#fff' }}>stitch-mcp</code>
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '2px' }}>
                Bridges Google Stitch visual canvas design tokens to this React frontend.
              </div>
            </div>
            <a
              href="https://stitch.withgoogle.com"
              target="_blank"
              rel="noreferrer"
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
                color: 'var(--accent-cyan)',
                textDecoration: 'none',
                fontSize: '0.75rem',
                fontWeight: 600,
              }}
            >
              <span>Open Stitch</span>
              <ExternalLink size={12} />
            </a>
          </div>

          {msg && (
            <div
              style={{
                padding: '10px 14px',
                background: 'rgba(16, 185, 129, 0.12)',
                border: '1px solid var(--accent-emerald)',
                borderRadius: '8px',
                color: 'var(--accent-emerald)',
                fontSize: '0.82rem',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
              }}
            >
              <CheckCircle2 size={15} />
              <span>{msg}</span>
            </div>
          )}

          {/* Sync Form */}
          <form onSubmit={handleSync} style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <div className="form-group">
              <label className="form-label">Stitch Project ID or Canvas Name</label>
              <input
                type="text"
                className="form-input"
                placeholder="e.g. repomind-stitch-v1 or project URL"
                value={projectId}
                onChange={(e) => setProjectId(e.target.value)}
                required
              />
            </div>

            <div className="form-group">
              <label className="form-label">Stitch API Key (Optional if set in .env)</label>
              <input
                type="password"
                className="form-input"
                placeholder="stitch_api_key_..."
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
              />
            </div>

            <button
              type="submit"
              className="btn btn-primary"
              disabled={isSyncing}
              style={{ alignSelf: 'flex-start', marginTop: '4px' }}
            >
              <RefreshCw size={14} className={isSyncing ? 'animate-spin' : ''} />
              <span>{isSyncing ? 'Syncing Canvas...' : 'Sync Design Tokens & Screens'}</span>
            </button>
          </form>

          <hr style={{ border: 'none', borderTop: '1px solid var(--border-subtle)', margin: '8px 0' }} />

          {/* Synced Design Tokens Preview */}
          <div>
            <h4 style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '10px', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Layers size={14} color="var(--accent-primary)" />
              <span>Active Stitch Design System Tokens</span>
            </h4>

            {/* Colors */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: '8px', marginBottom: '16px' }}>
              <div style={{ background: '#090D16', border: '1px solid var(--border-subtle)', borderRadius: '6px', padding: '8px', textAlign: 'center', fontSize: '0.7rem' }}>
                <div style={{ width: '100%', height: '20px', background: '#090D16', borderRadius: '4px', marginBottom: '4px' }} />
                <span>Base #090D16</span>
              </div>
              <div style={{ background: '#0F172A', border: '1px solid var(--border-subtle)', borderRadius: '6px', padding: '8px', textAlign: 'center', fontSize: '0.7rem' }}>
                <div style={{ width: '100%', height: '20px', background: '#0F172A', borderRadius: '4px', marginBottom: '4px' }} />
                <span>Surface #0F172A</span>
              </div>
              <div style={{ background: '#6366F1', border: '1px solid var(--border-subtle)', borderRadius: '6px', padding: '8px', textAlign: 'center', fontSize: '0.7rem', color: '#fff' }}>
                <div style={{ width: '100%', height: '20px', background: '#6366F1', borderRadius: '4px', marginBottom: '4px' }} />
                <span>Primary #6366F1</span>
              </div>
              <div style={{ background: '#06B6D4', border: '1px solid var(--border-subtle)', borderRadius: '6px', padding: '8px', textAlign: 'center', fontSize: '0.7rem', color: '#000' }}>
                <div style={{ width: '100%', height: '20px', background: '#06B6D4', borderRadius: '4px', marginBottom: '4px' }} />
                <span>Cyan #06B6D4</span>
              </div>
              <div style={{ background: '#10B981', border: '1px solid var(--border-subtle)', borderRadius: '6px', padding: '8px', textAlign: 'center', fontSize: '0.7rem', color: '#000' }}>
                <div style={{ width: '100%', height: '20px', background: '#10B981', borderRadius: '4px', marginBottom: '4px' }} />
                <span>Emerald #10B981</span>
              </div>
            </div>

            {/* Synced Screens List */}
            <h4 style={{ fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Layout size={13} />
              <span>Connected Canvas Screens</span>
            </h4>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 12px', background: 'var(--bg-base)', borderRadius: '6px', border: '1px solid var(--border-subtle)', fontSize: '0.8rem' }}>
                <span>📁 Left Panel: File Explorer & AST Hierarchy</span>
                <span style={{ color: 'var(--accent-emerald)', fontWeight: 600 }}>Active</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 12px', background: 'var(--bg-base)', borderRadius: '6px', border: '1px solid var(--border-subtle)', fontSize: '0.8rem' }}>
                <span>💬 Center Panel: Streaming RAG Chat Assistant</span>
                <span style={{ color: 'var(--accent-emerald)', fontWeight: 600 }}>Active</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 12px', background: 'var(--bg-base)', borderRadius: '6px', border: '1px solid var(--border-subtle)', fontSize: '0.8rem' }}>
                <span>📜 Right Panel: Code Inspector & Auto-Scroll Citations</span>
                <span style={{ color: 'var(--accent-emerald)', fontWeight: 600 }}>Active</span>
              </div>
            </div>
          </div>
        </div>

        <div className="modal-footer">
          <button className="btn btn-secondary" onClick={onClose}>
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
