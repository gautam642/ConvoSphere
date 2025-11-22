import React, { useState } from 'react';
import type { ChatSummary } from '../types';

interface Props {
  chats: ChatSummary[];
  activeChatId: string | null;
  onSelectChat: (id: string) => void;
  onCreateChat: (data: { client_phone: string; client_name: string; client_details: string }) => Promise<void>;
}

const Sidebar: React.FC<Props> = ({ chats, activeChatId, onSelectChat, onCreateChat }) => {
  const [phone, setPhone] = useState('');
  const [name, setName] = useState('');
  const [details, setDetails] = useState('');
  const [creating, setCreating] = useState(false);
  const [showNew, setShowNew] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setCreating(true);
    try {
      await onCreateChat({ client_phone: phone, client_name: name, client_details: details });
      setPhone('');
      setName('');
      setDetails('');
    } finally {
      setCreating(false);
    }
  }

  return (
    <div
      style={{
        width: 320,
        background: '#0d1117',
        borderRight: '1px solid #1e2530',
        padding: '1rem 0.5rem',
        boxSizing: 'border-box',
        display: 'flex',
        flexDirection: 'column',
        gap: '0.5rem',
      }}
    >
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '0.5rem 0.75rem',
          marginBottom: '0.5rem',
        }}
      >
        <div style={{ fontSize: '1.25rem', fontWeight: 700, color: '#ffffff' }}>Chats</div>
        <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
          <button
            type="button"
            style={{
              width: 32,
              height: 32,
              borderRadius: 8,
              border: 'none',
              background: '#1e2530',
              color: '#9ca3af',
              fontSize: '1rem',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            🔍
          </button>
          <button
            type="button"
            onClick={() => setShowNew((v) => !v)}
            style={{
              width: 32,
              height: 32,
              borderRadius: 8,
              border: 'none',
              background: showNew ? '#0ea5e9' : '#1e2530',
              color: '#ffffff',
              fontSize: '1.1rem',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            ✏️
          </button>
        </div>
      </div>

      {showNew && (
        <div
          style={{
            padding: '0.75rem',
            borderRadius: 12,
            background: '#1a1d29',
            border: '1px solid #2a2f3d',
            margin: '0 0.5rem 0.5rem',
          }}
        >
          <div style={{ fontSize: '0.95rem', fontWeight: 600, marginBottom: '0.5rem', color: '#ffffff' }}>Start a new chat</div>
          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            <label
              style={{
                fontSize: '0.8rem',
                display: 'flex',
                flexDirection: 'column',
                gap: '0.2rem',
                color: '#9ca3af',
              }}
            >
              phone no.:
              <input
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                style={{
                  width: '100%',
                  marginTop: 2,
                  padding: '0.5rem 0.65rem',
                  borderRadius: 8,
                  border: '1px solid #2a2f3d',
                  background: '#0d1117',
                  color: '#ffffff',
                }}
              />
            </label>
            <label
              style={{
                fontSize: '0.8rem',
                display: 'flex',
                flexDirection: 'column',
                gap: '0.2rem',
                color: '#9ca3af',
              }}
            >
              name of client:
              <input
                value={name}
                onChange={(e) => setName(e.target.value)}
                style={{
                  width: '100%',
                  marginTop: 2,
                  padding: '0.5rem 0.65rem',
                  borderRadius: 8,
                  border: '1px solid #2a2f3d',
                  background: '#0d1117',
                  color: '#ffffff',
                }}
              />
            </label>
            <label
              style={{
                fontSize: '0.8rem',
                display: 'flex',
                flexDirection: 'column',
                gap: '0.2rem',
                color: '#9ca3af',
              }}
            >
              client details aware of:
              <textarea
                value={details}
                onChange={(e) => setDetails(e.target.value)}
                rows={3}
                style={{
                  width: '100%',
                  marginTop: 2,
                  padding: '0.5rem 0.65rem',
                  borderRadius: 8,
                  border: '1px solid #2a2f3d',
                  background: '#0d1117',
                  color: '#ffffff',
                  resize: 'vertical',
                }}
              />
            </label>
            <button
              type="submit"
              disabled={creating}
              style={{
                marginTop: 8,
                padding: '0.5rem 0.8rem',
                borderRadius: 8,
                border: 'none',
                background: '#0ea5e9',
                color: '#ffffff',
                fontSize: '0.9rem',
                fontWeight: 600,
                cursor: 'pointer',
              }}
            >
              {creating ? 'Creating...' : 'Start Chat'}
            </button>
          </form>
        </div>
      )}

      <div
        style={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          minHeight: 0,
          overflowY: 'auto',
        }}
      >
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            gap: 2,
          }}
        >
          {chats.map((chat, idx) => {
            const label = chat.metadata.client_name || chat.id;
            const active = chat.id === activeChatId;
            const time = new Date(chat.metadata.start_timestamp || Date.now()).toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true });
            const preview = 'Last message preview...';
            return (
              <button
                key={chat.id}
                onClick={() => onSelectChat(chat.id)}
                style={{
                  textAlign: 'left',
                  padding: '0.75rem',
                  borderRadius: 0,
                  border: 'none',
                  background: active ? '#1a1d29' : 'transparent',
                  color: '#ffffff',
                  fontSize: '0.9rem',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'flex-start',
                  gap: 12,
                  position: 'relative',
                }}
              >
                <div
                  style={{
                    width: 48,
                    height: 48,
                    borderRadius: '50%',
                    background: `hsl(${idx * 60}, 65%, 55%)`,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '1rem',
                    fontWeight: 600,
                    color: '#ffffff',
                    flexShrink: 0,
                  }}
                >
                  {label.slice(0, 2).toUpperCase()}
                </div>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                    <div style={{ fontWeight: 600, fontSize: '0.95rem', color: '#ffffff' }}>{label}</div>
                    <div style={{ fontSize: '0.75rem', color: '#6b7280' }}>{time}</div>
                  </div>
                  <div
                    style={{
                      fontSize: '0.85rem',
                      color: '#9ca3af',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap',
                    }}
                  >
                    {preview}
                  </div>
                </div>
                {idx < 3 && (
                  <div
                    style={{
                      position: 'absolute',
                      top: 12,
                      right: 12,
                      background: '#0ea5e9',
                      color: '#ffffff',
                      borderRadius: '999px',
                      width: 20,
                      height: 20,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: '0.7rem',
                      fontWeight: 700,
                    }}
                  >
                    {idx + 1}
                  </div>
                )}
              </button>
            );
          })}
          {chats.length === 0 && (
            <div style={{ fontSize: '0.85rem', color: '#6b7280', padding: '1rem 0.75rem', textAlign: 'center' }}>
              No chats yet. Click the ✏️ button to start one.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Sidebar;
