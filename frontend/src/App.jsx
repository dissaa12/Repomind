import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import FileExplorer from './components/FileExplorer';
import ChatPanel from './components/ChatPanel';
import CodeInspector from './components/CodeInspector';
import IngestModal from './components/IngestModal';
import SettingsModal from './components/SettingsModal';
import StitchModal from './components/StitchModal';

export default function App() {
  const [repos, setRepos] = useState([]);
  const [activeRepo, setActiveRepo] = useState(null);
  const [fileTree, setFileTree] = useState([]);
  const [activeFilePath, setActiveFilePath] = useState('');
  const [fileContent, setFileContent] = useState('');
  const [fileLineCount, setFileLineCount] = useState(0);
  const [isFileLoading, setIsFileLoading] = useState(false);
  const [highlightRange, setHighlightRange] = useState(null);

  const [messages, setMessages] = useState([]);
  const [streamingMessage, setStreamingMessage] = useState('');
  const [currentCitations, setCurrentCitations] = useState([]);
  const [isStreaming, setIsStreaming] = useState(false);

  const [settings, setSettings] = useState(null);
  const [isIngestModalOpen, setIsIngestModalOpen] = useState(false);
  const [isSettingsModalOpen, setIsSettingsModalOpen] = useState(false);
  const [isStitchModalOpen, setIsStitchModalOpen] = useState(false);

  // 1. Initial Load: Fetch Repos & Settings
  useEffect(() => {
    fetchRepos();
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      const res = await fetch('/api/settings');
      if (res.ok) {
        const data = await res.json();
        setSettings(data);
      }
    } catch (e) {
      console.error('Failed to load settings:', e);
    }
  };

  const fetchRepos = async () => {
    try {
      const res = await fetch('/api/repos');
      if (res.ok) {
        const data = await res.json();
        setRepos(data);
        if (data.length > 0 && !activeRepo) {
          selectRepository(data[0]);
        }
      }
    } catch (e) {
      console.error('Failed to load repos:', e);
    }
  };

  // 2. Select Repository & Load its Tree & Messages
  const selectRepository = async (repo) => {
    setActiveRepo(repo);
    setHighlightRange(null);
    setStreamingMessage('');
    setCurrentCitations([]);

    try {
      // Fetch file tree
      const treeRes = await fetch(`/api/repos/${repo.id}/tree`);
      if (treeRes.ok) {
        const treeData = await treeRes.json();
        setFileTree(treeData.tree || []);

        // Pick an interesting default file to display
        const firstFile = findFirstCodeFile(treeData.tree || []);
        if (firstFile) {
          loadFileContent(repo.id, firstFile.path);
        }
      }

      // Fetch chat messages
      const msgRes = await fetch(`/api/repos/${repo.id}/messages`);
      if (msgRes.ok) {
        const msgData = await msgRes.json();
        setMessages(msgData.messages || []);
      }
    } catch (e) {
      console.error('Error switching repository:', e);
    }
  };

  const findFirstCodeFile = (nodes) => {
    for (const node of nodes) {
      if (node.type === 'file') return node;
      if (node.children) {
        const found = findFirstCodeFile(node.children);
        if (found) return found;
      }
    }
    return null;
  };

  // 3. Load File Content for Code Inspector
  const loadFileContent = async (repoId, path, range = null) => {
    if (!repoId || !path) return;
    setIsFileLoading(true);
    setActiveFilePath(path);
    if (range) {
      setHighlightRange(range);
    } else {
      setHighlightRange(null);
    }

    try {
      const res = await fetch(`/api/repos/${repoId}/file?path=${encodeURIComponent(path)}`);
      if (res.ok) {
        const data = await res.json();
        setFileContent(data.content || '');
        setFileLineCount(data.line_count || 0);
      }
    } catch (e) {
      console.error('Error loading file content:', e);
    } finally {
      setIsFileLoading(false);
    }
  };

  // 4. Handle Citation Click from Chat
  const handleJumpToCitation = (citation) => {
    if (!activeRepo) return;
    const range = { start: citation.start_line, end: citation.end_line };
    loadFileContent(activeRepo.id, citation.file_path, range);
  };

  // 5. Send Chat Message & Handle SSE Stream
  const handleSendMessage = async (queryText) => {
    if (!activeRepo || isStreaming) return;

    // Optimistic user message update
    const userMsg = {
      id: `temp-${Date.now()}`,
      role: 'user',
      content: queryText,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setIsStreaming(true);
    setStreamingMessage('');
    setCurrentCitations([]);

    try {
      const response = await fetch(`/api/repos/${activeRepo.id}/chat/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: queryText }),
      });

      if (!response.ok) {
        throw new Error('Streaming failed');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      let accumulatedAnswer = '';
      let receivedCitations = [];

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        let currentEvent = 'message';
        for (const line of lines) {
          if (line.startsWith('event: ')) {
            currentEvent = line.slice(7).trim();
          } else if (line.startsWith('data: ')) {
            const rawData = line.slice(6).trim();
            try {
              const parsed = JSON.parse(rawData);
              if (currentEvent === 'citations') {
                receivedCitations = parsed;
                setCurrentCitations(parsed);
              } else if (currentEvent === 'token') {
                accumulatedAnswer += parsed.token;
                setStreamingMessage(accumulatedAnswer);
              } else if (currentEvent === 'done') {
                // Done event
              }
            } catch (err) {
              // ignore parse errors
            }
          }
        }
      }

      // Add final assistant message
      const assistantMsg = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: accumulatedAnswer,
        citations: receivedCitations,
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (e) {
      console.error('Chat stream error:', e);
      setMessages((prev) => [
        ...prev,
        {
          id: `error-${Date.now()}`,
          role: 'assistant',
          content: `Error: Unable to stream response (${e.message}). Please check backend connection.`,
        },
      ]);
    } finally {
      setIsStreaming(false);
      setStreamingMessage('');
      setCurrentCitations([]);
    }
  };

  const handleClearChat = async () => {
    if (!activeRepo || isStreaming) return;
    setMessages([]);
    setStreamingMessage('');
    setCurrentCitations([]);
    try {
      await fetch(`/api/repos/${activeRepo.id}/messages`, { method: 'DELETE' });
    } catch (e) {
      console.error('Failed to clear chat on backend:', e);
    }
  };

  return (
    <div className="app-container">
      {/* Top Header */}
      <Header
        repos={repos}
        activeRepo={activeRepo}
        onSelectRepo={(repo) => selectRepository(repo)}
        onOpenIngestModal={() => setIsIngestModalOpen(true)}
        onOpenSettingsModal={() => setIsSettingsModalOpen(true)}
        onOpenStitchModal={() => setIsStitchModalOpen(true)}
        settings={settings}
      />

      {/* 3-Panel IDE Workspace Grid */}
      <main className="workspace-grid">
        {/* Left Panel: File Explorer */}
        <FileExplorer
          activeRepo={activeRepo}
          fileTree={fileTree}
          onSelectFile={(path) => activeRepo && loadFileContent(activeRepo.id, path)}
          activeFilePath={activeFilePath}
        />

        {/* Center Panel: Streaming RAG Chat */}
        <ChatPanel
          activeRepo={activeRepo}
          messages={messages}
          streamingMessage={streamingMessage}
          currentCitations={currentCitations}
          isStreaming={isStreaming}
          onSendMessage={handleSendMessage}
          onJumpToCitation={handleJumpToCitation}
          onClearChat={handleClearChat}
        />

        {/* Right Panel: Code Inspector */}
        <CodeInspector
          filePath={activeFilePath}
          content={fileContent}
          language="text"
          lineCount={fileLineCount}
          highlightRange={highlightRange}
          isLoading={isFileLoading}
        />
      </main>

      {/* Modals */}
      <IngestModal
        isOpen={isIngestModalOpen}
        onClose={() => setIsIngestModalOpen(false)}
        onRepoIndexed={(newRepo) => {
          setRepos((prev) => [newRepo, ...prev.filter((r) => r.id !== newRepo.repo_id)]);
          selectRepository(newRepo);
        }}
      />

      <SettingsModal
        isOpen={isSettingsModalOpen}
        onClose={() => setIsSettingsModalOpen(false)}
        currentSettings={settings}
        onSettingsUpdated={(updated) => setSettings(updated)}
      />

      <StitchModal
        isOpen={isStitchModalOpen}
        onClose={() => setIsStitchModalOpen(false)}
      />
    </div>
  );
}
