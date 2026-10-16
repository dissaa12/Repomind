import React, { useState } from 'react';
import {
  Folder,
  FolderOpen,
  FileCode,
  FileText,
  Search,
  ChevronRight,
  ChevronDown,
  Database,
  Code2
} from 'lucide-react';

function getFileIcon(fileName, language) {
  if (language === 'python') return <FileCode size={14} color="#38BDF8" />;
  if (language === 'javascript' || language === 'typescript')
    return <FileCode size={14} color="#FBBF24" />;
  if (language === 'markdown') return <FileText size={14} color="#A78BFA" />;
  if (language === 'json' || language === 'yaml')
    return <Database size={14} color="#34D399" />;
  return <FileText size={14} color="#94A3B8" />;
}

function TreeNode({ item, onSelectFile, activeFilePath, filterText }) {
  const [isOpen, setIsOpen] = useState(true);

  if (item.type === 'directory') {
    // If filter text exists, check if any child matches
    const hasVisibleChildren = item.children && item.children.length > 0;
    if (!hasVisibleChildren && filterText) return null;

    return (
      <div style={{ marginLeft: '8px' }}>
        <div
          className="tree-node"
          onClick={() => setIsOpen(!isOpen)}
          style={{ fontWeight: 500 }}
        >
          {isOpen ? (
            <ChevronDown size={14} color="var(--text-muted)" />
          ) : (
            <ChevronRight size={14} color="var(--text-muted)" />
          )}
          {isOpen ? (
            <FolderOpen size={14} color="var(--accent-primary)" />
          ) : (
            <Folder size={14} color="var(--accent-primary)" />
          )}
          <span style={{ color: 'var(--text-primary)' }}>{item.name}</span>
        </div>

        {isOpen && (
          <div style={{ borderLeft: '1px solid rgba(255,255,255,0.06)', marginLeft: '12px' }}>
            {item.children.map((child) => (
              <TreeNode
                key={child.path}
                item={child}
                onSelectFile={onSelectFile}
                activeFilePath={activeFilePath}
                filterText={filterText}
              />
            ))}
          </div>
        )}
      </div>
    );
  }

  // File Node
  if (filterText && !item.path.toLowerCase().includes(filterText.toLowerCase())) {
    return null;
  }

  const isActive = activeFilePath === item.path;

  return (
    <div
      className={`tree-node ${isActive ? 'active' : ''}`}
      style={{ marginLeft: '14px' }}
      onClick={() => onSelectFile(item.path)}
      title={`${item.path} (${item.line_count || 0} lines)`}
    >
      {getFileIcon(item.name, item.language)}
      <span style={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
        {item.name}
      </span>
      {item.line_count > 0 && (
        <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
          {item.line_count}L
        </span>
      )}
    </div>
  );
}

export default function FileExplorer({
  activeRepo,
  fileTree,
  onSelectFile,
  activeFilePath,
}) {
  const [filterText, setFilterText] = useState('');

  const languages = activeRepo?.languages || {};

  return (
    <aside className="panel file-explorer-panel">
      <div className="panel-header">
        <div className="panel-header-title">
          <Code2 size={15} color="var(--accent-primary)" />
          <span>Explorer</span>
        </div>
        <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
          {activeRepo?.file_count || 0} files
        </span>
      </div>

      {/* Filter / Search File Bar */}
      <div className="file-search-bar">
        <div className="search-input-wrapper">
          <Search size={14} />
          <input
            type="text"
            className="search-input"
            placeholder="Search files (e.g. main.py)..."
            value={filterText}
            onChange={(e) => setFilterText(e.target.value)}
          />
        </div>
      </div>

      {/* File Tree View */}
      <div className="panel-content" style={{ padding: '8px 4px' }}>
        {fileTree && fileTree.length > 0 ? (
          fileTree.map((node) => (
            <TreeNode
              key={node.path}
              item={node}
              onSelectFile={onSelectFile}
              activeFilePath={activeFilePath}
              filterText={filterText}
            />
          ))
        ) : (
          <div style={{ padding: '24px 16px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.82rem' }}>
            No files loaded in this repository.
          </div>
        )}
      </div>

      {/* Language Breakdown Footer */}
      {Object.keys(languages).length > 0 && (
        <div className="repo-meta-summary">
          <span style={{ fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
            Languages
          </span>
          <div className="lang-tag-bar">
            {Object.entries(languages).map(([lang, count]) => (
              <span key={lang} className="lang-pill">
                {lang}: {count}
              </span>
            ))}
          </div>
        </div>
      )}
    </aside>
  );
}
