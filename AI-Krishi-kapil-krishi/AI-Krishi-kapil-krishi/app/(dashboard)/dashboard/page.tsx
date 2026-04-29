'use client';

import { useState } from 'react';
import Link from 'next/link';
import TopBar from '@/app/components/ui/TopBar';
import StatusBanner from '@/app/components/ui/StatusBanner';

const actions = [
  { id: 1, text: 'Inspect Plot A for pests', done: false },
  { id: 2, text: 'Apply fertilizer to Plot C', done: true },
  { id: 3, text: 'Check drip lines in greenhouse', done: false },
];

export default function HomePage() {
  const [todoList, setTodoList] = useState(actions);

  const toggleAction = (id: number) => {
    setTodoList((prev) =>
      prev.map((a) => (a.id === id ? { ...a, done: !a.done } : a))
    );
  };

  return (
    <div className="dashboard-page">
      <TopBar location="Nashik, MH" weather="28°C, Partly Cloudy" />

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
          <p className="metric-value">28°C</p>
          <p className="metric-sub">Rain: 10%</p>
        </Link>

        <div className="metric-card">
          <div className="metric-card-header">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#1565C0" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z" />
            </svg>
            <span className="metric-label" style={{ color: '#1565C0' }}>Moisture</span>
          </div>
          <p className="metric-value">42%</p>
          <div className="moisture-bar">
            <div className="moisture-fill" style={{ width: '42%' }} />
          </div>
        </div>
      </div>

      {/* Soybeans Price + Crop Alert */}
      <div className="metric-grid">
        <div className="metric-card">
          <div className="metric-card-header">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#2E7D32" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="12" y1="1" x2="12" y2="23" />
              <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" />
            </svg>
            <span className="metric-label" style={{ color: 'var(--green-800)' }}>Soybeans</span>
          </div>
          <p className="metric-value">₹4,200/qtl</p>
          <p className="metric-sub metric-positive">📈 +1.2%</p>
        </div>

        <div className="metric-card metric-card--alert">
          <div className="metric-card-header">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#C62828" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
              <line x1="12" y1="9" x2="12" y2="13" />
              <line x1="12" y1="17" x2="12.01" y2="17" />
            </svg>
            <span className="metric-label" style={{ color: '#C62828' }}>Crop Alert</span>
          </div>
          <p className="metric-alert-title">Watering due tomorrow</p>
          <p className="metric-sub">Plot B - Tomatoes</p>
        </div>
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
        <h3 className="ai-insight-title">Optimal Irrigation Window</h3>
        <p className="ai-insight-text">
          Moisture dropping in Plot B. Turning on pump now will save 15% water and ensure deep root penetration.
        </p>
        <button className="btn-action" id="btn-turn-pump">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="10" />
            <polyline points="12 6 12 12 16 14" />
          </svg>
          Turn on Pump
        </button>
      </div>

      {/* FAB Chat button */}
      <button className="fab-chat" aria-label="AI Chat" id="btn-ai-chat">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
        </svg>
      </button>
    </div>
  );
}
