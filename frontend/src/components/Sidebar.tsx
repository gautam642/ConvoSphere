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
    <div style={{
      width: 280,
      background: '#020617',
      borderRight: '1px solid #1f2937',
      padding: '1rem 0.75rem',
      boxSizing: 'border-box',
      display: 'flex',
      flexDirection: 'column',
      gap: '1rem',
    }}>
      <div
        style={{
          padding: '0.75rem',
          borderRadius: 8,
          background: '#030712',
          border: '1px solid #1f2937',
        }}
      >
        <div style={{ fontSize: '1.1rem', fontWeight: 600, marginBottom: '0.75rem' }}>Session Setup</div>
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          <label style={{ fontSize: '0.8rem', display: 'flex', flexDirection: 'column', gap: '0.2rem', color: '#9ca3af' }}>
            phone no.:
            <input
              value={phone}
              onChange={e => setPhone(e.target.value)}
              style={{ width: '100%', marginTop: 2, padding: '0.25rem 0.4rem', borderRadius: 4, border: '1px solid #1f2937', background: '#020617', color: '#e5e7eb' }}
            />
          </label>
          <label style={{ fontSize: '0.8rem', display: 'flex', flexDirection: 'column', gap: '0.2rem', color: '#9ca3af' }}>
            name of client:
            <input
              value={name}
              onChange={e => setName(e.target.value)}
              style={{ width: '100%', marginTop: 2, padding: '0.25rem 0.4rem', borderRadius: 4, border: '1px solid #1f2937', background: '#020617', color: '#e5e7eb' }}
            />
          </label>
          <label style={{ fontSize: '0.8rem', display: 'flex', flexDirection: 'column', gap: '0.2rem', color: '#9ca3af' }}>
            client details aware of:
            <textarea
              value={details}
              onChange={e => setDetails(e.target.value)}
              rows={3}
              style={{ width: '100%', marginTop: 2, padding: '0.25rem 0.4rem', borderRadius: 4, border: '1px solid #1f2937', background: '#020617', color: '#e5e7eb', resize: 'vertical' }}
            />
          </label>
          <button
            type="submit"
            disabled={creating}
            style={{
              marginTop: 6,
              padding: '0.4rem 0.6rem',
              borderRadius: 6,
              border: 'none',
              background: '#3b82f6',
              color: '#e5e7eb',
              fontSize: '0.9rem',
              fontWeight: 500,
              cursor: 'pointer',
            }}
          >
            {creating ? 'Creating...' : 'Start Chat'}
          </button>
        </form>
      </div>

      <div
        style={{
          padding: '0.75rem',
          borderRadius: 8,
          background: '#030712',
          border: '1px solid #1f2937',
        }}
      >
        <div style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '0.5rem' }}>Chat Sessions</div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 4, maxHeight: '40vh', overflowY: 'auto' }}>
          {chats.map(chat => {
            const label = chat.metadata.client_name || chat.id;
            const active = chat.id === activeChatId;
            return (
              <button
                key={chat.id}
                onClick={() => onSelectChat(chat.id)}
                style={{
                  textAlign: 'left',
                  padding: '0.4rem 0.5rem',
                  borderRadius: 6,
                  border: 'none',
                  background: active ? '#1d4ed8' : '#020617',
                  color: active ? '#e5e7eb' : '#d1d5db',
                  fontSize: '0.85rem',
                  cursor: 'pointer',
                  borderLeft: active ? '3px solid #60a5fa' : '3px solid transparent',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 6,
                }}
              >
                <span style={{ fontSize: '0.65rem', color: active ? '#bfdbfe' : '#6b7280' }}>●</span>
                <span>{label}</span>
              </button>
            );
          })}
          {chats.length === 0 && (
            <div style={{ fontSize: '0.85rem', color: '#6b7280' }}>No chats yet. Create one above.</div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Sidebar;
