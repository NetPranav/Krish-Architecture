'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import TopBar from '@/app/components/ui/TopBar';
import StatusBanner from '@/app/components/ui/StatusBanner';
import { getDashboard, controlPump } from '@/app/lib/api';

// Fallback data when backend is unreachable
const FALLBACK = {
  weather: { temperature: 28, description: 'Partly Cloudy', rain_probability: 10, location: 'Nashik, MH' },
  moisture: { value: 42, status: 'normal' },
  market: { commodity: 'Soybeans', price: 4200, unit: '₹/qtl', change_pct: 1.2 },
  alerts: [{ title: 'Watering due tomorrow', desc: 'Plot B - Tomatoes', severity: 'warning' }],
  actions: [
    { id: 1, text: 'Inspect Plot A for pests', done: false },
    { id: 2, text: 'Apply fertilizer to Plot C', done: true },
    { id: 3, text: 'Check drip lines in greenhouse', done: false },
  ],
  ai_insight: { title: 'Optimal Irrigation Window', text: 'Moisture dropping in Plot B. Turning on pump now will save 15% water.' },
};

export default function HomePage() {
  const [data, setData] = useState<any>(null);
  const [todoList, setTodoList] = useState(FALLBACK.actions);
  const [loading, setLoading] = useState(true);
  const [pumpLoading, setPumpLoading] = useState(false);

  useEffect(() => {
    getDashboard()
      .then((res) => {
        if (res) {
          setData(res);
          if (res.actions) setTodoList(res.actions);
        }
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const d = data || FALLBACK;

  const toggleAction = (id: number) => {
    setTodoList((prev) =>
      prev.map((a) => (a.id === id ? { ...a, done: !a.done } : a))
    );
  };

  const handlePump = async () => {
    setPumpLoading(true);
    try {
      await controlPump('start');
    } catch {}
    setPumpLoading(false);
  };

  return (
    <div className="dashboard-page">
      <TopBar
        location={d.weather?.location || 'Nashik, MH'}
        weather={`${d.weather?.temperature || 28}°C, ${d.weather?.description || 'Partly Cloudy'}`}
      />

      {/* Field Status Banner */}
      <StatusBanner
        type="success"
        title="Field Status: Healthy"
        message="All vital metrics are stable."
      />

      {/* Weather + Moisture Cards */}
      <div className="metric-grid">
        <Link href="/weather" className="metric-card">
          <div className="metric-card-header">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#2E7D32" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="5" />
              <line x1="12" y1="1" x2="12" y2="3" />
              <line x1="12" y1="21" x2="12" y2="23" />
              <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" />
              <line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
              <line x1="1" y1="12" x2="3" y2="12" />
              <line x1="21" y1="12" x2="23" y2="12" />
              <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" />
              <line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
            </svg>
            <span className="metric-label" style={{ color: 'var(--green-800)' }}>Weather</span>
          </div>
          <p className="metric-value">{d.weather?.temperature || 28}°C</p>
          <p className="metric-sub">Rain: {d.weather?.rain_probability || 10}%</p>
        </Link>

        <div className="metric-card">
          <div className="metric-card-header">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#1565C0" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z" />
            </svg>
            <span className="metric-label" style={{ color: '#1565C0' }}>Moisture</span>
          </div>
          <p className="metric-value">{d.moisture?.value || 42}%</p>
          <div className="moisture-bar">
            <div className="moisture-fill" style={{ width: `${d.moisture?.value || 42}%` }} />
          </div>
        </div>
      </div>

      {/* Market Price + Crop Alert */}
      <div className="metric-grid">
        <Link href="/mandi" className="metric-card">
          <div className="metric-card-header">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#2E7D32" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="12" y1="1" x2="12" y2="23" />
              <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" />
            </svg>
            <span className="metric-label" style={{ color: 'var(--green-800)' }}>{d.market?.commodity || 'Soybeans'}</span>
          </div>
          <p className="metric-value">₹{(d.market?.price || 4200).toLocaleString()}/qtl</p>
          <p className={`metric-sub ${(d.market?.change_pct || 0) >= 0 ? 'metric-positive' : 'metric-negative'}`}>
            {(d.market?.change_pct || 0) >= 0 ? '📈' : '📉'} {d.market?.change_pct > 0 ? '+' : ''}{d.market?.change_pct || 1.2}%
          </p>
        </Link>

        <Link href="/alerts" className="metric-card metric-card--alert">
          <div className="metric-card-header">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#C62828" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
              <line x1="12" y1="9" x2="12" y2="13" />
              <line x1="12" y1="17" x2="12.01" y2="17" />
            </svg>
            <span className="metric-label" style={{ color: '#C62828' }}>
              {d.alerts_count ? `${d.alerts_count} Alerts` : 'Crop Alert'}
            </span>
          </div>
          <p className="metric-alert-title">{d.alerts?.[0]?.title || 'Watering due tomorrow'}</p>
          <p className="metric-sub">{d.alerts?.[0]?.desc || 'Plot B - Tomatoes'}</p>
        </Link>
      </div>

      {/* Quick Tools */}
      <div className="metric-grid" style={{ marginBottom: 20 }}>
        <Link href="/scanner/capture" className="metric-card" style={{ display: 'flex', alignItems: 'center', gap: 12, padding: 16 }}>
          <div style={{ background: '#E8F5E9', padding: 12, borderRadius: 12, color: '#2E7D32' }}>
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z" />
              <circle cx="12" cy="13" r="4" />
            </svg>
          </div>
          <div>
            <p className="metric-label" style={{ fontSize: 14, color: '#1B5E20' }}>Scan Crop</p>
            <p style={{ fontSize: 11, color: '#666', marginTop: 2 }}>Detect disease</p>
          </div>
        </Link>
        <Link href="/scanner/capture" className="metric-card" style={{ display: 'flex', alignItems: 'center', gap: 12, padding: 16 }}>
          <div style={{ background: '#FFF8E1', padding: 12, borderRadius: 12, color: '#F9A825' }}>
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" />
            </svg>
          </div>
          <div>
            <p className="metric-label" style={{ fontSize: 14, color: '#F9A825' }}>Check Soil</p>
            <p style={{ fontSize: 11, color: '#666', marginTop: 2 }}>Analyze soil type</p>
          </div>
        </Link>
      </div>

      {/* Today's Actions */}
      <div className="section-card">
        <h2 className="section-title">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#2E7D32" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
            <polyline points="22 4 12 14.01 9 11.01" />
          </svg>
          Today&apos;s Actions
        </h2>
        <ul className="action-list">
          {todoList.map((action) => (
            <li
              key={action.id}
              className={`action-item ${action.done ? 'action-item--done' : ''}`}
              onClick={() => toggleAction(action.id)}
            >
              <span className={`action-checkbox ${action.done ? 'action-checkbox--checked' : ''}`}>
                {action.done && (
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                    <polyline points="20 6 9 17 4 12" />
                  </svg>
                )}
              </span>
              <span className="action-text">{action.text}</span>
            </li>
          ))}
        </ul>
      </div>

      {/* AI Insight Card */}
      <div className="ai-insight-card">
        <div className="ai-insight-badge">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#4CAF50" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
          </svg>
          AI INSIGHT
        </div>
        <h3 className="ai-insight-title">{d.ai_insight?.title || 'Optimal Irrigation Window'}</h3>
        <p className="ai-insight-text">{d.ai_insight?.text || 'Moisture dropping in Plot B.'}</p>
        <button className="btn-action" id="btn-turn-pump" onClick={handlePump} disabled={pumpLoading}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="10" />
            <polyline points="12 6 12 12 16 14" />
          </svg>
          {pumpLoading ? 'Starting...' : 'Turn on Pump'}
        </button>
      </div>

      {/* FAB Chat button */}
      <Link href="/mitra" className="fab-chat" aria-label="AI Chat" id="btn-ai-chat">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
        </svg>
      </Link>

      {/* Live data indicator */}
      {data && (
        <div className="live-indicator">
          <span className="live-dot" />
          Live from backend
        </div>
      )}
    </div>
  );
}
