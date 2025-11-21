import React, { useEffect, useRef, useState } from 'react';
import type { TelegramMessage } from '../types';
import { pollTelegram, sendTelegram } from '../api';

interface Props {
  chatId: string | null;
}

const TelegramChatPane: React.FC<Props> = ({ chatId }) => {
  const [messages, setMessages] = useState<TelegramMessage[]>([]);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const scrollRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!chatId) return;
    const interval = setInterval(async () => {
      try {
        const { messages: newMessages } = await pollTelegram(chatId);
        if (newMessages.length) {
          setMessages(prev => [...prev, ...newMessages]);
        }
      } catch (e) {
        // ignore polling errors
      }
    }, 1500);
    return () => clearInterval(interval);
  }, [chatId]);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!input.trim()) return;
    if (!chatId) {
      window.alert('Start or select a chat session from the left before sending.');
      return;
    }
    const text = input.trim();
    setSending(true);
    try {
      await sendTelegram(chatId, text);
      setMessages(prev => [
        ...prev,
        { sender: 'You', text, timestamp: Date.now() / 1000 },
      ]);
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
        TELEGRAM CHAT
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
        {messages.length ? (
          messages.map((msg, idx) => {
            const isUser = msg.sender === 'You';
            const align = isUser ? 'flex-end' : 'flex-start';
            const bg = isUser ? '#111827' : '#1d4ed8';
            const headerLabel = msg.sender || (isUser ? 'You' : 'Client');
            const time = new Date(msg.timestamp * 1000).toLocaleTimeString(undefined, {
              hour: '2-digit',
              minute: '2-digit',
            });
            return (
              <div
                key={idx}
                style={{ display: 'flex', justifyContent: align, margin: '0.25rem 0' }}
              >
                <div
                  style={{
                    maxWidth: '80%',
                    padding: '0.45rem 0.7rem',
                    borderRadius: 10,
                    background: bg,
                    fontSize: '0.95rem',
                    boxShadow: '0 0 0 1px rgba(15,23,42,0.4)',
                  }}
                >
                  <div
                    style={{
                      fontSize: '0.75rem',
                      color: isUser ? '#9ca3af' : '#e5e7eb',
                      marginBottom: '0.15rem',
                    }}
                  >
                    {headerLabel}
                  </div>
                  <div style={{ color: '#e5e7eb', marginBottom: '0.15rem' }}>{msg.text}</div>
                  <div
                    style={{
                      fontSize: '0.7rem',
                      color: '#9ca3af',
                      textAlign: isUser ? 'right' : 'left',
                    }}
                  >
                    {time}
                  </div>
                </div>
              </div>
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
        <input
          value={input}
          onChange={e => setInput(e.target.value)}
          placeholder="type to chat to client:"
          style={{
            flex: 1,
            padding: '0.45rem 0.6rem',
            borderRadius: 6,
            border: '1px solid #1f2937',
            background: '#020617',
            color: '#e5e7eb',
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

export default TelegramChatPane;
