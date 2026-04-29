'use client';

import { useState } from 'react';

const nodes = [
  {
    id: 'alpha',
    name: 'Node Alpha',
    location: 'North Field Sector',
    battery: 82,
    signal: 'Strong',
    signalColor: '#2E7D32',
    online: true,
  },
  {
    id: 'beta',
    name: 'Node Beta',
    location: 'East Orchard',
    battery: 24,
    signal: 'Good',
    signalColor: '#2E7D32',
    online: true,
  },
];

export default function ScannerPage() {
  const [syncing, setSyncing] = useState(false);

  const handleSync = () => {
    setSyncing(true);
    setTimeout(() => setSyncing(false), 2000);
  };

  // SVG arc helper for circular gauges
  const describeArc = (cx: number, cy: number, r: number, startAngle: number, endAngle: number) => {
    const start = polarToCartesian(cx, cy, r, endAngle);
    const end = polarToCartesian(cx, cy, r, startAngle);
    const largeArcFlag = endAngle - startAngle <= 180 ? '0' : '1';
    return `M ${start.x} ${start.y} A ${r} ${r} 0 ${largeArcFlag} 0 ${end.x} ${end.y}`;
  };

  const polarToCartesian = (cx: number, cy: number, r: number, angleDeg: number) => {
    const angleRad = ((angleDeg - 90) * Math.PI) / 180;
    return { x: cx + r * Math.cos(angleRad), y: cy + r * Math.sin(angleRad) };
  };

  return (
    <div className="dashboard-page">
      {/* Header */}
      <div className="telemetry-header">
        <h1 className="telemetry-title">Live Telemetry HUD</h1>
        <div className="telemetry-status">
          <span className="status-dot status-dot--online" />
          System Online • All nodes reporting
        </div>
        <button
          className="sync-btn"
          onClick={handleSync}
          disabled={syncing}
          id="btn-sync"
        >
          <svg
            width="16" height="16" viewBox="0 0 24 24" fill="none"
            stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
            className={syncing ? 'spin' : ''}
          >
            <polyline points="23 4 23 10 17 10" />
            <polyline points="1 20 1 14 7 14" />
            <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15" />
          </svg>
          {syncing ? 'Syncing...' : 'Sync Data'}
        </button>
      </div>

      {/* Soil Moisture Gauge */}
      <div className="section-card" style={{ textAlign: 'center' }}>
        <h2 className="section-title" style={{ justifyContent: 'center' }}>Soil Moisture</h2>
        <div className="gauge-container">
          <svg viewBox="0 0 200 200" width="180" height="180">
            {/* Background track */}
            <path
              d={describeArc(100, 100, 80, 0, 360)}
              fill="none"
              stroke="#E8E8E8"
              strokeWidth="14"
              strokeLinecap="round"
            />
            {/* Progress arc (75% = 270deg) */}
            <path
              d={describeArc(100, 100, 80, 0, 270)}
              fill="none"
              stroke="#2196F3"
              strokeWidth="14"
              strokeLinecap="round"
              className="gauge-arc"
            />
          </svg>
          <div className="gauge-center">
            <span className="gauge-value">75%</span>
            <span className="gauge-label" style={{ color: '#2E7D32' }}>Optimal</span>
          </div>
        </div>
      </div>

      {/* NPK Levels */}
      <div className="section-card" style={{ textAlign: 'center' }}>
        <h2 className="section-title" style={{ justifyContent: 'center' }}>NPK Levels</h2>
        <div className="npk-container">
          <svg viewBox="0 0 200 200" width="160" height="160">
            {/* Background */}
            <path d={describeArc(100, 100, 75, 180, 360)} fill="none" stroke="#E8E8E8" strokeWidth="16" strokeLinecap="round" />
            {/* K - Blue */}
            <path d={describeArc(100, 100, 75, 180, 225)} fill="none" stroke="#1565C0" strokeWidth="16" strokeLinecap="round" />
            {/* P - Yellow/Orange */}
            <path d={describeArc(100, 100, 75, 230, 290)} fill="none" stroke="#F9A825" strokeWidth="16" strokeLinecap="round" />
            {/* N - Green */}
            <path d={describeArc(100, 100, 75, 295, 360)} fill="none" stroke="#2E7D32" strokeWidth="16" strokeLinecap="round" />
          </svg>
          <div className="npk-legend">
            <div className="npk-item">
              <span className="npk-dot" style={{ background: '#2E7D32' }} />
              N: 45
            </div>
            <div className="npk-item">
              <span className="npk-dot" style={{ background: '#F9A825' }} />
              P: 30
            </div>
            <div className="npk-item">
              <span className="npk-dot" style={{ background: '#1565C0' }} />
              K: 25
            </div>
          </div>
        </div>
      </div>

      {/* Soil pH */}
      <div className="section-card section-card--green">
        <h2 className="section-title" style={{ justifyContent: 'center' }}>Soil pH</h2>
        <div className="ph-container">
          <div className="ph-labels">
            <span className="ph-label-text">Acidic</span>
            <span className="ph-value">6.5</span>
            <span className="ph-label-text">Alkaline</span>
          </div>
          <div className="ph-bar">
            <div className="ph-gradient" />
            <div className="ph-indicator" style={{ left: '46%' }} />
          </div>
        </div>
      </div>

      {/* Sensor Nodes */}
      {nodes.map((node) => (
        <div className="section-card node-card" key={node.id}>
          <div className="node-row">
            <div className="node-icon">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M5.12 19a7 7 0 0 1 0-14" />
                <path d="M18.88 5a7 7 0 0 1 0 14" />
                <path d="M8.46 15.54a3 3 0 0 1 0-7.08" />
                <path d="M15.54 8.46a3 3 0 0 1 0 7.08" />
                <circle cx="12" cy="12" r="1" />
              </svg>
            </div>
            <div className="node-info">
              <p className="node-name">{node.name}</p>
              <p className="node-location">{node.location}</p>
            </div>
            <div className="node-stats">
              <div className="node-stat">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                  <rect x="6" y="2" width="12" height="20" rx="2" />
                  <line x1="6" y1="18" x2="18" y2="18" />
                </svg>
                <span>{node.battery}%</span>
                <small>Battery</small>
              </div>
              <div className="node-stat">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke={node.signalColor} strokeWidth="2.5">
                  <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
                </svg>
                <span style={{ color: node.signalColor }}>{node.signal}</span>
                <small>Signal</small>
              </div>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
