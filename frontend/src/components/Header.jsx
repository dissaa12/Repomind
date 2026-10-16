import React from 'react';
import { Layers, GitBranch, Settings, Plus, Sparkles, ChevronDown, Palette } from 'lucide-react';

export default function Header({
  repos,
  activeRepo,
  onSelectRepo,
  onOpenIngestModal,
  onOpenSettingsModal,
  onOpenStitchModal,
  settings,
}) {
  return (
    <header className="top-header">
      <div className="brand-section">
        <a href="#" className="brand-logo">
          <div className="logo-badge">
            <Layers size={18} color="#fff" />
          </div>
          <span>Repomind</span>
        </a>

        {/* Repository Switcher Pill */}
        {repos && repos.length > 0 && (
          <div className="repo-selector-pill" title="Switch active repository">
            <GitBranch size={14} color="var(--accent-cyan)" />
            <select
              value={activeRepo?.id || ''}
              onChange={(e) => {
                const selected = repos.find((r) => r.id === e.target.value);
                if (selected) onSelectRepo(selected);
              }}
              style={{
                background: 'transparent',
                border: 'none',
                color: 'inherit',
                outline: 'none',
                cursor: 'pointer',
                fontWeight: 600,
                fontSize: '0.85rem',
              }}
            >
              {repos.map((r) => (
                <option key={r.id} value={r.id} style={{ background: '#0F172A', color: '#fff' }}>
                  {r.name} ({r.chunk_count} chunks)
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      <div className="header-actions">
        {/* Active Model Indicator */}
        <div
          className="repo-selector-pill"
          style={{ cursor: 'default', borderColor: 'rgba(99, 102, 241, 0.3)' }}
          title="Active LLM Engine"
        >
          <Sparkles size={13} color="var(--accent-primary)" />
          <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
            {settings?.active_provider?.toUpperCase() || 'MOCK AI'}
          </span>
        </div>

        {/* Google Stitch Studio Button */}
        <button
          className="btn btn-secondary"
          onClick={onOpenStitchModal}
          title="Google Stitch UI Studio & MCP Design Sync"
          style={{ borderColor: 'rgba(6, 182, 212, 0.4)' }}
        >
          <Palette size={14} color="var(--accent-cyan)" />
          <span>Stitch</span>
        </button>

        {/* Ingest Repository Button */}
        <button
          className="btn btn-primary"
          onClick={onOpenIngestModal}
          title="Index a new local directory or GitHub repo"
        >
          <Plus size={15} />
          <span>Ingest Repo</span>
        </button>

        {/* Settings Button */}
        <button
          className="btn btn-icon"
          onClick={onOpenSettingsModal}
          title="Configure API Keys & LLM Settings"
        >
          <Settings size={16} />
        </button>
      </div>
    </header>
  );
}
