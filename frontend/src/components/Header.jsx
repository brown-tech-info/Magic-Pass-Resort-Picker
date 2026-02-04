import React from 'react';

export default function Header({ targetWeekend }) {
  return (
    <header className="header">
      <div className="header-content">
        <h1 className="header-title">Magic Pass Resort Picker</h1>
        <p className="header-subtitle">
          Find the best ski conditions for your weekend from Geneva
        </p>
        {targetWeekend && (
          <div className="weekend-badge">
            Weekend of {targetWeekend}
          </div>
        )}
      </div>
    </header>
  );
}
