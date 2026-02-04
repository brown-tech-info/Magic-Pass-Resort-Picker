import React from 'react';

function getSnowQualityColor(quality) {
  const q = (quality || '').toLowerCase();
  if (q === 'powder' || q === 'fresh') return 'quality-excellent';
  if (q === 'packed' || q === 'groomed') return 'quality-good';
  if (q === 'icy' || q === 'hard') return 'quality-poor';
  return 'quality-unknown';
}

export default function SnowDisplay({ snow }) {
  if (!snow) {
    return (
      <div className="snow-display snow-unavailable">
        <span className="snow-icon">❄️</span>
        <span>Snow data unavailable</span>
      </div>
    );
  }

  const qualityClass = getSnowQualityColor(snow.snow_quality);

  return (
    <div className="snow-display">
      <div className="snow-depths">
        {snow.snow_base && (
          <div className="snow-depth">
            <span className="depth-label">Base</span>
            <span className="depth-value">{snow.snow_base}cm</span>
          </div>
        )}
        {snow.snow_summit && (
          <div className="snow-depth">
            <span className="depth-label">Summit</span>
            <span className="depth-value">{snow.snow_summit}cm</span>
          </div>
        )}
      </div>

      {snow.new_snow_24h > 0 && (
        <div className="fresh-snow">
          <span className="fresh-snow-icon">✨</span>
          <span>{snow.new_snow_24h}cm fresh in 24h</span>
        </div>
      )}

      <div className={`snow-quality ${qualityClass}`}>
        {snow.snow_quality}
      </div>
    </div>
  );
}
