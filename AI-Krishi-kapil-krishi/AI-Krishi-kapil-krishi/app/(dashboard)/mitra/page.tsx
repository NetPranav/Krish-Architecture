'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';

const quickActions = [
  { label: 'Check Mandi Prices', icon: '🏪', route: '/mandi' },
  { label: 'Weather Forecast', icon: '☁️', route: '/weather' },
  { label: 'Scan My Crop', icon: '🌿', route: '/scanner/capture' },
  { label: 'Irrigation Status', icon: '💧', route: '/alerts/irrigation' },
];

const sampleResponses: Record<string, { en: string; hi: string }> = {
  default: {
    en: '"Should I water the field today?"',
    hi: '"क्या मुझे आज खेत में पानी देना चाहिए?"',
  },
  listening: {
    en: 'Listening...',
    hi: 'सुन रहा हूँ...',
  },
};

export default function MitraAIPage() {
  const router = useRouter();
  const [isListening, setIsListening] = useState(false);
  const [bars, setBars] = useState([3, 5, 7, 5, 3]);

  // Animate voice bars when listening
  useEffect(() => {
    if (!isListening) return;
    const interval = setInterval(() => {
      setBars(prev => prev.map(() => Math.floor(Math.random() * 8) + 2));
    }, 150);
    return () => clearInterval(interval);
  }, [isListening]);

  const toggleListening = useCallback(() => {
    setIsListening(prev => !prev);
  }, []);

  return (
    <div className="mitra-page">
      {/* Header */}
      <div className="mitra-header">
        <div className="mitra-logo">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#2E7D32" strokeWidth="2.5">
            <line x1="4" y1="8" x2="4" y2="16" /><line x1="8" y1="4" x2="8" y2="20" />
            <line x1="12" y1="6" x2="12" y2="18" /><line x1="16" y1="4" x2="16" y2="20" />
            <line x1="20" y1="8" x2="20" y2="16" />
          </svg>
          <span className="mitra-brand">Mitra AI</span>
        </div>
        <button className="mitra-close-btn" onClick={() => router.back()} aria-label="Close">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="var(--gray-700)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
          </svg>
        </button>
      </div>

      {/* Speech Bubble */}
      <div className="mitra-content">
        <div className="mitra-bubble">
          {isListening && (
            <div className="mitra-listening-badge">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#2E7D32" strokeWidth="2.5">
                <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" />
                <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
              </svg>
              Listening...
            </div>
          )}
          <p className="mitra-prompt-en">{sampleResponses.default.en}</p>
          <p className="mitra-prompt-hi">{sampleResponses.default.hi}</p>
        </div>
      </div>

      {/* Voice Bars */}
      <div className="mitra-voice-section">
        <div className="mitra-voice-bars">
          {bars.map((h, i) => (
            <div
              key={i}
              className={`mitra-bar ${isListening ? 'mitra-bar--active' : ''}`}
              style={{ height: isListening ? `${h * 5}px` : `${(i === 2 ? 7 : i === 1 || i === 3 ? 5 : 3) * 4}px` }}
            />
          ))}
        </div>

        {/* Mic Button */}
        <button
          className={`mitra-mic-btn ${isListening ? 'mitra-mic-btn--active' : ''}`}
          onClick={toggleListening}
          aria-label={isListening ? 'Stop listening' : 'Start listening'}
        >
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" />
            <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
            <line x1="12" y1="19" x2="12" y2="23" />
            <line x1="8" y1="23" x2="16" y2="23" />
          </svg>
        </button>
      </div>

      {/* Quick Actions */}
      <div className="mitra-quick-actions">
        {quickActions.map((action) => (
          <button
            key={action.label}
            className="mitra-quick-chip"
            onClick={() => router.push(action.route)}
          >
            <span>{action.icon}</span>
            {action.label}
          </button>
        ))}
      </div>
    </div>
  );
}
