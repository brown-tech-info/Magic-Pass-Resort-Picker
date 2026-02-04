const API_BASE_URL = 'http://localhost:8000';

export async function getResorts() {
  const response = await fetch(`${API_BASE_URL}/api/resorts`);
  if (!response.ok) {
    throw new Error('Failed to fetch resorts');
  }
  return response.json();
}

export async function getRecommendations(startLocation = 'Geneva', targetDate = null, numRecommendations = 5) {
  const response = await fetch(`${API_BASE_URL}/api/recommendations`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      start_location: startLocation,
      target_date: targetDate,
      num_recommendations: numRecommendations,
    }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || 'Failed to get recommendations');
  }

  return response.json();
}

export async function getResortDetails(resortId, targetDate = null) {
  const params = new URLSearchParams();
  if (targetDate) {
    params.append('target_date', targetDate);
  }

  const url = `${API_BASE_URL}/api/recommendations/${resortId}${params.toString() ? '?' + params.toString() : ''}`;
  const response = await fetch(url);

  if (!response.ok) {
    throw new Error('Failed to fetch resort details');
  }

  return response.json();
}

export async function getHealthStatus() {
  const response = await fetch(`${API_BASE_URL}/health`);
  if (!response.ok) {
    throw new Error('Failed to check health');
  }
  return response.json();
}
