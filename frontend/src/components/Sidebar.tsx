import React, { useState } from 'react';
import type { Session, CreateSessionRequest } from '../types';

interface Props {
  sessions: Session[];
  activeSessionId: string | null;
  onSelectSession: (id: string) => void;
  onCreateSession: (data: CreateSessionRequest) => Promise<void>;
}

const Sidebar: React.FC<Props> = ({ sessions, activeSessionId, onSelectSession, onCreateSession }) => {
  const [phone, setPhone] = useState('');
  const [name, setName] = useState('');
  const [context, setContext] = useState('');
  const [goal, setGoal] = useState('');
  const [ownerId, setOwnerId] = useState('sales_agent_001');
  const [creating, setCreating] = useState(false);
  const [showNew, setShowNew] = useState(true);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setCreating(true);
    try {
      await onCreateSession({
        name,
        phone,
        context,
        goal,
        owner_id: ownerId,
      });
      // Clear form after creation
      setPhone('');
      setName('');
      setContext('');
      setGoal('');
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
        <div style={{ fontSize: '1.25rem', fontWeight: 700, color: '#ffffff' }}>Sessions</div>
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
          <div style={{ fontSize: '0.95rem', fontWeight: 600, marginBottom: '0.5rem', color: '#ffffff' }}>Start New Session</div>
          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            <label style={{ fontSize: '0.85rem', display: 'flex', flexDirection: 'column', gap: '0.35rem', color: '#9ca3af' }}>
              Client Name:
              <input value={name} onChange={(e) => setName(e.target.value)} placeholder="John Doe" style={{ width: '100%', padding: '0.65rem 0.75rem', borderRadius: 8, border: '1px solid #2a2f3d', background: '#0d1117', color: '#ffffff', fontSize: '0.9rem', outline: 'none', boxSizing: 'border-box' }} />
            </label>
            <label style={{ fontSize: '0.85rem', display: 'flex', flexDirection: 'column', gap: '0.35rem', color: '#9ca3af' }}>
              Client Phone:
              <input value={phone} onChange={(e) => setPhone(e.target.value)} placeholder="+1234567890" style={{ width: '100%', padding: '0.65rem 0.75rem', borderRadius: 8, border: '1px solid #2a2f3d', background: '#0d1117', color: '#ffffff', fontSize: '0.9rem', outline: 'none', boxSizing: 'border-box' }} />
            </label>
            <label style={{ fontSize: '0.85rem', display: 'flex', flexDirection: 'column', gap: '0.35rem', color: '#9ca3af' }}>
              Context:
              <textarea value={context} onChange={(e) => setContext(e.target.value)} rows={3} placeholder="Background, interests..." style={{ width: '100%', padding: '0.65rem 0.75rem', borderRadius: 8, border: '1px solid #2a2f3d', background: '#0d1117', color: '#ffffff', fontSize: '0.9rem', resize: 'vertical', outline: 'none', fontFamily: 'inherit', boxSizing: 'border-box' }} />
            </label>
            <label style={{ fontSize: '0.85rem', display: 'flex', flexDirection: 'column', gap: '0.35rem', color: '#9ca3af' }}>
              Goal:
              <textarea value={goal} onChange={(e) => setGoal(e.target.value)} rows={2} placeholder="e.g., Book a demo" style={{ width: '100%', padding: '0.65rem 0.75rem', borderRadius: 8, border: '1px solid #2a2f3d', background: '#0d1117', color: '#ffffff', fontSize: '0.9rem', resize: 'vertical', outline: 'none', fontFamily: 'inherit', boxSizing: 'border-box' }} />
            </label>
            <label style={{ fontSize: '0.85rem', display: 'flex', flexDirection: 'column', gap: '0.35rem', color: '#9ca3af' }}>
              Agent ID:
              <input value={ownerId} onChange={(e) => setOwnerId(e.target.value)} style={{ width: '100%', padding: '0.65rem 0.75rem', borderRadius: 8, border: '1px solid #2a2f3d', background: '#0d1117', color: '#ffffff', fontSize: '0.9rem', outline: 'none', boxSizing: 'border-box' }} />
            </label>
            <button type="submit" disabled={creating} style={{ marginTop: '0.5rem', padding: '0.7rem 1rem', borderRadius: 8, border: 'none', background: '#0ea5e9', color: '#ffffff', fontSize: '0.95rem', fontWeight: 600, cursor: creating ? 'not-allowed' : 'pointer', opacity: creating ? 0.7 : 1 }}>
              {creating ? 'Creating...' : 'Start Session'}
            </button>
          </form>
        </div>
      )}

      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0, overflowY: 'auto' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          {sessions.map((session, idx) => {
            const label = session.customer.name || session.session_id;
            const active = session.session_id === activeSessionId;
            const time = new Date(session.created_at).toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true });
            const preview = session.messages.length > 0 ? session.messages[session.messages.length - 1].text : "No messages yet.";
            return (
              <button key={session.session_id} onClick={() => onSelectSession(session.session_id)} style={{ textAlign: 'left', padding: '0.75rem', borderRadius: 0, border: 'none', background: active ? '#1a1d29' : 'transparent', color: '#ffffff', fontSize: '0.9rem', cursor: 'pointer', display: 'flex', alignItems: 'flex-start', gap: 12, position: 'relative' }}>
                <div style={{ width: 48, height: 48, borderRadius: '50%', background: `hsl(${idx * 60}, 65%, 55%)`, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1rem', fontWeight: 600, color: '#ffffff', flexShrink: 0, }}>
                  {label.slice(0, 2).toUpperCase()}
                </div>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                    <div style={{ fontWeight: 600, fontSize: '0.95rem', color: '#ffffff' }}>{label}</div>
                    <div style={{ fontSize: '0.75rem', color: '#6b7280' }}>{time}</div>
                  </div>
                  <div style={{ fontSize: '0.85rem', color: '#9ca3af', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {preview}
                  </div>
                </div>
              </button>
            );
          })}
          {sessions.length === 0 && <div style={{ fontSize: '0.85rem', color: '#6b7280', padding: '1rem 0.75rem', textAlign: 'center' }}>No sessions yet. Click the ✏️ button to start one.</div>}
        </div>
      </div>
    </div>
  );
};

export default Sidebar;
