import React, { useState, useEffect } from 'react';
import { X, Key, Cpu, Sparkles, CheckCircle2, AlertCircle } from 'lucide-react';

const PROVIDER_OPTIONS = [
  { id: 'gemini', name: 'Google Gemini', defaultModel: 'gemini-3.8-flash' },
  { id: 'openai', name: 'OpenAI', defaultModel: 'gpt-4o-mini' },
  { id: 'groq', name: 'Groq Cloud', defaultModel: 'llama-3.3-70b-versatile' },
  { id: 'ollama', name: 'Local Ollama', defaultModel: 'llama3.2' },
  { id: 'mock', name: 'Mock AI (Offline Grounded Demo)', defaultModel: 'mock-engine' },
];

export default function SettingsModal({ isOpen, onClose, currentSettings, onSettingsUpdated }) {
  const [provider, setProvider] = useState('gemini');
  const [model, setModel] = useState('gemini-3.8-flash');
  const [geminiKey, setGeminiKey] = useState('');
  const [openaiKey, setOpenaiKey] = useState('');
  const [groqKey, setGroqKey] = useState('');
  const [githubToken, setGithubToken] = useState('');
  const [ollamaUrl, setOllamaUrl] = useState('http://localhost:11434');
  const [statusMsg, setStatusMsg] = useState('');

  useEffect(() => {
    if (currentSettings) {
      if (currentSettings.active_provider) setProvider(currentSettings.active_provider);
      if (currentSettings.active_model) setModel(currentSettings.active_model);
      if (currentSettings.ollama_base_url) setOllamaUrl(currentSettings.ollama_base_url);
    }
  }, [currentSettings, isOpen]);

  if (!isOpen) return null;

  const handleProviderChange = (e) => {
    const newProv = e.target.value;
    setProvider(newProv);
    const matched = PROVIDER_OPTIONS.find((p) => p.id === newProv);
    if (matched) setModel(matched.defaultModel);
  };

  const handleSave = async (e) => {
    e.preventDefault();
    try {
      const payload = {
        active_provider: provider,
        active_model: model,
        gemini_api_key: geminiKey.trim() || undefined,
        openai_api_key: openaiKey.trim() || undefined,
        groq_api_key: groqKey.trim() || undefined,
        github_token: githubToken.trim() || undefined,
        ollama_base_url: ollamaUrl.trim() || undefined,
      };

      const res = await fetch('/api/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      const data = await res.json();
      if (res.ok) {
        setStatusMsg('Settings successfully updated!');
        if (onSettingsUpdated) onSettingsUpdated(data.settings);
        setTimeout(() => {
          setStatusMsg('');
          onClose();
        }, 1000);
      }
    } catch (err) {
      setStatusMsg(`Error updating settings: ${err.message}`);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-card" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Key size={18} color="var(--accent-primary)" />
            <span>LLM Providers & API Keys</span>
          </div>
          <button className="btn btn-icon" onClick={onClose}>
            <X size={16} />
          </button>
        </div>

        <form onSubmit={handleSave}>
          <div className="modal-body" style={{ maxHeight: '70vh', overflowY: 'auto' }}>
            {statusMsg && (
              <div style={{ padding: '10px 14px', background: 'rgba(16, 185, 129, 0.12)', border: '1px solid var(--accent-emerald)', borderRadius: '8px', color: 'var(--accent-emerald)', fontSize: '0.82rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <CheckCircle2 size={15} />
                <span>{statusMsg}</span>
              </div>
            )}

            {/* Provider Select */}
            <div className="form-group">
              <label className="form-label">Active Generation Provider</label>
              <select className="form-select" value={provider} onChange={handleProviderChange}>
                {PROVIDER_OPTIONS.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name}
                  </option>
                ))}
              </select>
            </div>

            {/* Model Name */}
            <div className="form-group">
              <label className="form-label">Model Name</label>
              <input
                type="text"
                className="form-input"
                value={model}
                onChange={(e) => setModel(e.target.value)}
                placeholder="e.g. gemini-2.0-flash, gemini-1.5-flash, gpt-4o-mini, llama-3.3-70b-versatile"
              />
            </div>

            <hr style={{ border: 'none', borderTop: '1px solid var(--border-subtle)', margin: '4px 0' }} />

            {/* Gemini API Key */}
            <div className="form-group">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <label className="form-label">Google Gemini API Key</label>
                {currentSettings?.gemini_api_key_set && (
                  <span style={{ fontSize: '0.7rem', color: 'var(--accent-emerald)' }}>✓ Configured</span>
                )}
              </div>
              <input
                type="password"
                className="form-input"
                placeholder="AIzaSy..."
                value={geminiKey}
                onChange={(e) => setGeminiKey(e.target.value)}
              />
            </div>

            {/* OpenAI API Key */}
            <div className="form-group">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <label className="form-label">OpenAI API Key</label>
                {currentSettings?.openai_api_key_set && (
                  <span style={{ fontSize: '0.7rem', color: 'var(--accent-emerald)' }}>✓ Configured</span>
                )}
              </div>
              <input
                type="password"
                className="form-input"
                placeholder="sk-proj-..."
                value={openaiKey}
                onChange={(e) => setOpenaiKey(e.target.value)}
              />
            </div>

            {/* Groq API Key */}
            <div className="form-group">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <label className="form-label">Groq API Key</label>
                {currentSettings?.groq_api_key_set && (
                  <span style={{ fontSize: '0.7rem', color: 'var(--accent-emerald)' }}>✓ Configured</span>
                )}
              </div>
              <input
                type="password"
                className="form-input"
                placeholder="gsk_..."
                value={groqKey}
                onChange={(e) => setGroqKey(e.target.value)}
              />
            </div>

            {/* GitHub Token */}
            <div className="form-group">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <label className="form-label">GitHub Token (Optional for private repos)</label>
                {currentSettings?.github_token_set && (
                  <span style={{ fontSize: '0.7rem', color: 'var(--accent-emerald)' }}>✓ Configured</span>
                )}
              </div>
              <input
                type="password"
                className="form-input"
                placeholder="ghp_..."
                value={githubToken}
                onChange={(e) => setGithubToken(e.target.value)}
              />
            </div>

            {/* Ollama URL */}
            {provider === 'ollama' && (
              <div className="form-group">
                <label className="form-label">Ollama Base URL</label>
                <input
                  type="text"
                  className="form-input"
                  value={ollamaUrl}
                  onChange={(e) => setOllamaUrl(e.target.value)}
                  placeholder="http://localhost:11434"
                />
              </div>
            )}
          </div>

          <div className="modal-footer">
            <button type="button" className="btn btn-secondary" onClick={onClose}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary">
              Save Configuration
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
