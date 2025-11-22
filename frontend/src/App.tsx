import React, { useEffect, useState } from 'react';
import Sidebar from './components/Sidebar';
import TelegramChatPane from './components/TelegramChatPane';
import GeminiChatPane from './components/GeminiChatPane';
import type { Chat, ChatSummary } from './types';
import { createChat, getChat, listChats } from './api';

const App: React.FC = () => {
  const [chats, setChats] = useState<ChatSummary[]>([]);
  const [activeChatId, setActiveChatId] = useState<string | null>(null);
  const [activeChat, setActiveChat] = useState<Chat | null>(null);
  const [loadingChat, setLoadingChat] = useState(false);

  useEffect(() => {
    listChats()
      .then(setChats)
      .catch(() => {
        // ignore initial load errors
      });
  }, []);

  useEffect(() => {
    if (!activeChatId) return;
    setLoadingChat(true);
    getChat(activeChatId)
      .then((res) => setActiveChat(res.chat))
      .finally(() => setLoadingChat(false));
  }, [activeChatId]);

  async function handleCreateChat(data: { client_phone: string; client_name: string; client_details: string }) {
    const res = await createChat(data);
    setChats((prev) => [...prev, { id: res.id, metadata: res.chat.metadata }]);
    setActiveChatId(res.id);
    setActiveChat(res.chat);
  }

  function handleSelectChat(id: string) {
    setActiveChatId(id);
  }

  return (
    <div style={{ display: 'flex', height: '100vh', background: '#0f1419', color: '#e5e7eb' }}>
      <Sidebar
        chats={chats}
        activeChatId={activeChatId}
        onSelectChat={handleSelectChat}
        onCreateChat={handleCreateChat}
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
            {activeChatId ? (
              <TelegramChatPane chatId={activeChatId} chat={activeChat} />
            ) : (
              <div
                style={{
                  flex: 1,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                <div
                  style={{
                    maxWidth: 460,
                    width: '100%',
                    padding: '2rem 1.75rem',
                    borderRadius: 16,
                    background: '#1a1d29',
                    border: '1px solid #2a2f3d',
                    boxShadow: '0 25px 60px rgba(0,0,0,0.5)',
                  }}
                >
                  <div style={{ fontSize: '1.5rem', fontWeight: 700, marginBottom: '0.75rem', color: '#ffffff' }}>
                    Welcome to ConvoSphere
                  </div>
                  <div style={{ fontSize: '1rem', color: '#9ca3af', marginBottom: '1.5rem', lineHeight: 1.5 }}>
                    Start a new chat session or pick a previous conversation from the list on the left.
                  </div>
                  <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
                    <div
                      style={{
                        flex: 1,
                        minWidth: 120,
                        padding: '0.65rem 0.85rem',
                        borderRadius: 10,
                        border: '1px dashed #0ea5e9',
                        background: 'linear-gradient(135deg, rgba(14,165,233,0.15), rgba(8,47,73,0.3))',
                        fontSize: '0.9rem',
                        color: '#7dd3fc',
                      }}
                    >
                      Use the <span style={{ fontWeight: 600 }}>New Chat</span> button in the left panel to create a
                      fresh session.
                    </div>
                    <div
                      style={{
                        flex: 1,
                        minWidth: 120,
                        padding: '0.65rem 0.85rem',
                        borderRadius: 10,
                        border: '1px solid #2a2f3d',
                        background: '#0d1117',
                        fontSize: '0.9rem',
                        color: '#9ca3af',
                      }}
                    >
                      Or click any existing conversation in the <span style={{ fontWeight: 600 }}>Chats</span> list to
                      continue where you left off.
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
          {activeChatId && (
            <div style={{ width: 360, minWidth: 340 }}>
              {loadingChat && (
                <div
                  style={{
                    fontSize: '0.8rem',
                    color: '#6b7280',
                    marginBottom: '0.75rem',
                    textAlign: 'center',
                  }}
                >
                  Loading ConvoSphere...
                </div>
              )}
              <GeminiChatPane chatId={activeChatId} chat={activeChat} onChatUpdated={setActiveChat} />
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default App;
