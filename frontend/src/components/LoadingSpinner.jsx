import React from 'react';
import { PROGRESS_STAGES, STAGE_ORDER } from '../hooks/useSSERecommendations';

export default function LoadingSpinner({ message = 'Loading...', progress = null }) {
  // If no progress data, show simple spinner
  if (!progress) {
    return (
      <div className="loading-container">
        <div className="loading-spinner">
          <div className="spinner"></div>
        </div>
        <p className="loading-message">{message}</p>
      </div>
    );
  }

  const currentStage = progress.stage;
  const currentStageIndex = STAGE_ORDER.indexOf(currentStage);
  const stageInfo = PROGRESS_STAGES[currentStage] || { icon: '⏳', label: 'Processing' };

  // Calculate progress percentage
  const hasDetailedProgress = progress.total > 0;
  const progressPercent = hasDetailedProgress
    ? Math.round((progress.current / progress.total) * 100)
    : 0;

  return (
    <div className="loading-container">
      {/* Stage indicators */}
      <div className="progress-stages">
        {STAGE_ORDER.slice(0, -1).map((stage, index) => {
          const info = PROGRESS_STAGES[stage];
          const isComplete = index < currentStageIndex;
          const isActive = index === currentStageIndex;
          const isPending = index > currentStageIndex;

          return (
            <div
              key={stage}
              className={`progress-stage ${isComplete ? 'complete' : ''} ${isActive ? 'active' : ''} ${isPending ? 'pending' : ''}`}
            >
              <span className="stage-icon">{info.icon}</span>
              <span className="stage-label">{info.label}</span>
            </div>
          );
        })}
      </div>

      {/* Current stage display */}
      <div className="current-stage">
        <span className="current-stage-icon">{stageInfo.icon}</span>
        <p className="loading-message">{progress.message}</p>
      </div>

      {/* Progress bar (only shown when we have detailed progress) */}
      {hasDetailedProgress && (
        <div className="progress-bar-container">
          <div className="progress-bar-track">
            <div
              className="progress-bar-fill"
              style={{ width: `${progressPercent}%` }}
            />
          </div>
          <span className="progress-text">{progress.current} / {progress.total}</span>
        </div>
      )}
    </div>
  );
}
