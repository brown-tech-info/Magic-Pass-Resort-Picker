import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import RecommendationCard from './components/RecommendationCard';
import AISummary from './components/AISummary';
import LoadingSpinner from './components/LoadingSpinner';
import { getHealthStatus } from './services/api';
import { useSSERecommendations } from './hooks/useSSERecommendations';

function App() {
  const {
    recommendations,
    aiSummary,
    targetWeekend,
    loading,
    error,
    progress,
    fetchRecommendations,
  } = useSSERecommendations();

  const [apiStatus, setApiStatus] = useState(null);
  const [showAll, setShowAll] = useState(false);

  useEffect(() => {
    checkApiHealth();
  }, []);

  async function checkApiHealth() {
    try {
      const status = await getHealthStatus();
      setApiStatus(status);
    } catch (err) {
      setApiStatus({ status: 'offline', services: {} });
    }
  }

  function handleGetRecommendations() {
    setShowAll(false);
    fetchRecommendations('Geneva', null, 10);
  }

  const displayedRecommendations = showAll
    ? recommendations
    : recommendations?.slice(0, 5);

  return (
    <div className="app">
      <Header targetWeekend={targetWeekend} />

      <main className="main-content">
        {apiStatus?.status === 'offline' && (
          <div className="status-banner status-offline">
            Backend server is not running. Please start the backend server first.
          </div>
        )}

        {!recommendations && !loading && (
          <div className="welcome-section">
            <div className="welcome-card">
              <h2>Plan Your Perfect Weekend</h2>
              <p>
                Get personalized ski resort recommendations based on weather forecasts,
                snow conditions, and travel times from Geneva.
              </p>

              <div className="features">
                <div className="feature">
                  <span className="feature-icon">☀️</span>
                  <span>Weather Analysis</span>
                </div>
                <div className="feature">
                  <span className="feature-icon">❄️</span>
                  <span>Snow Conditions</span>
                </div>
                <div className="feature">
                  <span className="feature-icon">🚂</span>
                  <span>Travel Times</span>
                </div>
                <div className="feature">
                  <span className="feature-icon">🤖</span>
                  <span>AI Insights</span>
                </div>
              </div>

              <button
                className="get-recommendations-btn"
                onClick={handleGetRecommendations}
                disabled={loading || apiStatus?.status === 'offline'}
              >
                {loading ? 'Analyzing...' : 'Get Weekend Recommendations'}
              </button>
            </div>
          </div>
        )}

        {loading && (
          <LoadingSpinner
            message="Analyzing weather, snow conditions, and transport options for 29 Magic Pass resorts..."
            progress={progress}
          />
        )}

        {error && (
          <div className="error-container">
            <div className="error-message">
              <span className="error-icon">⚠️</span>
              <p>{error}</p>
            </div>
            <button className="retry-btn" onClick={handleGetRecommendations}>
              Try Again
            </button>
          </div>
        )}

        {recommendations && !loading && (
          <div className="recommendations-section">
            <div className="recommendations-header">
              <h2>Your Weekend Recommendations</h2>
              <button
                className="refresh-btn"
                onClick={handleGetRecommendations}
                disabled={loading}
              >
                🔄 Refresh
              </button>
            </div>

            <AISummary summary={aiSummary} />

            <div className="recommendations-grid">
              {displayedRecommendations?.map((rec, index) => (
                <RecommendationCard
                  key={rec.resort.id}
                  recommendation={rec}
                  rank={index + 1}
                />
              ))}
            </div>

            {recommendations.length > 5 && !showAll && (
              <button
                className="show-more-btn"
                onClick={() => setShowAll(true)}
              >
                Show {recommendations.length - 5} More Resorts
              </button>
            )}

            {showAll && (
              <button
                className="show-more-btn"
                onClick={() => setShowAll(false)}
              >
                Show Less
              </button>
            )}
          </div>
        )}
      </main>

      <footer className="footer">
        <p>Magic Pass Resort Picker | Data from OpenWeather, Swiss Transport API, and snow-forecast.com</p>
      </footer>
    </div>
  );
}

export default App;
