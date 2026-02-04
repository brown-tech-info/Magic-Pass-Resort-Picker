import React from 'react';
import WeatherDisplay from './WeatherDisplay';
import SnowDisplay from './SnowDisplay';
import TransportDisplay from './TransportDisplay';

function ScoreBar({ score, maxScore = 10 }) {
  const percentage = (score / maxScore) * 100;
  let colorClass = 'score-low';
  if (score >= 7) colorClass = 'score-high';
  else if (score >= 5) colorClass = 'score-medium';

  return (
    <div className="score-bar">
      <div
        className={`score-bar-fill ${colorClass}`}
        style={{ width: `${percentage}%` }}
      />
    </div>
  );
}

export default function RecommendationCard({ recommendation, rank }) {
  const { resort, score, weather_score, snow_score, transport_score, size_score,
          weather_forecast, snow_conditions, journey, highlights, concerns } = recommendation;

  return (
    <div className={`recommendation-card ${rank === 1 ? 'top-pick' : ''}`}>
      {rank === 1 && <div className="top-pick-badge">Top Pick</div>}

      <div className="card-header">
        <div className="resort-info">
          <h3 className="resort-name">{resort.name}</h3>
          <span className="resort-region">{resort.region}</span>
        </div>
        <div className="score-container">
          <span className="score-value">{score.toFixed(1)}</span>
          <span className="score-max">/10</span>
        </div>
      </div>

      <div className="card-scores">
        <div className="score-item">
          <span className="score-label">☀️ Weather</span>
          <ScoreBar score={weather_score} />
          <span className="score-number">{weather_score.toFixed(1)}</span>
        </div>
        <div className="score-item">
          <span className="score-label">❄️ Snow</span>
          <ScoreBar score={snow_score} />
          <span className="score-number">{snow_score.toFixed(1)}</span>
        </div>
        <div className="score-item">
          <span className="score-label">🚂 Travel</span>
          <ScoreBar score={transport_score} />
          <span className="score-number">{transport_score.toFixed(1)}</span>
        </div>
        <div className="score-item">
          <span className="score-label">⛷️ Size</span>
          <ScoreBar score={size_score || 5} />
          <span className="score-number">{(size_score || 5).toFixed(1)}</span>
        </div>
      </div>

      <div className="card-details">
        <div className="detail-section">
          <h4>Weather</h4>
          <WeatherDisplay weather={weather_forecast} />
        </div>

        <div className="detail-section">
          <h4>Snow Conditions</h4>
          <SnowDisplay snow={snow_conditions} />
        </div>

        <div className="detail-section">
          <h4>Getting There</h4>
          <TransportDisplay journey={journey} />
        </div>
      </div>

      {(highlights.length > 0 || concerns.length > 0) && (
        <div className="card-highlights">
          {highlights.length > 0 && (
            <div className="highlights">
              {highlights.slice(0, 3).map((h, i) => (
                <span key={i} className="highlight-item">✅ {h}</span>
              ))}
            </div>
          )}
          {concerns.length > 0 && (
            <div className="concerns">
              {concerns.slice(0, 2).map((c, i) => (
                <span key={i} className="concern-item">⚠️ {c}</span>
              ))}
            </div>
          )}
        </div>
      )}

      <div className="card-footer">
        <div className="resort-stats">
          <span className="stat-item">⛰️ {resort.elevation_base}m - {resort.elevation_top}m</span>
          {resort.skiable_terrain_km && (
            <span className="stat-item">⛷️ {resort.skiable_terrain_km}km pistes</span>
          )}
        </div>
        <a
          href={resort.website}
          target="_blank"
          rel="noopener noreferrer"
          className="resort-link"
        >
          Visit Website →
        </a>
      </div>
    </div>
  );
}
