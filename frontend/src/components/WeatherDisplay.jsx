import React from 'react';

function getWeatherIcon(conditions, icon) {
  const conditionsLower = (conditions || '').toLowerCase();

  if (conditionsLower.includes('snow')) return '❄️';
  if (conditionsLower.includes('rain')) return '🌧️';
  if (conditionsLower.includes('cloud')) return '☁️';
  if (conditionsLower.includes('clear') || conditionsLower.includes('sun')) return '☀️';
  if (conditionsLower.includes('fog') || conditionsLower.includes('mist')) return '🌫️';

  return '⛅';
}

export default function WeatherDisplay({ weather }) {
  if (!weather) {
    return (
      <div className="weather-display weather-unavailable">
        <span className="weather-icon">❓</span>
        <span>Weather data unavailable</span>
      </div>
    );
  }

  const icon = getWeatherIcon(weather.conditions, weather.icon);

  return (
    <div className="weather-display">
      <div className="weather-main">
        <span className="weather-icon">{icon}</span>
        <div className="weather-temps">
          <span className="temp-high">{weather.temperature_max?.toFixed(0)}°</span>
          <span className="temp-separator">/</span>
          <span className="temp-low">{weather.temperature_min?.toFixed(0)}°</span>
        </div>
      </div>
      <div className="weather-details">
        <span className="weather-conditions">{weather.conditions}</span>
        {weather.snowfall_cm > 0 && (
          <span className="weather-snow">❄️ {weather.snowfall_cm?.toFixed(0)}cm expected</span>
        )}
        <span className="weather-wind">💨 {weather.wind_speed?.toFixed(0)} km/h</span>
      </div>
    </div>
  );
}
