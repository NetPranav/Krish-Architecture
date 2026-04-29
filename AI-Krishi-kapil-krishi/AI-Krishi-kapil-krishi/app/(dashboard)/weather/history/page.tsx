'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import TopBar from '@/app/components/ui/TopBar';

const rainfallData = [
  { month: 'Jan', value: 20 }, { month: 'Feb', value: 15 },
  { month: 'Mar', value: 25 }, { month: 'Apr', value: 35 },
  { month: 'May', value: 80 }, { month: 'Jun', value: 60 },
  { month: 'Jul', value: 50 },
];

const weatherContext = [
  { label: 'This Month', value: '145 mm', change: '+15%', color: '#2E7D32' },
  { label: 'Same Month Last Year', value: '126 mm', change: 'Avg', color: '#757575' },
];

export default function WeatherHistoryPage() {
  const router = useRouter();
  const [fieldZone, setFieldZone] = useState('All Field Zones');
  const [crop, setCrop] = useState('All Crops');

  return (
    <div className="dashboard-page">
      <TopBar location="Nashik, MH" weather="" />

      <div style={{ padding: '4px 16px 4px' }}>
        <h1 className="apmc-title">Historical Weather & Yield</h1>
        <p className="weather-hist-sub">Analyze past trends to optimize future harvests.</p>
      </div>

      {/* Filters */}
      <div className="weather-hist-filters">
        <button className="weather-hist-filter-btn">
          {fieldZone}
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
            <polyline points="6 9 12 15 18 9" />
          </svg>
        </button>
        <button className="weather-hist-filter-btn">
          {crop}
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
            <polyline points="6 9 12 15 18 9" />
          </svg>
        </button>
      </div>

      {/* AI Predicted Yield */}
      <div className="yield-prediction-card">
        <div className="yield-icon">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z" /><circle cx="12" cy="10" r="3" />
          </svg>
        </div>
        <p className="yield-label">AI PREDICTED YIELD (CURRENT SEASON)</p>
        <p className="yield-value">4.2 <span className="yield-unit">Tons/Acre</span></p>
        <p className="yield-desc">
          Expected +12% increase compared to 5-year average, driven by optimal early-season rainfall.
        </p>
        <button className="yield-detail-btn" onClick={() => router.push('/weather')}>
          View Detail →
        </button>
      </div>

      {/* Yield vs Rainfall Chart */}
      <div className="section-card">
        <div className="chart-header">
          <div>
            <h2 style={{ fontSize: 16, fontWeight: 700, color: 'var(--gray-900)' }}>Yield vs. Rainfall (2018-2023)</h2>
            <p className="chart-sub">Historical correlation analysis</p>
          </div>
          <button className="mitra-close-btn" style={{ width: 28, height: 28 }} aria-label="More options">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--gray-400)" strokeWidth="2">
              <circle cx="12" cy="5" r="1" /><circle cx="12" cy="12" r="1" /><circle cx="12" cy="19" r="1" />
            </svg>
          </button>
        </div>
        <div className="yield-chart-placeholder">
          <svg width="120" height="60" viewBox="0 0 120 60" fill="none">
            <path d="M10 50 Q30 20 50 35 T90 15 L110 20" stroke="var(--green-800)" strokeWidth="2.5" fill="none" strokeLinecap="round" />
            <path d="M10 45 Q35 30 55 40 T95 25 L110 30" stroke="var(--gray-400)" strokeWidth="2" fill="none" strokeDasharray="4 3" strokeLinecap="round" />
          </svg>
          <p className="chart-placeholder-text">Interactive Chart Rendered Here</p>
        </div>
        <div className="yield-legend">
          <span className="yield-legend-item">
            <span className="yield-legend-dot" style={{ background: 'var(--green-800)' }} />
            Avg Yield (Tons)
          </span>
          <span className="yield-legend-item">
            <span className="yield-legend-dot" style={{ background: 'var(--gray-400)' }} />
            Rainfall (mm)
          </span>
        </div>
      </div>

      {/* Monthly Rainfall Spikes */}
      <div className="section-card">
        <div className="trend-header">
          <h2 className="section-title" style={{ margin: 0 }}>Monthly Rainfall Spikes</h2>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#1565C0" strokeWidth="2">
            <path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z" />
          </svg>
        </div>
        <div className="trend-chart">
          <div className="trend-bars" style={{ height: 110 }}>
            {rainfallData.map((d, i) => {
              const isHighlight = d.month === 'May';
              return (
                <div key={d.month} className="trend-bar-col">
                  <div
                    className={`trend-bar ${isHighlight ? 'trend-bar--today' : ''}`}
                    style={{ height: `${d.value}px`, width: 24 }}
                  >
                    {isHighlight && (
                      <span className="trend-today-label" style={{ color: '#1565C0' }}>
                        {d.month}
                      </span>
                    )}
                  </div>
                  {!isHighlight && <span className="trend-day-label">{d.month}</span>}
                </div>
              );
            })}
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', paddingTop: 4 }}>
            <span style={{ fontSize: 10, color: 'var(--gray-400)' }}>Jan</span>
            <span style={{ fontSize: 10, color: 'var(--gray-400)' }}>Jul</span>
          </div>
        </div>
      </div>

      {/* Weather Context */}
      <div style={{ padding: '8px 16px 4px' }}>
        <h2 className="mandi-section-title">Weather Context</h2>
      </div>

      {weatherContext.map((item) => (
        <div key={item.label} className="weather-context-card">
          <div className="weather-context-icon">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--gray-500)" strokeWidth="2">
              <path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z" />
            </svg>
          </div>
          <div style={{ flex: 1 }}>
            <p className="weather-context-label">{item.label}</p>
            <p className="weather-context-value">
              {item.value}
              <span className="weather-context-change" style={{ color: item.color }}> {item.change}</span>
            </p>
          </div>
          <div className="weather-context-bar" style={{ background: item.color === '#2E7D32' ? '#E8F5E9' : '#F5F5F5' }}>
            <div style={{ width: '70%', height: '100%', borderRadius: 4, background: item.color, opacity: 0.6 }} />
          </div>
        </div>
      ))}

      {/* Back to Weather */}
      <div style={{ padding: '8px 16px 16px' }}>
        <button className="view-map-btn" onClick={() => router.push('/weather')}>
          ← Back to Weather
        </button>
      </div>
    </div>
  );
}
