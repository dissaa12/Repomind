import React, { useEffect, useRef } from 'react';
import { Code, Copy, Check, FileCode2 } from 'lucide-react';

export default function CodeInspector({
  filePath,
  content,
  language,
  lineCount,
  highlightRange,
  isLoading,
}) {
  const [copied, setCopied] = React.useState(false);
  const highlightedLineRef = useRef(null);

  // Auto-scroll to highlighted line range when citation badge is clicked
  useEffect(() => {
    if (highlightRange && highlightedLineRef.current) {
      highlightedLineRef.current.scrollIntoView({
        behavior: 'smooth',
        block: 'center',
      });
    }
  }, [highlightRange, content]);

  const handleCopy = () => {
    if (!content) return;
    navigator.clipboard.writeText(content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const lines = content ? content.split('\n') : [];

  return (
    <section className="panel code-inspector-panel">
      <div className="panel-header">
        <div className="panel-header-title">
          <FileCode2 size={15} color="var(--accent-purple)" />
          <span style={{ maxWidth: '240px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
            {filePath ? filePath.split('/').pop() : 'Code Inspector'}
          </span>
        </div>

        {filePath && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
              {lineCount || lines.length} lines
            </span>
            <button
              className="btn btn-icon"
              style={{ width: '26px', height: '26px' }}
              onClick={handleCopy}
              title="Copy file content"
            >
              {copied ? <Check size={12} color="var(--accent-emerald)" /> : <Copy size={12} />}
            </button>
          </div>
        )}
      </div>

      {/* Inspector Body */}
      <div className="panel-content" style={{ display: 'flex', flexDirection: 'column' }}>
        {isLoading ? (
          <div style={{ padding: '30px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
            Loading file source...
          </div>
        ) : !filePath || !content ? (
          <div style={{ padding: '40px 20px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
            <Code size={32} style={{ marginBottom: '12px', opacity: 0.3 }} />
            <p>Select any file from the explorer or click a citation badge in chat to inspect code here.</p>
          </div>
        ) : (
          <div className="code-viewer-container">
            {/* Line Numbers Gutter */}
            <div className="line-numbers-col">
              {lines.map((_, i) => (
                <div key={i + 1} className="code-line">
                  {i + 1}
                </div>
              ))}
            </div>

            {/* Code Content */}
            <div className="code-content-col">
              {lines.map((line, i) => {
                const lineNum = i + 1;
                const isHighlighted =
                  highlightRange &&
                  lineNum >= highlightRange.start &&
                  lineNum <= highlightRange.end;

                return (
                  <div
                    key={lineNum}
                    ref={isHighlighted && lineNum === highlightRange.start ? highlightedLineRef : null}
                    className={`code-line ${isHighlighted ? 'highlighted' : ''}`}
                  >
                    {line || ' '}
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </section>
  );
}
