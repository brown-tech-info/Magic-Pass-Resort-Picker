import React from 'react';

export default function AISummary({ summary }) {
  if (!summary) return null;

  return (
    <div className="ai-summary">
      <div className="ai-summary-header">
        <span className="ai-icon">🤖</span>
        <h3>AI Recommendation</h3>
      </div>
      <div className="ai-summary-content">
        {summary.split('\n').map((paragraph, index) => (
          paragraph.trim() && <p key={index}>{paragraph}</p>
        ))}
      </div>
    </div>
  );
}
