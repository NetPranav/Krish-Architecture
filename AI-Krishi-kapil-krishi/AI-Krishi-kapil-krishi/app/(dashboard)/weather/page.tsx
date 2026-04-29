'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import TopBar from '@/app/components/ui/TopBar';
import StatusBanner from '@/app/components/ui/StatusBanner';

const forecastTimeline = ['Now', '+2h', '+4h', 'Fri', 'Sat', 'Sun'];

const hourlyForecast = [
  { time: 'Now', icon: '⛅', temp: '32°' },
  { time: '14:00', icon: '☀️', temp: '34°' },
  { time: '15:00', icon: '☀️', temp: '35°' },
];

const weeklyForecast = [
  { day: 'Today', rain: '10%', icon: '☀️', low: '22°', high: '35°', highlight: false },
  { day: 'Thu', rain: '20%', icon: '⛅', low: '23°', high: '33°', highlight: false },
  { day: 'Fri', rain: '90%', icon: '🌧️', low: '20°', high: '28°', highlight: true },
  { day: 'Sat', rain: '60%', icon: '🌦️', low: '21°', high: '29°', highlight: false },
  { day: 'Sun', rain: '', icon: '☀️', low: '22°', high: '32°', highlight: false },
];

export default function WeatherPage() {
  const router = useRouter();
  const [activeTimeSlot, setActiveTimeSlot] = useState('Fri');

  return (
    <div className="dashboard-page">
      <TopBar location="Nashik, MH" weather="28°C, Partly Cloudy" />

      {/* Weather Warning Banner */}
      <StatusBanner
        type="warning"
        title="Heavy Rain predicted for Friday."
        message="Secure vulnerable equipment."
      />

      {/* Current Conditions */}
      <div className="section-card">
        <div className="weather-current-header">
          <div>
            <h2 className="section-title" style={{ marginBottom: 4 }}>Current Conditions</h2>
            <p className="weather-temp-large">32°</p>
            <p className="weather-realfeel">RealFeel 35°</p>
            <p className="weather-desc">⛅ Partly Cloudy</p>
          </div>
          <div className="weather-safe-badge">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#2E7D32" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
            </svg>
            Safe from Frost
          </div>
        </div>

        <div className="weather-metrics-row">
          <div className="weather-metric">
            <p className="weather-metric-label">Humidity</p>
            <p className="weather-metric-value">65%</p>
          </div>
          <div className="weather-metric">
            <p className="weather-metric-label">Wind</p>
            <p className="weather-metric-value">12 km/h</p>
            <p className="weather-metric-sub">NE</p>
          </div>
          <div className="weather-metric">
            <p className="weather-metric-label">Soil Moisture</p>
            <p className="weather-metric-value" style={{ color: 'var(--green-800)' }}>Optimal</p>
          </div>
        </div>
      </div>

      {/* Rain Probability */}
      <div className="section-card">
        <h2 className="section-title">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--gray-700)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z" />
          </svg>
          Rain Probability
        </h2>
        <div className="rain-timeline">
          {forecastTimeline.map((slot) => (
            <button
              key={slot}
              className={`rain-slot ${activeTimeSlot === slot ? 'rain-slot--active' : ''}`}
              onClick={() => setActiveTimeSlot(slot)}
            >
              {slot}
            </button>
          ))}
        </div>
      </div>

      {/* 48-Hour Forecast */}
      <div className="section-card section-card--green">
        <h2 className="section-title">48-Hour Forecast</h2>
        <div className="hourly-forecast">
          {hourlyForecast.map((h) => (
            <div key={h.time} className="hourly-item">
              <p className="hourly-time">{h.time}</p>
              <p className="hourly-icon">{h.icon}</p>
              <p className="hourly-temp">{h.temp}</p>
            </div>
          ))}
        </div>
      </div>

      {/* 7-Day Outlook */}
      <div className="section-card">
        <h2 className="section-title">7-Day Outlook</h2>
        <div className="weekly-forecast">
          {weeklyForecast.map((d) => (
            <div
              key={d.day}
              className={`weekly-row ${d.highlight ? 'weekly-row--highlight' : ''}`}
            >
              <span className={`weekly-day ${d.highlight ? 'weekly-day--alert' : ''}`}>{d.day}</span>
              {d.rain ? (
                <span className={`weekly-rain ${d.highlight ? 'weekly-rain--alert' : ''}`}>
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z" />
                  </svg>
                  {d.rain}
                </span>
              ) : (
                <span className="weekly-rain" />
              )}
              <span className="weekly-icon">{d.icon}</span>
              <span className="weekly-low">{d.low}</span>
              <span className="weekly-high">{d.high}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Link to Historical Weather & Yield */}
      <div style={{ padding: '0 16px 16px' }}>
        <button
          className="product-cta-btn product-cta-btn--primary"
          onClick={() => router.push('/weather/history')}
        >
          📊 View Historical Weather & Yield
        </button>
      </div>
    </div>
  );
}
