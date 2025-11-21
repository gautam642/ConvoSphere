import React, { useEffect, useRef, useState } from 'react';
import type { Chat } from '../types';
import { sendGemini } from '../api';

interface Props {
  chatId: string | null;
  chat: Chat | null;
  onChatUpdated: (chat: Chat) => void;
}

const GeminiChatPane: React.FC<Props> = ({ chatId, chat, onChatUpdated }) => {
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const scrollRef = useRef<HTMLDivElement | null>(null);

  const past = chat?.past ?? [];
  const generated = chat?.generated ?? [];

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [past.length, generated.length]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!input.trim()) return;
    if (!chatId) {
      window.alert('Start or select a chat session from the left before chatting with Convosphere.');
      return;
    }
    const text = input.trim();
    setSending(true);
    try {
      const { chat: updated } = await sendGemini(chatId, text);
      onChatUpdated(updated);
      setInput('');
    } finally {
      setSending(false);
    }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div
        style={{
          marginTop: '0.25rem',
          textAlign: 'center',
          fontWeight: 600,
          fontSize: '1.05rem',
          padding: '0.4rem 0',
          borderBottom: '2px solid #374151',
          letterSpacing: 0.5,
        }}
      >
        CONVOSPHERE
      </div>
      <div
        ref={scrollRef}
        style={{
          height: '60vh',
          overflowY: 'auto',
          padding: '0.5rem 0.75rem 0.5rem 0',
          border: '2px solid #374151',
          borderRadius: '0.5rem',
          marginTop: '0.5rem',
          background: '#020617',
        }}
      >
        {generated.length ? (
          generated.map((bot, i) => {
            const user = past[i] ?? '';
            return (
              <React.Fragment key={i}>
                <div style={{ display: 'flex', justifyContent: 'flex-end', margin: '0.25rem 0' }}>
                  <div
                    style={{
                      maxWidth: '80%',
                      padding: '0.45rem 0.7rem',
                      borderRadius: 10,
                      background: '#111827',
                      fontSize: '0.95rem',
                      boxShadow: '0 0 0 1px rgba(15,23,42,0.4)',
                    }}
                  >
                    <div
                      style={{
                        fontSize: '0.75rem',
                        color: '#9ca3af',
                        marginBottom: '0.15rem',
                      }}
                    >
                      You
                    </div>
                    <div style={{ color: '#e5e7eb' }}>{user}</div>
                  </div>
                </div>
                <div style={{ display: 'flex', justifyContent: 'flex-start', margin: '0.25rem 0' }}>
                  <div
                    style={{
                      maxWidth: '80%',
                      padding: '0.45rem 0.7rem',
                      borderRadius: 10,
                      background: '#4c1d95',
                      fontSize: '0.95rem',
                      boxShadow: '0 0 0 1px rgba(15,23,42,0.4)',
                    }}
                  >
                    <div
                      style={{
                        fontSize: '0.75rem',
                        color: '#e5e7eb',
                        marginBottom: '0.15rem',
                      }}
                    >
                      Convosphere
                    </div>
                    <div style={{ color: '#e5e7eb' }}>{bot}</div>
                  </div>
                </div>
              </React.Fragment>
            );
          })
        ) : (
          <div style={{ color: '#6b7280', fontSize: '0.9rem' }}>
            No messages yet. Start chatting below.
          </div>
        )}
      </div>
      <form
        onSubmit={handleSubmit}
        style={{
          marginTop: '0.75rem',
          padding: '0.6rem 0.65rem 0.65rem',
          borderTop: '2px solid #374151',
          background: '#020617',
          display: 'flex',
          gap: '0.6rem',
          alignItems: 'flex-end',
        }}
      >
        <textarea
          value={input}
          onChange={e => setInput(e.target.value)}
          placeholder="type to chat to gemini:"
          rows={3}
          style={{
            flex: 1,
            padding: '0.45rem 0.6rem',
            borderRadius: 6,
            border: '1px solid #1f2937',
            background: '#020617',
            color: '#e5e7eb',
            resize: 'vertical',
            fontSize: '0.95rem',
          }}
        />
        <button
          type="submit"
          disabled={sending}
          style={{
            padding: '0.45rem 0.9rem',
            borderRadius: 999,
            border: 'none',
            background: '#22c55e',
            color: '#022c22',
            fontWeight: 600,
            cursor: sending ? 'not-allowed' : 'pointer',
            opacity: sending ? 0.7 : 1,
            whiteSpace: 'nowrap',
          }}
        >
          Send
        </button>
      </form>
    </div>
  );
};

export default GeminiChatPane;
