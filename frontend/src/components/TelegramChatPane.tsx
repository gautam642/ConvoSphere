import React, { useEffect, useRef, useState } from 'react';
import type { TelegramMessage, Chat } from '../types';
import { pollTelegram, sendTelegram } from '../api';

interface Props {
  chatId: string | null;
  chat: Chat | null;
}

const TelegramChatPane: React.FC<Props> = ({ chatId, chat }) => {
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
          <div
            style={{
              width: 40,
              height: 40,
              borderRadius: '50%',
              background: '#0ea5e9',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '1rem',
              fontWeight: 600,
              color: '#ffffff',
            }}
          >
            {(chat?.metadata?.client_name || 'CL').slice(0, 2).toUpperCase()}
          </div>
          <div>
            <div style={{ fontWeight: 600, fontSize: '1rem', color: '#ffffff' }}>
              {chat?.metadata?.client_name || 'Client'}
            </div>
            <div style={{ fontSize: '0.8rem', color: '#22c55e' }}>Online</div>
          </div>
        </div>
        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
          <button
            style={{
              width: 36,
              height: 36,
              borderRadius: 8,
              border: 'none',
              background: 'transparent',
              color: '#9ca3af',
              fontSize: '1.1rem',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            📞
          </button>
          <button
            style={{
              width: 36,
              height: 36,
              borderRadius: 8,
              border: 'none',
              background: 'transparent',
              color: '#9ca3af',
              fontSize: '1.1rem',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            🔍
          </button>
          <button
            style={{
              width: 36,
              height: 36,
              borderRadius: 8,
              border: 'none',
              background: 'transparent',
              color: '#9ca3af',
              fontSize: '1.1rem',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            ⋮
          </button>
          <button
            style={{
              padding: '0.4rem 0.75rem',
              borderRadius: 8,
              border: 'none',
              background: '#0ea5e9',
              color: '#ffffff',
              fontSize: '0.8rem',
              fontWeight: 600,
              cursor: 'pointer',
            }}
          >
            Info
          </button>
        </div>
      </div>
      {/* Date Separator */}
      <div style={{ textAlign: 'center', padding: '1rem 0', background: '#1a1d29' }}>
        <span
          style={{
            fontSize: '0.75rem',
            color: '#6b7280',
            background: '#0f1419',
            padding: '0.35rem 0.75rem',
            borderRadius: 999,
          }}
        >
          Thursday, 27 September
        </span>
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
        {messages.length ? (
          messages.map((msg, idx) => {
            const isUser = msg.sender === 'You';
            const time = new Date(msg.timestamp * 1000).toLocaleTimeString('en-US', {
              hour: 'numeric',
              minute: '2-digit',
              hour12: true,
            });
            
            // Check if this is the last message in a consecutive group from the same sender
            const isLastInGroup = idx === messages.length - 1 || messages[idx + 1].sender !== msg.sender;
            
            return (
              <div
                key={idx}
                style={{
                  display: 'flex',
                  justifyContent: isUser ? 'flex-end' : 'flex-start',
                  marginBottom: isLastInGroup ? '1rem' : '0.25rem',
                  gap: 10,
                }}
              >
                {!isUser && isLastInGroup && (
                  <div
                    style={{
                      width: 32,
                      height: 32,
                      borderRadius: '50%',
                      background: '#0ea5e9',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: '0.75rem',
                      fontWeight: 600,
                      color: '#ffffff',
                      flexShrink: 0,
                    }}
                  >
                    {(chat?.metadata?.client_name || 'CL').slice(0, 2).toUpperCase()}
                  </div>
                )}
                {!isUser && !isLastInGroup && (
                  <div style={{ width: 32, flexShrink: 0 }} />
                )}
                <div style={{ maxWidth: '65%' }}>
                  <div
                    style={{
                      padding: '0.65rem 0.85rem',
                      borderRadius: 12,
                      background: isUser ? '#0ea5e9' : '#e5e7eb',
                      color: isUser ? '#ffffff' : '#1f2937',
                      fontSize: '0.95rem',
                      lineHeight: 1.5,
                      wordWrap: 'break-word',
                    }}
                  >
                    {msg.text}
                  </div>
                  {isLastInGroup && (
                    <div
                      style={{
                        fontSize: '0.7rem',
                        color: '#6b7280',
                        marginTop: 4,
                        textAlign: isUser ? 'right' : 'left',
                      }}
                    >
                      {time}
                    </div>
                  )}
                </div>
                {isUser && !isLastInGroup && (
                  <div style={{ width: 32, flexShrink: 0 }} />
                )}
                {isUser && isLastInGroup && (
                  <div
                    style={{
                      width: 32,
                      height: 32,
                      borderRadius: '50%',
                      background: '#6366f1',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: '0.75rem',
                      fontWeight: 600,
                      color: '#ffffff',
                      flexShrink: 0,
                    }}
                  >
                    YO
                  </div>
                )}
              </div>
            );
          })
        ) : (
          <div style={{ color: '#6b7280', fontSize: '0.9rem', textAlign: 'center', padding: '2rem' }}>
            No messages yet. Start chatting below.
          </div>
        )}
      </div>
      {/* Input Area */}
      <form
        onSubmit={handleSubmit}
        style={{
          padding: '1rem 1.25rem',
          borderTop: '1px solid #2a2f3d',
          background: '#1a1d29',
          display: 'flex',
          gap: '0.75rem',
          alignItems: 'center',
          borderRadius: '0 0 12px 12px',
        }}
      >
        <button
          type="button"
          style={{
            width: 36,
            height: 36,
            borderRadius: '50%',
            border: 'none',
            background: 'transparent',
            color: '#9ca3af',
            fontSize: '1.2rem',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          😊
        </button>
        <input
          value={input}
          onChange={e => setInput(e.target.value)}
          placeholder="Type a message"
          style={{
            flex: 1,
            padding: '0.65rem 1rem',
            borderRadius: 999,
            border: '1px solid #2a2f3d',
            background: '#0f1419',
            color: '#e5e7eb',
            fontSize: '0.9rem',
            outline: 'none',
          }}
        />
        <button
          type="button"
          style={{
            width: 36,
            height: 36,
            borderRadius: '50%',
            border: 'none',
            background: 'transparent',
            color: '#9ca3af',
            fontSize: '1.2rem',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          📎
        </button>
        <button
          type="submit"
          disabled={sending}
          style={{
            width: 36,
            height: 36,
            borderRadius: '50%',
            border: 'none',
            background: '#0ea5e9',
            color: '#ffffff',
            fontSize: '1.2rem',
            cursor: sending ? 'not-allowed' : 'pointer',
            opacity: sending ? 0.7 : 1,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          ➤
        </button>
      </form>
    </div>
  );
};

export default TelegramChatPane;
