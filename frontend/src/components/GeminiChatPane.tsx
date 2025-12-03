import React, { useState, useEffect, useRef } from 'react';
import type { Session, LocalLLMAnalysis, GeminiAnalysis } from '../types';
import { triggerGemini } from '../api';

interface Props {
  session: Session | null;
}

const IntelligencePane: React.FC<Props> = ({ session }) => {
  const localLlmAnalysis: LocalLLMAnalysis | undefined = session?.local_llm;
  const geminiAnalysis: GeminiAnalysis | undefined = session?.gemini;
  const [geminiInput, setGeminiInput] = useState('');
  const [sendingGemini, setSendingGemini] = useState(false);
  const scrollRef = useRef<HTMLDivElement | null>(null);

  // Debug logging
  useEffect(() => {
    console.log('GeminiChatPane - geminiAnalysis:', geminiAnalysis);
    console.log('GeminiChatPane - query_type:', geminiAnalysis?.query_type);
    console.log('GeminiChatPane - response:', geminiAnalysis?.response);
  }, [geminiAnalysis]);

  const localLlmLastAnalysisAt = localLlmAnalysis?.last_analysis_at
    ? new Date(localLlmAnalysis.last_analysis_at).toLocaleString()
    : 'N/A';

  const geminiLastCallAt = geminiAnalysis?.last_call_at
    ? new Date(geminiAnalysis.last_call_at).toLocaleString()
    : 'N/A';

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [localLlmAnalysis, geminiAnalysis]);

  async function handleTriggerGemini(e: React.FormEvent) {
    e.preventDefault();
    if (!geminiInput.trim() || !session?.session_id) return;
    setSendingGemini(true);
    try {
      await triggerGemini(session.session_id, geminiInput.trim());
      setGeminiInput('');
    } finally {
      setSendingGemini(false);
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
        LLM INSIGHTS
      </div>

      <div
        ref={scrollRef}
        style={{
          flex: 1,
          overflowY: 'auto',
          padding: '0.5rem 0.75rem',
          border: '2px solid #374151',
          borderRadius: '0.5rem',
          marginTop: '0.5rem',
          background: '#020617',
          fontSize: '0.9rem',
          color: '#e5e7eb',
        }}
      >
        {localLlmAnalysis || geminiAnalysis ? (
          <div>
            <h3 style={{ color: '#a5b4fc', marginBottom: '0.5rem' }}>Tactical Insights (Local LLM)</h3>
            {localLlmAnalysis ? (
              <div>
                <p><strong>Last Analyzed:</strong> {localLlmLastAnalysisAt}</p>
                {localLlmAnalysis.error ? (
                  <p style={{ color: '#dc2626' }}><strong>Error:</strong> {localLlmAnalysis.error}</p>
                ) : (
                  <>
                    <p><strong>Global Summary:</strong> {localLlmAnalysis.global_summary || 'N/A'}</p>
                    <p><strong>Latest Interaction:</strong> {localLlmAnalysis.latest_interaction_summary || 'N/A'}</p>
                    <p><strong>Sentiment:</strong> {localLlmAnalysis.current_sentiment || 'N/A'}</p>
                    <p><strong>Conversation State:</strong> {localLlmAnalysis.conversation_state_tag || 'N/A'}</p>
                  </>
                )}
              </div>
            ) : (
              <p style={{ color: '#6b7280' }}>No Local LLM analysis available yet.</p>
            )}

            <h3 style={{ color: '#a5b4fc', marginTop: '1.5rem', marginBottom: '0.5rem' }}>Strategic Insights (Gemini)</h3>
            {geminiAnalysis ? (
              <div>
                <p><strong>Last Called:</strong> {geminiLastCallAt}</p>
                {geminiAnalysis.error ? (
                  <p style={{ color: '#dc2626' }}><strong>Error:</strong> {geminiAnalysis.error}</p>
                ) : (
                  <>
                    {geminiAnalysis.response ? (
                      <div style={{ background: '#1f2937', padding: '0.75rem', borderRadius: '0.5rem', marginTop: '0.5rem' }}>
                        {/* Debug: Show raw response if nothing else renders */}
                        {!geminiAnalysis.response.answer && !geminiAnalysis.response.analysis && (
                          <div style={{ marginBottom: '1rem', background: '#7f1d1d', padding: '0.75rem', borderRadius: '0.5rem' }}>
                            <h4 style={{ color: '#fca5a5', marginBottom: '0.5rem' }}>Debug: Raw Response</h4>
                            <pre style={{ fontSize: '0.75rem', whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
                              {JSON.stringify(geminiAnalysis.response, null, 2)}
                            </pre>
                          </div>
                        )}
                        
                        {/* User Query Response */}
                        {geminiAnalysis.response.answer && (
                          <div style={{ marginBottom: '1rem', background: '#0f172a', padding: '0.75rem', borderRadius: '0.5rem', borderLeft: '3px solid #818cf8' }}>
                            {geminiAnalysis.user_query && (
                              <h4 style={{ color: '#818cf8', marginBottom: '0.5rem', fontSize: '0.9rem' }}>
                                Q: {geminiAnalysis.user_query}
                              </h4>
                            )}
                            <p style={{ marginBottom: '0.75rem', lineHeight: 1.6 }}>{geminiAnalysis.response.answer}</p>
                            {geminiAnalysis.response.key_insights && geminiAnalysis.response.key_insights.length > 0 && (
                              <div style={{ marginTop: '0.75rem' }}>
                                <strong style={{ color: '#a5b4fc' }}>Key Insights:</strong>
                                <ul style={{ marginTop: '0.25rem', marginLeft: '1.25rem', lineHeight: 1.6 }}>
                                  {geminiAnalysis.response.key_insights.map((insight: string, idx: number) => (
                                    <li key={idx}>{insight}</li>
                                  ))}
                                </ul>
                              </div>
                            )}
                            {geminiAnalysis.response.suggested_action && (
                              <p style={{ marginTop: '0.75rem', color: '#10b981' }}>
                                <strong>Action:</strong> {geminiAnalysis.response.suggested_action}
                              </p>
                            )}
                          </div>
                        )}
                        
                        {/* Strategic Review Response */}
                        {geminiAnalysis.response.analysis && (
                          <div style={{ marginBottom: '1rem' }}>
                            <h4 style={{ color: '#818cf8', marginBottom: '0.5rem' }}>Analysis</h4>
                            <p><strong>Stage:</strong> {geminiAnalysis.response.analysis.current_stage}</p>
                            <p><strong>Client Mode:</strong> {geminiAnalysis.response.analysis.client_mode}</p>
                            <p><strong>Critique:</strong> {geminiAnalysis.response.analysis.salesperson_critique}</p>
                            {geminiAnalysis.response.analysis.red_flags?.length > 0 && (
                              <p><strong>Red Flags:</strong> {geminiAnalysis.response.analysis.red_flags.join(', ')}</p>
                            )}
                          </div>
                        )}
                        {geminiAnalysis.response.strategy && (
                          <div style={{ marginBottom: '1rem' }}>
                            <h4 style={{ color: '#818cf8', marginBottom: '0.5rem' }}>Strategy</h4>
                            <p><strong>Suggested Message:</strong> {geminiAnalysis.response.strategy.suggested_next_message}</p>
                            <p><strong>Question:</strong> {geminiAnalysis.response.strategy.suggested_question}</p>
                            {geminiAnalysis.response.strategy.personal_hook && (
                              <p><strong>Personal Hook:</strong> {geminiAnalysis.response.strategy.personal_hook}</p>
                            )}
                          </div>
                        )}
                        {geminiAnalysis.response.tracker && (
                          <div style={{ marginBottom: '1rem' }}>
                            <h4 style={{ color: '#818cf8', marginBottom: '0.5rem' }}>Tracker (B.A.N.T.)</h4>
                            <p><strong>Trust Level:</strong> {geminiAnalysis.response.tracker.trust_level}</p>
                            <p><strong>Budget:</strong> {geminiAnalysis.response.tracker.budget_clarity}</p>
                            <p><strong>Authority:</strong> {geminiAnalysis.response.tracker.authority_status}</p>
                            {geminiAnalysis.response.tracker.pain_points_discovered?.length > 0 && (
                              <p><strong>Pain Points:</strong> {geminiAnalysis.response.tracker.pain_points_discovered.join(', ')}</p>
                            )}
                          </div>
                        )}
                        {geminiAnalysis.response.objections && (
                          <div>
                            <h4 style={{ color: '#818cf8', marginBottom: '0.5rem' }}>Objections</h4>
                            <p><strong>Predicted Next:</strong> {geminiAnalysis.response.objections.predicted_next}</p>
                            <p><strong>Probability:</strong> {(geminiAnalysis.response.objections.probability * 100).toFixed(0)}%</p>
                            <p><strong>Tactic:</strong> {geminiAnalysis.response.objections.preemptive_tactic}</p>
                          </div>
                        )}
                      </div>
                    ) : (
                      <p style={{ color: '#6b7280' }}>No Gemini response available yet.</p>
                    )}
                  </>
                )}
              </div>
            ) : (
              <p style={{ color: '#6b7280' }}>No Gemini analysis available yet.</p>
            )}
          </div>
        ) : (
          <div style={{ color: '#6b7280' }}>
            No LLM analysis available for this session yet. Send a message or trigger Gemini to get insights.
          </div>
        )}
      </div>

      <form
        onSubmit={handleTriggerGemini}
        style={{
          padding: '1rem 0.75rem',
          borderTop: '2px solid #374151',
          background: '#020617',
          display: 'flex',
          gap: '0.5rem',
          alignItems: 'center',
          marginTop: '0.5rem',
        }}
      >
        <textarea
          value={geminiInput}
          onChange={(e) => setGeminiInput(e.target.value)}
          placeholder="Ask Gemini for strategic advice..."
          rows={1}
          style={{
            flex: 1,
            padding: '0.5rem 0.75rem',
            borderRadius: '0.375rem',
            border: '1px solid #4b5563',
            background: '#1f2937',
            color: '#e5e7eb',
            fontSize: '0.85rem',
            outline: 'none',
            resize: 'none',
            fontFamily: 'inherit',
          }}
          disabled={!session?.session_id || sendingGemini}
        />
        <button
          type="submit"
          disabled={!session?.session_id || sendingGemini || !geminiInput.trim()}
          style={{
            padding: '0.5rem 1rem',
            borderRadius: '0.375rem',
            border: 'none',
            background: '#6366f1',
            color: '#ffffff',
            fontSize: '0.85rem',
            fontWeight: 600,
            cursor: (!session?.session_id || sendingGemini || !geminiInput.trim()) ? 'not-allowed' : 'pointer',
            opacity: (!session?.session_id || sendingGemini || !geminiInput.trim()) ? 0.6 : 1,
            flexShrink: 0,
          }}
        >
          {sendingGemini ? 'Sending...' : 'Trigger Gemini'}
        </button>
      </form>
    </div>
  );
};

export default IntelligencePane;
