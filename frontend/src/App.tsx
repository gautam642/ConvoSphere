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
    <div style={{ display: 'flex', height: '100vh', background: '#020617', color: '#e5e7eb' }}>
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
            maxWidth: 1180,
            gap: '1rem',
          }}
        >
          <div style={{ flex: 1, minWidth: 0 }}>
            <TelegramChatPane chatId={activeChatId} />
          </div>
          <div
            style={{
              width: 2,
              background: '#374151',
              alignSelf: 'stretch',
              position: 'relative',
              margin: '0 0.25rem',
            }}
          >
            <div
              style={{
                position: 'absolute',
                top: '-0.6rem',
                left: '50%',
                transform: 'translateX(-50%)',
                fontSize: '0.7rem',
                color: '#6b7280',
                padding: '0 0.25rem',
                background: '#020617',
              }}
            >
              ASSIST
            </div>
          </div>
          <div style={{ flex: 1, minWidth: 0 }}>
            {loadingChat && <div style={{ fontSize: '0.9rem', color: '#9ca3af' }}>Loading chat...</div>}
            <GeminiChatPane
              chatId={activeChatId}
              chat={activeChat}
              onChatUpdated={setActiveChat}
            />
          </div>
        </div>
      </div>
    </div>
  );
};

export default App;
