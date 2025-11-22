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
  const [isTyping, setIsTyping] = useState(false);
  const scrollRef = useRef<HTMLDivElement | null>(null);

  const past = chat?.past ?? [];
  const generated = chat?.generated ?? [];

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [past.length, generated.length]);

  useEffect(() => {
    setIsTyping(input.length > 0);
  }, [input]);

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
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        background: '#1a1d29',
        borderRadius: 12,
        overflow: 'hidden',
      }}
    >
      <div
        style={{
          padding: '1rem 1.25rem',
          borderBottom: '1px solid #2a2f3d',
          background: '#1a1d29',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div
            style={{
              width: 36,
              height: 36,
              borderRadius: '50%',
              background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '1.2rem',
            }}
          >
            🤖
          </div>
          <div>
            <div style={{ fontWeight: 700, fontSize: '1rem', color: '#ffffff' }}>ConvoSphere</div>
            <div style={{ fontSize: '0.75rem', color: '#22c55e' }}>● AI Assistant</div>
          </div>
        </div>
        <div
          style={{
            fontSize: '0.7rem',
            color: '#9ca3af',
            background: '#0f1419',
            padding: '0.3rem 0.6rem',
            borderRadius: 999,
          }}
        >
          Smart Assist
        </div>
      </div>

      <div
        ref={scrollRef}
        style={{
          flex: 1,
          overflowY: 'auto',
          padding: '1.25rem',
          background: '#1a1d29',
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        {!isTyping && past.length === 0 && (
          <div
            style={{
              flex: 1,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              textAlign: 'center',
              padding: '2rem 1rem',
            }}
          >
            <div>
              <div style={{ fontSize: '2.5rem', marginBottom: '1rem' }}>
                🤖
              </div>
              <div
                style={{
                  fontSize: '1.1rem',
                  fontWeight: 600,
                  color: '#ffffff',
                  marginBottom: '0.5rem',
                  lineHeight: 1.4,
                }}
              >
                Your Personal Context-Aware
                <br />
                Smart AI Sales Chat Assistant
              </div>
              <div
                style={{
                  fontSize: '0.85rem',
                  color: '#9ca3af',
                  lineHeight: 1.6,
                  maxWidth: 280,
                  margin: '0 auto',
                }}
              >
                I analyze your conversations in real-time and provide smart suggestions, triggers, and insights to help you close deals faster.
              </div>
            </div>
          </div>
        )}

        {(isTyping || past.length > 0) && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div
              style={{
                padding: '1rem',
                borderRadius: 12,
                background: 'linear-gradient(135deg, rgba(99,102,241,0.1), rgba(139,92,246,0.1))',
                border: '1px solid rgba(99,102,241,0.3)',
              }}
            >
              <div style={{ fontSize: '0.8rem', fontWeight: 700, color: '#a5b4fc', marginBottom: '0.5rem' }}>
                💡 SMART SUGGESTIONS
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                <button
                  style={{
                    padding: '0.6rem 0.75rem',
                    borderRadius: 8,
                    border: '1px solid #2a2f3d',
                    background: '#0f1419',
                    color: '#e5e7eb',
                    fontSize: '0.85rem',
                    textAlign: 'left',
                    cursor: 'pointer',
                  }}
                >
                  "Can you share the updated specs for last task?"
                </button>
                <button
                  style={{
                    padding: '0.6rem 0.75rem',
                    borderRadius: 8,
                    border: '1px solid #2a2f3d',
                    background: '#0f1419',
                    color: '#e5e7eb',
                    fontSize: '0.85rem',
                    textAlign: 'left',
                    cursor: 'pointer',
                  }}
                >
                  "Yeah done! When can we schedule a follow-up?"
                </button>
              </div>
            </div>

            <div
              style={{
                padding: '1rem',
                borderRadius: 12,
                background: 'rgba(14,165,233,0.1)',
                border: '1px solid rgba(14,165,233,0.3)',
              }}
            >
              <div style={{ fontSize: '0.8rem', fontWeight: 700, color: '#7dd3fc', marginBottom: '0.5rem' }}>
                �� LIVE INSIGHTS
              </div>
              <div style={{ fontSize: '0.85rem', color: '#e5e7eb', lineHeight: 1.5 }}>
                <div style={{ marginBottom: '0.5rem' }}>
                  <span style={{ color: '#22c55e', fontWeight: 600 }}>✓</span> Client is engaged
                </div>
                <div style={{ marginBottom: '0.5rem' }}>
                  <span style={{ color: '#f59e0b', fontWeight: 600 }}>⚠</span> Mentioned pricing concerns
                </div>
                <div>
                  <span style={{ color: '#0ea5e9', fontWeight: 600 }}>→</span> Suggest value proposition
                </div>
              </div>
            </div>

            {past.length > 0 && (
              <div style={{ marginTop: '1rem' }}>
                <div
                  style={{
                    fontSize: '0.75rem',
                    fontWeight: 700,
                    color: '#6b7280',
                    textTransform: 'uppercase',
                    letterSpacing: 0.5,
                    marginBottom: '0.75rem',
                  }}
                >
                  Conversation History
                </div>
                {generated.map((bot, i) => {
                  const user = past[i] ?? '';
                  return (
                    <div key={i} style={{ marginBottom: '1rem' }}>
                      {user && (
                        <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '0.5rem' }}>
                          <div
                            style={{
                              maxWidth: '85%',
                              padding: '0.6rem 0.8rem',
                              borderRadius: 12,
                              background: '#6366f1',
                              color: '#ffffff',
                              fontSize: '0.85rem',
                              lineHeight: 1.5,
                            }}
                          >
                            {user}
                          </div>
                        </div>
                      )}
                      <div style={{ display: 'flex', justifyContent: 'flex-start' }}>
                        <div
                          style={{
                            maxWidth: '85%',
                            padding: '0.6rem 0.8rem',
                            borderRadius: 12,
                            background: '#0f1419',
                            border: '1px solid #2a2f3d',
                            color: '#e5e7eb',
                            fontSize: '0.85rem',
                            lineHeight: 1.5,
                          }}
                        >
                          <div style={{ fontSize: '0.7rem', color: '#9ca3af', marginBottom: '0.25rem' }}>🤖 ConvoSphere</div>
                          {bot}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}
      </div>

      <form
        onSubmit={handleSubmit}
        style={{
          padding: '1rem 1.25rem',
          borderTop: '1px solid #2a2f3d',
          background: '#1a1d29',
          display: 'flex',
          gap: '0.75rem',
          alignItems: 'center',
        }}
      >
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask ConvoSphere for help..."
          rows={2}
          style={{
            flex: 1,
            padding: '0.65rem 1rem',
            borderRadius: 12,
            border: '1px solid #2a2f3d',
            background: '#0f1419',
            color: '#e5e7eb',
            fontSize: '0.9rem',
            outline: 'none',
            resize: 'none',
            fontFamily: 'inherit',
          }}
        />
        <button
          type="submit"
          disabled={sending || !input.trim()}
          style={{
            width: 40,
            height: 40,
            borderRadius: '50%',
            border: 'none',
            background: input.trim() ? '#6366f1' : '#2a2f3d',
            color: '#ffffff',
            fontSize: '1.2rem',
            cursor: sending || !input.trim() ? 'not-allowed' : 'pointer',
            opacity: sending ? 0.7 : 1,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            flexShrink: 0,
          }}
        >
          ➤
        </button>
      </form>
    </div>
  );
};

export default GeminiChatPane;
