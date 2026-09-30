import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import './App.css';

function App() {
  const [activeTab, setActiveTab] = useState('chat');
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [activeChatId, setActiveChatId] = useState(1);
  const [searchFilter, setSearchFilter] = useState('');
  
  const [chats, setChats] = useState([
    { id: 1, title: 'Enterprise RAG Architecture', history: [] },
    { id: 2, title: 'Multi-Agent Workflow Tuning', history: [] },
    { id: 3, title: 'Local LLM Deployment', history: [] },
  ]);

  const [selectedFile, setSelectedFile] = useState(null);
  const [uploadStatus, setUploadStatus] = useState('');
  const chatEndRef = useRef(null);

  const currentChat = chats.find(c => c.id === activeChatId) || chats[0];

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [currentChat.history, loading]);

  const handleFileUpload = async () => {
    if (!selectedFile) return;
    const formData = new FormData();
    formData.append('file', selectedFile);

    setUploadStatus('Uploading...');
    try {
      const res = await axios.post('http://127.0.0.1:8000/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setUploadStatus(res.data.message || 'Indexed!');
      setSelectedFile(null);
      setTimeout(() => setUploadStatus(''), 3000);
    } catch (err) {
      console.error(err);
      setUploadStatus('Failed');
      setTimeout(() => setUploadStatus(''), 3000);
    }
  };

  const handleNewChat = () => {
    const newId = Date.now();
    const newChatObj = { id: newId, title: 'New Conversation', history: [] };
    setChats([newChatObj, ...chats]);
    setActiveChatId(newId);
  };

  const handleSendMessage = async (textToSend) => {
    const text = textToSend || query;
    if (!text.trim()) return;

    setQuery('');
    setLoading(true);

    const updatedHistory = [...currentChat.history, { sender: 'user', text }];
    setChats(chats.map(c => c.id === activeChatId ? { 
      ...c, 
      history: updatedHistory,
      title: c.history.length === 0 ? (text.slice(0, 28) + '...') : c.title 
    } : c));

    try {
      const response = await axios.post('http://127.0.0.1:8000/ask', { query: text });
      const botAnswer = response.data.answer;

      const finalHistory = [...updatedHistory, { sender: 'bot', text: botAnswer }];
      setChats(prevChats => prevChats.map(c => c.id === activeChatId ? { ...c, history: finalHistory } : c));
    } catch (err) {
      console.error(err);
      const errHistory = [...updatedHistory, { sender: 'bot', text: 'Error connecting to local server backend.' }];
      setChats(prevChats => prevChats.map(c => c.id === activeChatId ? { ...c, history: errHistory } : c));
    } finally {
      setLoading(false);
    }
  };

  const filteredChats = chats.filter(c => c.title.toLowerCase().includes(searchFilter.toLowerCase()));

  return (
    <div className="app-layout">
      {/* Cognify Sidebar */}
      <aside className="cognify-sidebar">
        <div className="sidebar-top-header">
          <div className="sidebar-brand">
            <div className="cognify-logo-icon">C</div>
            <span>Cognify</span>
          </div>
        </div>

        {/* Top Tabs */}
        <div className="sidebar-tabs">
          <button 
            className={`tab-btn ${activeTab === 'chat' ? 'active' : ''}`}
            onClick={() => setActiveTab('chat')}
          >
            Chat
          </button>
          <button 
            className={`tab-btn ${activeTab === 'spark' ? 'active' : ''}`}
            onClick={() => setActiveTab('spark')}
          >
            Spark <span className="tab-badge">PRO</span>
          </button>
        </div>

        {/* New Chat Button */}
        <button onClick={handleNewChat} className="nav-item" style={{ fontWeight: 500 }}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M5 12h14"/><path d="M12 5v14"/></svg>
          New chat
        </button>

        {/* Search Chats */}
        <div className="nav-item" style={{ cursor: 'default' }}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>
          <input 
            type="text" 
            placeholder="Search chats..." 
            value={searchFilter}
            onChange={(e) => setSearchFilter(e.target.value)}
            className="search-input-box"
          />
        </div>

        {/* Knowledge Base Ingestion Widget */}
        <div className="sidebar-kb-box">
          <span>📚 Knowledge Base (KB)</span>
          <div className="kb-file-wrapper">
            <input 
              type="file" 
              accept=".txt,.md" 
              onChange={(e) => setSelectedFile(e.target.files[0])}
              className="kb-file-input"
            />
            {selectedFile && (
              <button onClick={handleFileUpload} className="kb-upload-btn">
                Index Document
              </button>
            )}
          </div>
          {uploadStatus && <span style={{ color: '#a8c7fa', fontSize: '0.7rem' }}>{uploadStatus}</span>}
        </div>

        {/* Recent Section */}
        <div className="section-header-label">Recent Conversations</div>
        <div className="recent-chats-scroll">
          {filteredChats.map((chat) => (
            <button
              key={chat.id}
              onClick={() => setActiveChatId(chat.id)}
              className={`nav-item ${chat.id === activeChatId ? 'active-chat' : ''}`}
              style={{ width: '100%', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
              <span style={{ overflow: 'hidden', textOverflow: 'ellipsis' }}>{chat.title}</span>
            </button>
          ))}
        </div>
      </aside>

      {/* Main Workspace Stage */}
      <main className="main-stage">
        <header className="top-navbar">
          <div className="model-selector-pill">
            <span>Cognify</span>
            <span style={{ color: 'var(--text-muted)', fontSize: '0.85rem', fontWeight: 400 }}>▾ Llama 3.2 (Local)</span>
          </div>
          <div style={{ width: '32px', height: '32px', borderRadius: '50%', background: '#3b82f6', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 'bold', fontSize: '0.85rem', color: '#fff' }}>
            A
          </div>
        </header>

        <div className="chat-viewport">
          {currentChat.history.length === 0 ? (
            <div className="empty-state-greeting">
              Hello, Abhishek
            </div>
          ) : (
            <div className="message-stream">
              {currentChat.history.map((msg, index) => (
                <div key={index} className={`chat-row ${msg.sender}`}>
                  {msg.sender === 'bot' && (
                    <div className="bot-avatar">
                      C
                    </div>
                  )}
                  <div className="row-body">
                    {msg.text}
                  </div>
                </div>
              ))}

              {loading && (
                <div className="chat-row bot">
                  <div className="bot-avatar">
                    C
                  </div>
                  <div className="row-body">
                    <div className="thinking-indicator">
                      <div className="spinner-dot" style={{ animationDelay: '0s' }}></div>
                      <div className="spinner-dot" style={{ animationDelay: '0.2s' }}></div>
                      <div className="spinner-dot" style={{ animationDelay: '0.3s' }}></div>
                      <span>Cognify is thinking...</span>
                    </div>
                  </div>
                </div>
              )}
              <div ref={chatEndRef} />
            </div>
          )}
        </div>

        {/* Input Dock */}
        <div className="input-dock">
          <form 
            onSubmit={(e) => { e.preventDefault(); handleSendMessage(); }} 
            className="input-container"
          >
            <textarea
              rows={1}
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSendMessage();
                }
              }}
              placeholder="Ask Cognify anything..."
              className="chat-textarea"
            />
            <button type="submit" disabled={loading || !query.trim()} className="send-btn">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><path d="m5 12 7-7 7 7"/><path d="M12 19V5"/></svg>
            </button>
          </form>
        </div>
      </main>
    </div>
  );
}

export default App;