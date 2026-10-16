import React, { useState, useRef, useEffect } from 'react';
import {
  Send,
  Bot,
  User,
  Sparkles,
  Bookmark,
  Terminal,
  Cpu,
  HelpCircle,
  FileSearch,
  ExternalLink
} from 'lucide-react';

const SUGGESTED_PROMPTS = [
  "Explain the overall system architecture and key modules",
  "Where is the vector storage and hybrid retrieval logic defined?",
  "How does the syntax-aware AST chunker work?",
  "Show me the configuration and supported LLM providers",
];

export default function ChatPanel({
  activeRepo,
  messages,
  streamingMessage,
  currentCitations,
  isStreaming,
  onSendMessage,
  onJumpToCitation,
}) {
  const [input, setInput] = useState('');
  const messagesEndRef = useRef(null);

  // Auto-scroll chat to bottom as new tokens arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, streamingMessage]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!input.trim() || isStreaming) return;
    onSendMessage(input.trim());
    setInput('');
  };

  const handleChipClick = (prompt) => {
    if (isStreaming) return;
    onSendMessage(prompt);
  };

  const hasMessages = messages.length > 0 || isStreaming;

  return (
    <section className="panel chat-panel">
      <div className="panel-header">
        <div className="panel-header-title">
          <Bot size={15} color="var(--accent-cyan)" />
          <span>Codebase RAG Assistant</span>
        </div>
        {isStreaming && (
          <span style={{ fontSize: '0.72rem', color: 'var(--accent-cyan)', display: 'flex', alignItems: 'center', gap: '4px' }}>
            <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: 'var(--accent-cyan)', display: 'inline-block', animation: 'pulse 1s infinite' }} />
            Streaming response...
          </span>
        )}
      </div>

      {/* Messages Stream Area */}
      <div className="panel-content messages-stream">
        {!hasMessages ? (
          <div className="empty-chat-hero">
            <div className="empty-hero-icon">
              <Sparkles size={28} />
            </div>
            <h2 className="hero-title">Explore {activeRepo?.name || 'Repository'}</h2>
            <p className="hero-subtitle">
              Ask deep architectural questions, find exact function definitions, or inspect how data flows across modules.
            </p>

            <div className="prompt-chips-grid">
              {SUGGESTED_PROMPTS.map((prompt, i) => (
                <button
                  key={i}
                  className="prompt-chip"
                  onClick={() => handleChipClick(prompt)}
                >
                  <FileSearch size={13} style={{ display: 'inline', marginRight: '6px', verticalAlign: 'middle' }} />
                  {prompt}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <>
            {messages.map((msg) => (
              <div key={msg.id} className={`message-row ${msg.role}`}>
                {msg.role === 'assistant' && (
                  <div className="message-avatar assistant">
                    <Bot size={16} />
                  </div>
                )}

                <div className="message-bubble">
                  <div style={{ whiteSpace: 'pre-wrap' }}>{msg.content}</div>

                  {/* Render Citation Badges for assistant message */}
                  {msg.citations && msg.citations.length > 0 && (
                    <div className="citations-tray">
                      <div className="citations-header">
                        <Bookmark size={12} />
                        <span>Referenced Code Snippets ({msg.citations.length})</span>
                      </div>
                      <div className="citation-badges-list">
                        {msg.citations.map((c, idx) => (
                          <div
                            key={idx}
                            className="citation-badge"
                            onClick={() => onJumpToCitation(c)}
                            title={`Jump to ${c.file_path} lines ${c.start_line}-${c.end_line} in Code Inspector`}
                          >
                            <span>
                              {c.file_path.split('/').pop()}:{c.start_line}-{c.end_line}
                            </span>
                            {c.symbol_name && (
                              <span style={{ opacity: 0.7, fontStyle: 'italic' }}>
                                ({c.symbol_name})
                              </span>
                            )}
                            <ExternalLink size={10} />
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>

                {msg.role === 'user' && (
                  <div className="message-avatar user">
                    <User size={16} />
                  </div>
                )}
              </div>
            ))}

            {/* Currently Streaming Message */}
            {isStreaming && (
              <div className="message-row assistant">
                <div className="message-avatar assistant">
                  <Bot size={16} />
                </div>
                <div className="message-bubble">
                  <div style={{ whiteSpace: 'pre-wrap' }}>
                    {streamingMessage || 'Thinking...'}
                  </div>

                  {currentCitations && currentCitations.length > 0 && (
                    <div className="citations-tray">
                      <div className="citations-header">
                        <Bookmark size={12} />
                        <span>Referenced Code Snippets ({currentCitations.length})</span>
                      </div>
                      <div className="citation-badges-list">
                        {currentCitations.map((c, idx) => (
                          <div
                            key={idx}
                            className="citation-badge"
                            onClick={() => onJumpToCitation(c)}
                            title={`Jump to ${c.file_path} lines ${c.start_line}-${c.end_line}`}
                          >
                            <span>
                              {c.file_path.split('/').pop()}:{c.start_line}-{c.end_line}
                            </span>
                            {c.symbol_name && (
                              <span style={{ opacity: 0.7, fontStyle: 'italic' }}>
                                ({c.symbol_name})
                              </span>
                            )}
                            <ExternalLink size={10} />
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      {/* Input Bar */}
      <div className="chat-input-container">
        <form onSubmit={handleSubmit} className="input-box-wrapper">
          <input
            type="text"
            className="chat-input"
            placeholder={`Ask anything about ${activeRepo?.name || 'this codebase'}...`}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={isStreaming}
          />
          <button
            type="submit"
            className="btn-send"
            disabled={!input.trim() || isStreaming}
            title="Send query (Enter)"
          >
            <Send size={15} />
          </button>
        </form>
      </div>
    </section>
  );
}
