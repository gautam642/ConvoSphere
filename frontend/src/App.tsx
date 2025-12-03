import React, { useEffect, useState } from 'react';
import Sidebar from './components/Sidebar';
import TelegramChatPane from './components/TelegramChatPane';
import GeminiChatPane from './components/GeminiChatPane';
import OsintPane from './components/OsintPane';
import type { Session, CreateSessionRequest } from './types';
import { createSession, getSession, listSessions } from './api';

const App: React.FC = () => {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [activeSession, setActiveSession] = useState<Session | null>(null);
  const [loadingSession, setLoadingSession] = useState(false);
  const [showOsint, setShowOsint] = useState(false);

  // Initial load of all sessions for the sidebar
  useEffect(() => {
    listSessions()
      .then(setSessions)
      .catch((err) => console.error("Failed to load sessions:", err));
  }, []);

  // Effect to handle WebSocket connection for real-time updates
  useEffect(() => {
    if (!activeSessionId) {
      setActiveSession(null);
      return;
    }

    // Fetch the session once initially when selected
    const fetchInitialSession = async () => {
      setLoadingSession(true);
      try {
        const sessionData = await getSession(activeSessionId);
        setActiveSession(sessionData);
      } catch (error) {
        console.error('Failed to fetch initial session:', error);
        setActiveSession(null);
      } finally {
        setLoadingSession(false);
      }
    };
    fetchInitialSession();

    const wsUrl = `ws://localhost:8000/ws/${activeSessionId}`;
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => console.log(`WebSocket connected for session: ${activeSessionId}`);
    ws.onmessage = (event) => {
      try {
        const updatedSession = JSON.parse(event.data);
        console.log('WebSocket message received:', {
          gemini: updatedSession.gemini,
          query_type: updatedSession.gemini?.query_type,
          has_response: !!updatedSession.gemini?.response
        });
        setActiveSession(updatedSession);
      } catch (error) {
        console.error("Failed to parse WebSocket message:", error);
      }
    };
    ws.onclose = () => console.log(`WebSocket disconnected for session: ${activeSessionId}`);
    ws.onerror = (error) => console.error("WebSocket error:", error);

    // Cleanup WebSocket on component unmount or when activeSessionId changes
    return () => ws.close();
  }, [activeSessionId]);

  async function handleCreateSession(data: CreateSessionRequest) {
    const newSession = await createSession(data);
    setSessions((prev) => [...prev, newSession]);
    setActiveSessionId(newSession.session_id);
  }

  function handleSelectSession(id: string) {
    setActiveSessionId(id);
  }

  return (
    <div style={{ display: 'flex', height: '100vh', background: '#0f1419', color: '#e5e7eb' }}>
      <Sidebar
        sessions={sessions}
        activeSessionId={activeSessionId}
        onSelectSession={handleSelectSession}
        onCreateSession={handleCreateSession}
      />
      <div
        style={{
          flex: 1,
          display: 'flex',
          justifyContent: 'center',
          padding: '1rem 1.5rem',
          boxSizing: 'border-box',
        }}
      >
        <div
          style={{
            display: 'flex',
            width: '100%',
            maxWidth: 1280,
            gap: '1.25rem',
          }}
        >
          <div style={{ flex: 1, minWidth: 0, display: 'flex', flexDirection: 'column' }}>
            {activeSessionId ? (
              <TelegramChatPane 
                sessionId={activeSessionId} 
                session={activeSession} 
                onShowOsint={() => setShowOsint(true)}
              />
            ) : (
              <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <div style={{ maxWidth: 460, width: '100%', padding: '2rem 1.75rem', borderRadius: 16, background: '#1a1d29', border: '1px solid #2a2f3d', boxShadow: '0 25px 60px rgba(0,0,0,0.5)' }}>
                  <div style={{ fontSize: '1.5rem', fontWeight: 700, marginBottom: '0.75rem', color: '#ffffff' }}>Welcome to ConvoSphere</div>
                  <div style={{ fontSize: '1rem', color: '#9ca3af', marginBottom: '1.5rem', lineHeight: 1.5 }}>Start a new chat session or pick a previous conversation from the list on the left.</div>
                </div>
              </div>
            )}
          </div>
          {activeSessionId && (
            <div style={{ width: 360, minWidth: 340 }}>
              {loadingSession && <div style={{ fontSize: '0.8rem', color: '#6b7280', marginBottom: '0.75rem', textAlign: 'center' }}>Loading Session...</div>}
              {showOsint ? (
                <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
                  <button
                    onClick={() => setShowOsint(false)}
                    style={{
                      padding: '0.5rem 1rem',
                      marginBottom: '0.75rem',
                      borderRadius: 8,
                      border: '1px solid #2a2f3d',
                      background: '#1a1d29',
                      color: '#0ea5e9',
                      fontSize: '0.85rem',
                      fontWeight: 600,
                      cursor: 'pointer',
                      textAlign: 'center',
                    }}
                  >
                    ← Back to Gemini Chat
                  </button>
                  <OsintPane session={activeSession} />
                </div>
              ) : (
                <GeminiChatPane session={activeSession} />
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default App;
