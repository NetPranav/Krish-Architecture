'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import TopBar from '@/app/components/ui/TopBar';

const waterUsage = [
  { day: 'M', value: 35 },
  { day: 'T', value: 50 },
  { day: 'W', value: 30 },
  { day: 'T', value: 45 },
  { day: 'F', value: 25 },
  { day: 'S', value: 60 },
  { day: 'S', value: 80 },
];

export default function IrrigationHubPage() {
  const router = useRouter();
  const [pumpRunning, setPumpRunning] = useState(false);

  const handlePump = () => {
    setPumpRunning(true);
    setTimeout(() => setPumpRunning(false), 5000);
  };

  return (
    <div className="dashboard-page">
      <TopBar location="Nashik, MH" weather="" />

      <div style={{ padding: '4px 16px 8px' }}>
        <h1 className="apmc-title">Irrigation Hub</h1>
      </div>

      {/* Optimal Watering Window */}
      <div className="irr-window-card">
        <div className="irr-window-header">
          <div className="irr-window-icon">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#1565C0" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z" />
            </svg>
          </div>
          <div>
            <h2 className="irr-window-title">Optimal Watering Window</h2>
            <p className="irr-window-text">
              Soil moisture in Zone A is dropping. Rain is not expected for the next 48 hours. Recommended action: Run pump for 2 hours.
            </p>
          </div>
        </div>
        <button
          className={`irr-pump-btn ${pumpRunning ? 'irr-pump-btn--active' : ''}`}
          onClick={handlePump}
          disabled={pumpRunning}
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            {pumpRunning ? (
              <><rect x="6" y="4" width="4" height="16" /><rect x="14" y="4" width="4" height="16" /></>
            ) : (
              <><circle cx="12" cy="12" r="10" /><polyline points="12 6 12 12 16 14" /></>
            )}
          </svg>
          {pumpRunning ? 'Pump Running...' : 'Start Pump Now'}
        </button>
      </div>

      {/* Power Schedule */}
      <div className="section-card">
        <h2 className="section-title">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#F9A825" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
          </svg>
          Power Schedule
        </h2>
        <div className="power-outage-card">
          <div>
            <p className="power-outage-label">Upcoming Outage</p>
            <p className="power-outage-time">14:00 - 16:00</p>
          </div>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#C62828" strokeWidth="2">
            <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
            <line x1="12" y1="9" x2="12" y2="13" /><line x1="12" y1="17" x2="12.01" y2="17" />
          </svg>
        </div>
        <p className="power-note">Plan irrigation around these hours.</p>
      </div>

      {/* Active Alerts */}
      <div className="section-card">
        <h2 className="section-title">Active Alerts</h2>

        <div className="irr-alert-item irr-alert-item--danger">
          <div className="irr-alert-icon irr-alert-icon--danger">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#C62828" strokeWidth="2">
              <path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z" />
            </svg>
          </div>
          <div>
            <p className="irr-alert-title">Soil is Dry in Zone B</p>
            <p className="irr-alert-desc">Moisture level critically low at 12%.</p>
          </div>
        </div>

        <div className="irr-alert-item irr-alert-item--warning">
          <div className="irr-alert-icon irr-alert-icon--warning">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#E65100" strokeWidth="2">
              <circle cx="12" cy="12" r="10" /><line x1="12" y1="8" x2="12" y2="12" /><line x1="12" y1="16" x2="12.01" y2="16" />
            </svg>
          </div>
          <div>
            <p className="irr-alert-title">Valve 3 Maintenance</p>
            <p className="irr-alert-desc">Scheduled check required next week.</p>
          </div>
        </div>
      </div>

      {/* Water Usage */}
      <div className="section-card">
        <div className="trend-header">
          <h2 className="section-title" style={{ margin: 0 }}>Water Usage</h2>
          <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--green-800)' }}>Last 7 Days</span>
        </div>
        <div className="trend-chart">
          <div className="trend-bars">
            {waterUsage.map((d, i) => {
              const isToday = i === waterUsage.length - 1;
              return (
                <div key={i} className="trend-bar-col">
                  <div
                    className={`trend-bar ${isToday ? 'trend-bar--today' : ''}`}
                    style={{ height: `${d.value}px`, width: 28 }}
                  />
                  <span className="trend-day-label">{d.day}</span>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Back to Alerts */}
      <div style={{ padding: '0 16px 16px' }}>
        <button className="view-map-btn" onClick={() => router.push('/alerts')}>
          ← Back to All Alerts
        </button>
      </div>
    </div>
  );
}
