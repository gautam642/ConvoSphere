import React, { useEffect, useRef, useState } from 'react';
import type { Session, Message } from '../types';
import { sendMessage } from '../api';

interface Props {
  sessionId: string | null;
  session: Session | null;
  onShowOsint?: () => void;
}

const TelegramChatPane: React.FC<Props> = ({ sessionId, session, onShowOsint }) => {
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const scrollRef = useRef<HTMLDivElement | null>(null);

  const messages = session?.messages ?? [];

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages.length]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!input.trim() || !sessionId) return;
    setSending(true);
    try {
      await sendMessage(sessionId, input.trim());
      setInput('');
    } finally {
      setSending(false);
    }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', background: '#1a1d29', borderRadius: 12 }}>
      {/* Top Header Bar */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '1rem 1.25rem',
          borderBottom: '1px solid #2a2f3d',
          background: '#1a1d29',
          borderRadius: '12px 12px 0 0',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{ width: 40, height: 40, borderRadius: '50%', background: '#0ea5e9', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1rem', fontWeight: 600, color: '#ffffff' }}>
            {(session?.customer?.name || 'C').slice(0, 2).toUpperCase()}
          </div>
          <div>
            <div style={{ fontWeight: 600, fontSize: '1rem', color: '#ffffff' }}>
              {session?.customer?.name || 'Client'}
            </div>
            <div style={{ fontSize: '0.8rem', color: '#22c55e' }}>● Online</div>
          </div>
        </div>
        {/* OSINT Profile Button */}
        <button
          onClick={onShowOsint}
          style={{
            padding: '0.5rem 1rem',
            borderRadius: 8,
            border: '1px solid #2a2f3d',
            background: '#0ea5e9',
            color: '#ffffff',
            fontSize: '0.85rem',
            fontWeight: 600,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            transition: 'all 0.2s',
          }}
          onMouseEnter={(e) => e.currentTarget.style.background = '#0284c7'}
          onMouseLeave={(e) => e.currentTarget.style.background = '#0ea5e9'}
        >
          <span style={{ fontSize: '1rem' }}>ℹ️</span>
          OSINT Profile
        </button>
      </div>

      {/* Messages Area */}
      <div
        ref={scrollRef}
        style={{
          flex: 1,
          overflowY: 'auto',
          padding: '1rem 1.25rem',
          background: '#1a1d29',
        }}
      >
        {messages.map((msg, idx) => {
          const isAgent = msg.sender === 'agent';
          const time = new Date(msg.timestamp).toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true });
          const isLastInGroup = idx === messages.length - 1 || messages[idx + 1].sender !== msg.sender;
          
          return (
            <div key={msg.message_id} style={{ display: 'flex', justifyContent: isAgent ? 'flex-end' : 'flex-start', marginBottom: isLastInGroup ? '1rem' : '0.25rem', gap: 10 }}>
              {!isAgent && isLastInGroup && (
                <div style={{ width: 32, height: 32, borderRadius: '50%', background: '#0ea5e9', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.75rem', fontWeight: 600, color: '#ffffff', flexShrink: 0 }}>
                  {(session?.customer.name || 'C').slice(0, 2).toUpperCase()}
                </div>
              )}
              {!isAgent && !isLastInGroup && <div style={{ width: 32, flexShrink: 0 }} />}
              <div style={{ maxWidth: '65%' }}>
                <div style={{ padding: '0.65rem 0.85rem', borderRadius: 12, background: isAgent ? '#6366f1' : '#e5e7eb', color: isAgent ? '#ffffff' : '#1f2937', fontSize: '0.95rem', lineHeight: 1.5, wordWrap: 'break-word' }}>
                  {msg.text}
                </div>
                {isLastInGroup && (
                  <div style={{ fontSize: '0.7rem', color: '#6b7280', marginTop: 4, textAlign: isAgent ? 'right' : 'left' }}>
                    {time}
                  </div>
                )}
              </div>
              {isAgent && isLastInGroup && (
                <div style={{ width: 32, height: 32, borderRadius: '50%', background: '#6366f1', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.75rem', fontWeight: 600, color: '#ffffff', flexShrink: 0 }}>
                  YOU
                </div>
              )}
              {isAgent && !isLastInGroup && <div style={{ width: 32, flexShrink: 0 }} />}
            </div>
          );
        })}
        {messages.length === 0 && <div style={{ color: '#6b7280', fontSize: '0.9rem', textAlign: 'center', padding: '2rem' }}>No messages yet. Start chatting below.</div>}
      </div>

      {/* Input Area */}
      <form onSubmit={handleSubmit} style={{ padding: '1rem 1.25rem', borderTop: '1px solid #2a2f3d', background: '#1a1d29', display: 'flex', gap: '0.75rem', alignItems: 'center', borderRadius: '0 0 12px 12px' }}>
        <input value={input} onChange={e => setInput(e.target.value)} placeholder="Type a message" style={{ flex: 1, padding: '0.65rem 1rem', borderRadius: 999, border: '1px solid #2a2f3d', background: '#0f1419', color: '#e5e7eb', fontSize: '0.9rem', outline: 'none' }} disabled={!sessionId} />
        <button type="submit" disabled={sending || !sessionId} style={{ width: 36, height: 36, borderRadius: '50%', border: 'none', background: '#0ea5e9', color: '#ffffff', fontSize: '1.2rem', cursor: (sending || !sessionId) ? 'not-allowed' : 'pointer', opacity: (sending || !sessionId) ? 0.7 : 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          ➤
        </button>
      </form>
    </div>
  );
};

export default TelegramChatPane;
