import { useState, useCallback } from 'react';

const API_BASE_URL = 'http://localhost:8000';

export const PROGRESS_STAGES = {
  loading_resorts: { icon: '📍', label: 'Loading Resorts' },
  fetching_weather: { icon: '☀️', label: 'Weather Data' },
  scraping_snow: { icon: '❄️', label: 'Snow Conditions' },
  fetching_transport: { icon: '🚂', label: 'Transport' },
  scoring: { icon: '📊', label: 'Scoring' },
  generating_ai: { icon: '🤖', label: 'AI Summary' },
  complete: { icon: '✅', label: 'Complete' },
};

export const STAGE_ORDER = [
  'loading_resorts',
  'fetching_weather',
  'scraping_snow',
  'fetching_transport',
  'scoring',
  'generating_ai',
  'complete',
];

export function useSSERecommendations() {
  const [recommendations, setRecommendations] = useState(null);
  const [aiSummary, setAiSummary] = useState('');
  const [targetWeekend, setTargetWeekend] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [progress, setProgress] = useState(null);

  const fetchRecommendations = useCallback(async (startLocation = 'Geneva', targetDate = null, numRecommendations = 10) => {
    setLoading(true);
    setError(null);
    setRecommendations(null);
    setAiSummary('');
    setTargetWeekend('');
    setProgress(null);

    try {
      const response = await fetch(`${API_BASE_URL}/api/recommendations/stream`, {
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
        const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
        throw new Error(errorData.detail || 'Failed to get recommendations');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();

        if (done) {
          break;
        }

        buffer += decoder.decode(value, { stream: true });

        // Process complete SSE messages
        const lines = buffer.split('\n');
        buffer = lines.pop() || ''; // Keep incomplete line in buffer

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6);
            if (data) {
              try {
                const parsed = JSON.parse(data);

                if (parsed.type === 'progress') {
                  setProgress(parsed.data);
                } else if (parsed.type === 'result') {
                  setRecommendations(parsed.data.recommendations);
                  setAiSummary(parsed.data.ai_summary);
                  setTargetWeekend(parsed.data.target_weekend);
                } else if (parsed.type === 'error') {
                  throw new Error(parsed.data.message);
                }
              } catch (parseError) {
                console.error('Failed to parse SSE data:', parseError, data);
              }
            }
          }
        }
      }
    } catch (err) {
      setError(err.message || 'Failed to get recommendations. Please try again.');
      console.error('Error fetching recommendations:', err);
    } finally {
      setLoading(false);
      setProgress(null);
    }
  }, []);

  return {
    recommendations,
    aiSummary,
    targetWeekend,
    loading,
    error,
    progress,
    fetchRecommendations,
  };
}
