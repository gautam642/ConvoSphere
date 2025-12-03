import React from 'react';
import type { Session } from '../types';

interface Props {
  session: Session | null;
}

const OsintPane: React.FC<Props> = ({ session }) => {
  const osintData = session?.osint;
  
  // Debug logging
  console.log('OsintPane - session:', session);
  console.log('OsintPane - osintData:', osintData);
  console.log('OsintPane - osintData.status:', osintData?.status);
  console.log('OsintPane - osintData.data:', osintData?.data);
  console.log('OsintPane - osintData.data?.final_summary:', osintData?.data?.final_summary);
  
  const hasOsintData = osintData && (
    osintData.status === 'completed' || 
    osintData.data || 
    osintData.numverify || 
    osintData.linkedin || 
    osintData.serp
  );
  
  console.log('OsintPane - hasOsintData:', hasOsintData);

  const isProcessing = osintData?.status === 'processing';
  const hasFailed = osintData?.status === 'failed';

  return (
    <div
      style={{
        height: '100%',
        background: '#1a1d29',
        borderRadius: 12,
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
      }}
    >
      {/* Header */}
      <div
        style={{
          padding: '1rem 1.25rem',
          borderBottom: '1px solid #2a2f3d',
          background: '#1a1d29',
        }}
      >
        <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#ffffff', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <span style={{ fontSize: '1.3rem' }}>🔍</span>
          OSINT Profile
        </div>
        <div style={{ fontSize: '0.8rem', color: '#9ca3af', marginTop: '0.25rem' }}>
          Open Source Intelligence Data
        </div>
      </div>

      {/* Content */}
      <div
        style={{
          flex: 1,
          overflowY: 'auto',
          padding: '1.25rem',
        }}
      >
        {!session ? (
          <div style={{ textAlign: 'center', color: '#6b7280', padding: '2rem 1rem' }}>
            <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>📊</div>
            <div style={{ fontSize: '0.95rem' }}>Select a session to view OSINT data</div>
          </div>
        ) : isProcessing ? (
          <div style={{ textAlign: 'center', color: '#9ca3af', padding: '2rem 1rem' }}>
            <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>⏳</div>
            <div style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '0.5rem', color: '#ffffff' }}>
              OSINT Enrichment in Progress
            </div>
            <div style={{ fontSize: '0.85rem', lineHeight: 1.6 }}>
              We're gathering intelligence from multiple sources including:
            </div>
            <div style={{ marginTop: '1rem', textAlign: 'left', background: '#0f1419', padding: '1rem', borderRadius: 8, fontSize: '0.85rem' }}>
              <div style={{ marginBottom: '0.5rem' }}>✓ Phone validation</div>
              <div style={{ marginBottom: '0.5rem' }}>✓ Social media profiles (Twitter/X)</div>
              <div style={{ marginBottom: '0.5rem' }}>✓ Professional networks (LinkedIn)</div>
              <div style={{ marginBottom: '0.5rem' }}>✓ Web presence (Google Search)</div>
              <div>✓ AI-powered analysis</div>
            </div>
            <div style={{ marginTop: '1rem', fontSize: '0.8rem', color: '#6b7280' }}>
              This usually takes 30-60 seconds...
            </div>
          </div>
        ) : hasFailed ? (
          <div style={{ textAlign: 'center', color: '#ef4444', padding: '2rem 1rem' }}>
            <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>⚠️</div>
            <div style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '0.5rem' }}>
              OSINT Enrichment Failed
            </div>
            <div style={{ fontSize: '0.85rem', color: '#9ca3af' }}>
              {osintData?.error || 'An error occurred during data collection'}
            </div>
          </div>
        ) : hasOsintData ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {/* Customer Info */}
            <div style={{ background: '#0f1419', padding: '1rem', borderRadius: 8, border: '1px solid #2a2f3d' }}>
              <div style={{ fontSize: '0.9rem', fontWeight: 600, color: '#0ea5e9', marginBottom: '0.75rem' }}>
                👤 Customer Information
              </div>
              <div style={{ fontSize: '0.85rem', color: '#e5e7eb', lineHeight: 1.8 }}>
                <div><strong>Name:</strong> {session.customer.name}</div>
                <div><strong>Phone:</strong> {session.customer.phone}</div>
                {session.customer.context && <div><strong>Context:</strong> {session.customer.context}</div>}
                {session.customer.goal && <div><strong>Goal:</strong> {session.customer.goal}</div>}
              </div>
            </div>

            {/* Phone Validation */}
            {osintData.numverify && (
              <div style={{ background: '#0f1419', padding: '1rem', borderRadius: 8, border: '1px solid #2a2f3d' }}>
                <div style={{ fontSize: '0.9rem', fontWeight: 600, color: '#22c55e', marginBottom: '0.75rem' }}>
                  📞 Phone Validation
                </div>
                <div style={{ fontSize: '0.85rem', color: '#e5e7eb', lineHeight: 1.8 }}>
                  <pre style={{ whiteSpace: 'pre-wrap', wordWrap: 'break-word', fontFamily: 'inherit' }}>
                    {JSON.stringify(osintData.numverify, null, 2)}
                  </pre>
                </div>
              </div>
            )}

            {/* LinkedIn */}
            {osintData.linkedin && (
              <div style={{ background: '#0f1419', padding: '1rem', borderRadius: 8, border: '1px solid #2a2f3d' }}>
                <div style={{ fontSize: '0.9rem', fontWeight: 600, color: '#0077b5', marginBottom: '0.75rem' }}>
                  💼 LinkedIn Profile
                </div>
                <div style={{ fontSize: '0.85rem', color: '#e5e7eb', lineHeight: 1.8 }}>
                  <pre style={{ whiteSpace: 'pre-wrap', wordWrap: 'break-word', fontFamily: 'inherit' }}>
                    {JSON.stringify(osintData.linkedin, null, 2)}
                  </pre>
                </div>
              </div>
            )}

            {/* Web Search Results */}
            {osintData.serp && osintData.serp.length > 0 && (
              <div style={{ background: '#0f1419', padding: '1rem', borderRadius: 8, border: '1px solid #2a2f3d' }}>
                <div style={{ fontSize: '0.9rem', fontWeight: 600, color: '#f59e0b', marginBottom: '0.75rem' }}>
                  🔎 Web Search Results
                </div>
                <div style={{ fontSize: '0.85rem', color: '#e5e7eb', lineHeight: 1.8 }}>
                  {osintData.serp.slice(0, 5).map((result: any, idx: number) => (
                    <div key={idx} style={{ marginBottom: '0.75rem', paddingBottom: '0.75rem', borderBottom: idx < 4 ? '1px solid #2a2f3d' : 'none' }}>
                      <div style={{ fontWeight: 600, color: '#0ea5e9' }}>{result.title || 'No title'}</div>
                      <div style={{ fontSize: '0.8rem', color: '#9ca3af', marginTop: '0.25rem' }}>
                        {result.link || result.url || 'No URL'}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* OSINT Final Summary */}
            {osintData.data?.final_summary && (
              <>
                {/* Person Profile */}
                {osintData.data.final_summary.person_profile && (
                  <div style={{ background: '#0f1419', padding: '1rem', borderRadius: 8, border: '1px solid #2a2f3d' }}>
                    <div style={{ fontSize: '0.9rem', fontWeight: 600, color: '#3b82f6', marginBottom: '0.75rem' }}>
                      👤 Person Profile
                    </div>
                    <div style={{ fontSize: '0.85rem', color: '#e5e7eb', lineHeight: 1.8 }}>
                      {/* Basic Info */}
                      {osintData.data.final_summary.person_profile.basic_info && (
                        <>
                          {osintData.data.final_summary.person_profile.basic_info.name && (
                            <div style={{ marginBottom: '0.5rem' }}>
                              <strong>Name:</strong> {osintData.data.final_summary.person_profile.basic_info.name}
                            </div>
                          )}
                          {osintData.data.final_summary.person_profile.basic_info.current_role && (
                            <div style={{ marginBottom: '0.5rem' }}>
                              <strong>Role:</strong> {osintData.data.final_summary.person_profile.basic_info.current_role}
                            </div>
                          )}
                          {osintData.data.final_summary.person_profile.basic_info.company && (
                            <div style={{ marginBottom: '0.5rem' }}>
                              <strong>Company:</strong> {osintData.data.final_summary.person_profile.basic_info.company}
                            </div>
                          )}
                          {osintData.data.final_summary.person_profile.basic_info.location && (
                            <div style={{ marginBottom: '0.5rem' }}>
                              <strong>Location:</strong> {osintData.data.final_summary.person_profile.basic_info.location}
                            </div>
                          )}
                          {osintData.data.final_summary.person_profile.basic_info.industry && (
                            <div style={{ marginBottom: '0.5rem' }}>
                              <strong>Industry:</strong> {osintData.data.final_summary.person_profile.basic_info.industry}
                            </div>
                          )}
                        </>
                      )}
                      
                      {/* Contact Info */}
                      {osintData.data.final_summary.person_profile.contact_info && (
                        <div style={{ marginTop: '1rem', paddingTop: '1rem', borderTop: '1px solid #2a2f3d' }}>
                          <strong style={{ color: '#60a5fa' }}>Contact Information:</strong>
                          {osintData.data.final_summary.person_profile.contact_info.email && (
                            <div style={{ marginTop: '0.5rem' }}>
                              <strong>Email:</strong> {osintData.data.final_summary.person_profile.contact_info.email}
                            </div>
                          )}
                          {osintData.data.final_summary.person_profile.contact_info.phone && (
                            <div style={{ marginTop: '0.25rem' }}>
                              <strong>Phone:</strong> {osintData.data.final_summary.person_profile.contact_info.phone}
                            </div>
                          )}
                          {osintData.data.final_summary.person_profile.contact_info.linkedin && (
                            <div style={{ marginTop: '0.25rem' }}>
                              <strong>LinkedIn:</strong> <a href={osintData.data.final_summary.person_profile.contact_info.linkedin} target="_blank" rel="noopener noreferrer" style={{ color: '#60a5fa' }}>Profile</a>
                            </div>
                          )}
                        </div>
                      )}
                      
                      {/* Professional Background */}
                      {osintData.data.final_summary.person_profile.professional_background && (
                        <div style={{ marginTop: '1rem', paddingTop: '1rem', borderTop: '1px solid #2a2f3d' }}>
                          {osintData.data.final_summary.person_profile.professional_background.skills && osintData.data.final_summary.person_profile.professional_background.skills.length > 0 && (
                            <div>
                              <strong style={{ color: '#60a5fa' }}>Key Skills:</strong>
                              <ul style={{ marginTop: '0.5rem', marginLeft: '1.5rem', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.25rem' }}>
                                {osintData.data.final_summary.person_profile.professional_background.skills.slice(0, 8).map((skill: string, idx: number) => (
                                  <li key={idx}>{skill}</li>
                                ))}
                              </ul>
                            </div>
                          )}
                          {osintData.data.final_summary.person_profile.professional_background.education && osintData.data.final_summary.person_profile.professional_background.education.length > 0 && (
                            <div style={{ marginTop: '0.75rem' }}>
                              <strong style={{ color: '#60a5fa' }}>Education:</strong>
                              <ul style={{ marginTop: '0.5rem', marginLeft: '1.5rem' }}>
                                {osintData.data.final_summary.person_profile.professional_background.education}
                              </ul>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* Sales Intelligence */}
                {osintData.data.final_summary.sales_intelligence && (
                  <div style={{ background: '#0f1419', padding: '1rem', borderRadius: 8, border: '1px solid #2a2f3d' }}>
                    <div style={{ fontSize: '0.9rem', fontWeight: 600, color: '#10b981', marginBottom: '0.75rem' }}>
                      💡 Sales Intelligence
                    </div>
                    <div style={{ fontSize: '0.85rem', color: '#e5e7eb', lineHeight: 1.8 }}>
                      {osintData.data.final_summary.sales_intelligence.talking_points && osintData.data.final_summary.sales_intelligence.talking_points.length > 0 && (
                        <div style={{ marginBottom: '1rem' }}>
                          <strong style={{ color: '#10b981' }}>Talking Points:</strong>
                          <ul style={{ marginTop: '0.5rem', marginLeft: '1.5rem' }}>
                            {osintData.data.final_summary.sales_intelligence.talking_points.map((point: string, idx: number) => (
                              <li key={idx} style={{ marginBottom: '0.5rem' }}>{point}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                      {osintData.data.final_summary.sales_intelligence.pain_points && osintData.data.final_summary.sales_intelligence.pain_points.length > 0 && (
                        <div style={{ marginBottom: '1rem' }}>
                          <strong style={{ color: '#ef4444' }}>Pain Points:</strong>
                          <ul style={{ marginTop: '0.5rem', marginLeft: '1.5rem' }}>
                            {osintData.data.final_summary.sales_intelligence.pain_points.map((point: string, idx: number) => (
                              <li key={idx} style={{ marginBottom: '0.5rem' }}>{point}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                      {osintData.data.final_summary.sales_intelligence.interests && osintData.data.final_summary.sales_intelligence.interests.length > 0 && (
                        <div style={{ marginBottom: '1rem' }}>
                          <strong style={{ color: '#f59e0b' }}>Interests:</strong>
                          <ul style={{ marginTop: '0.5rem', marginLeft: '1.5rem' }}>
                            {osintData.data.final_summary.sales_intelligence.interests.map((interest: string, idx: number) => (
                              <li key={idx}>{interest}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                      {osintData.data.final_summary.sales_intelligence.best_contact_method && (
                        <div style={{ marginBottom: '0.5rem' }}>
                          <strong>Best Contact Method:</strong> {osintData.data.final_summary.sales_intelligence.best_contact_method}
                        </div>
                      )}
                      {osintData.data.final_summary.sales_intelligence.timing_insights && (
                        <div>
                          <strong>Timing Insights:</strong> {osintData.data.final_summary.sales_intelligence.timing_insights}
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* Company Context */}
                {osintData.data.final_summary.company_context && (
                  <div style={{ background: '#0f1419', padding: '1rem', borderRadius: 8, border: '1px solid #2a2f3d' }}>
                    <div style={{ fontSize: '0.9rem', fontWeight: 600, color: '#8b5cf6', marginBottom: '0.75rem' }}>
                      🏢 Company Context
                    </div>
                    <div style={{ fontSize: '0.85rem', color: '#e5e7eb', lineHeight: 1.8 }}>
                      {osintData.data.final_summary.company_context.company_description && (
                        <div style={{ marginBottom: '0.5rem' }}>
                          <strong>Description:</strong> {osintData.data.final_summary.company_context.company_description}
                        </div>
                      )}
                      {osintData.data.final_summary.company_context.company_size && (
                        <div style={{ marginBottom: '0.5rem' }}>
                          <strong>Size:</strong> {osintData.data.final_summary.company_context.company_size}
                        </div>
                      )}
                      {osintData.data.final_summary.company_context.industry_trends && (
                        <div style={{ marginBottom: '0.5rem' }}>
                          <strong>Industry Trends:</strong> {osintData.data.final_summary.company_context.industry_trends}
                        </div>
                      )}
                      {osintData.data.final_summary.company_context.potential_pain_points && osintData.data.final_summary.company_context.potential_pain_points.length > 0 && (
                        <div>
                          <strong>Potential Pain Points:</strong>
                          <ul style={{ marginTop: '0.25rem', marginLeft: '1.5rem' }}>
                            {osintData.data.final_summary.company_context.potential_pain_points.map((point: string, idx: number) => (
                              <li key={idx} style={{ marginBottom: '0.25rem' }}>{point}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* Verification Status */}
                {osintData.data.final_summary.verification_status && (
                  <div style={{ background: '#0f1419', padding: '1rem', borderRadius: 8, border: '1px solid #2a2f3d' }}>
                    <div style={{ fontSize: '0.9rem', fontWeight: 600, color: '#06b6d4', marginBottom: '0.75rem' }}>
                      ✅ Verification Status
                    </div>
                    <div style={{ fontSize: '0.85rem', color: '#e5e7eb', lineHeight: 1.8 }}>
                      <div style={{ marginBottom: '0.5rem' }}>
                        <strong>Status:</strong> <span style={{ 
                          color: osintData.data.final_summary.verification_status === 'VERIFIED' ? '#10b981' : 
                                osintData.data.final_summary.verification_status === 'ERROR' ? '#ef4444' : '#f59e0b'
                        }}>
                          {osintData.data.final_summary.verification_status}
                        </span>
                      </div>
                      {osintData.data.final_summary.confidence_score !== null && osintData.data.final_summary.confidence_score !== undefined && (
                        <div>
                          <strong>Confidence Score:</strong> {(osintData.data.final_summary.confidence_score * 100).toFixed(1)}%
                        </div>
                      )}
                      {osintData.data.final_summary.error && (
                        <div style={{ marginTop: '0.5rem', color: '#ef4444' }}>
                          <strong>Error:</strong> {osintData.data.final_summary.error}
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </>
            )}

            {/* Confidence Score */}
            {osintData.confidence !== null && osintData.confidence !== undefined && (
              <div style={{ background: '#0f1419', padding: '1rem', borderRadius: 8, border: '1px solid #2a2f3d' }}>
                <div style={{ fontSize: '0.9rem', fontWeight: 600, color: '#10b981', marginBottom: '0.75rem' }}>
                  ✨ Confidence Score
                </div>
                <div style={{ fontSize: '1.5rem', fontWeight: 700, color: '#10b981' }}>
                  {(osintData.confidence * 100).toFixed(1)}%
                </div>
              </div>
            )}
          </div>
        ) : (
          <div style={{ textAlign: 'center', color: '#9ca3af', padding: '2rem 1rem' }}>
            <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>🚀</div>
            <div style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '0.5rem', color: '#ffffff' }}>
              OSINT Enrichment Coming Soon
            </div>
            <div style={{ fontSize: '0.85rem', lineHeight: 1.6, marginBottom: '1.5rem' }}>
              Our AI-powered OSINT system will automatically gather and analyze intelligence from multiple sources to help you understand your customer better.
            </div>
            <div style={{ textAlign: 'left', background: '#0f1419', padding: '1rem', borderRadius: 8, fontSize: '0.85rem' }}>
              <div style={{ fontWeight: 600, marginBottom: '0.75rem', color: '#0ea5e9' }}>What we'll gather:</div>
              <div style={{ marginBottom: '0.5rem' }}>📞 Phone number validation & carrier info</div>
              <div style={{ marginBottom: '0.5rem' }}>🐦 Twitter/X profile & activity</div>
              <div style={{ marginBottom: '0.5rem' }}>💼 LinkedIn professional background</div>
              <div style={{ marginBottom: '0.5rem' }}>🔍 Web presence & digital footprint</div>
              <div style={{ marginBottom: '0.5rem' }}>🌐 Company information & context</div>
              <div>🤖 AI-powered insights & recommendations</div>
            </div>
            <div style={{ marginTop: '1.5rem', fontSize: '0.8rem', color: '#6b7280' }}>
              OSINT enrichment starts automatically when you create a new session.
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default OsintPane;
