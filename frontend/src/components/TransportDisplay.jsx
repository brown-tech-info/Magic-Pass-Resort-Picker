import React from 'react';

function formatDuration(minutes) {
  const hours = Math.floor(minutes / 60);
  const mins = minutes % 60;
  if (hours === 0) return `${mins}min`;
  return `${hours}h ${mins}min`;
}

function formatTime(dateString) {
  if (!dateString) return '';
  const date = new Date(dateString);
  return date.toLocaleTimeString('en-CH', { hour: '2-digit', minute: '2-digit' });
}

export default function TransportDisplay({ journey }) {
  if (!journey) {
    return (
      <div className="transport-display transport-unavailable">
        <span className="transport-icon">🚂</span>
        <span>Transport data unavailable</span>
      </div>
    );
  }

  return (
    <div className="transport-display">
      <div className="transport-main">
        <span className="transport-icon">🚂</span>
        <span className="transport-duration">{formatDuration(journey.duration_minutes)}</span>
      </div>

      <div className="transport-details">
        <div className="transport-times">
          <span className="time-departure">{formatTime(journey.departure_time)}</span>
          <span className="time-arrow">→</span>
          <span className="time-arrival">{formatTime(journey.arrival_time)}</span>
        </div>

        <div className="transport-changes">
          {journey.changes === 0 ? (
            <span className="direct">Direct</span>
          ) : (
            <span>{journey.changes} change{journey.changes > 1 ? 's' : ''}</span>
          )}
        </div>
      </div>

      {journey.segments && journey.segments.length > 0 && (
        <div className="transport-segments">
          {journey.segments.slice(0, 3).map((segment, index) => (
            <span key={index} className={`segment segment-${segment.type}`}>
              {segment.type === 'train' ? '🚂' : '🚌'} {segment.line}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
