'use client';

import { useRouter } from 'next/navigation';
import TopBar from '@/app/components/ui/TopBar';

const commodities = [
  { name: 'Onion', emoji: '🧅', price: 2450, unit: '/q', min: 2100, max: 2800, hot: true },
  { name: 'Tomato', emoji: '🍅', price: 1800, unit: '/q', min: 1500, max: 2100, hot: true },
  { name: 'Potato', emoji: '🥔', price: 1200, unit: '/q', min: 1000, max: 1400, hot: false },
];

const trendData = [
  { day: 'MON', value: 40 },
  { day: 'TUE', value: 45 },
  { day: 'WED', value: 50 },
  { day: 'THU', value: 48 },
  { day: 'FRI', value: 60 },
  { day: 'SAT', value: 70 },
  { day: 'SUN', value: 85 },
];

const nearbyAlternatives = [
  { name: 'Lasalgaon APMC', distance: '22 km away', price: 2350, commodity: 'Onion (Modal)' },
  { name: 'Vani Mandi', distance: '35 km away', price: 2500, commodity: 'Onion (Modal)' },
];

function TrendChart() {
  const maxVal = 100;
  const barWidth = 32;
  const gap = 12;
  const chartH = 120;

  return (
    <div className="trend-chart">
      <div className="trend-bars">
        {trendData.map((d, i) => {
          const height = (d.value / maxVal) * chartH;
          const isToday = i === trendData.length - 1;
          return (
            <div key={d.day} className="trend-bar-col">
              <div
                className={`trend-bar ${isToday ? 'trend-bar--today' : ''}`}
                style={{ height: `${height}px`, width: `${barWidth}px` }}
              >
                {isToday && (
                  <span className="trend-today-label">
                    <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="#2E7D32" strokeWidth="3">
                      <polyline points="23 6 13.5 15.5 8.5 10.5 1 18" />
                    </svg>
                    Today
                  </span>
                )}
              </div>
              <span className="trend-day-label">{d.day}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default function MandiDetailPage() {
  const router = useRouter();

  return (
    <div className="dashboard-page">
      <TopBar location="Nashik, MH" weather="" />

      {/* APMC Name */}
      <div className="apmc-header">
        <h1 className="apmc-title">Pimpalgaon Baswant APMC</h1>
        <button className="apmc-map-link">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#2E7D32" strokeWidth="2">
            <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z" /><circle cx="12" cy="10" r="3" />
          </svg>
          View on Map
        </button>
      </div>

      {/* Badges */}
      <div className="apmc-badges">
        <span className="apmc-badge apmc-badge--volume">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
            <polyline points="23 6 13.5 15.5 8.5 10.5 1 18" />
          </svg>
          HIGH ARRIVAL VOLUME
        </span>
      </div>

      <div className="apmc-updated">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--gray-400)" strokeWidth="2">
          <polyline points="23 4 23 10 17 10" /><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10" />
        </svg>
        Last updated: Today, 10:30 AM
      </div>

      {/* Commodity Price Cards */}
      <div className="commodity-grid">
        {commodities.map((c) => (
          <div key={c.name} className={`commodity-card ${c.name === 'Potato' ? 'commodity-card--full' : ''}`}>
            <div className="commodity-card-header">
              <span className="commodity-name">{c.name}</span>
              <span className="commodity-emoji">{c.emoji}</span>
              {c.hot && <span className="commodity-hot">🔥</span>}
            </div>
            <p className="commodity-price">
              ₹{c.price.toLocaleString()}
              <span className="commodity-unit">{c.unit}</span>
            </p>
            <div className="commodity-range">
              <span>Min: ₹{c.min.toLocaleString()}</span>
              <span>Max: ₹{c.max.toLocaleString()}</span>
            </div>
          </div>
        ))}
      </div>

      {/* 7-Day Trend */}
      <div className="section-card">
        <div className="trend-header">
          <h2 className="section-title" style={{ margin: 0 }}>7-Day Trend</h2>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--green-800)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="23 6 13.5 15.5 8.5 10.5 1 18" />
          </svg>
        </div>
        <TrendChart />
      </div>

      {/* Nearby Alternatives */}
      <div className="section-card">
        <div className="suppliers-header">
          <h2 className="section-title" style={{ margin: 0 }}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--gray-700)" strokeWidth="2">
              <rect x="2" y="7" width="20" height="14" rx="2" ry="2" />
              <path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16" />
            </svg>
            Nearby Alternatives
          </h2>
        </div>

        {nearbyAlternatives.map((alt) => (
          <div key={alt.name} className="supplier-row" style={{ cursor: 'pointer' }}>
            <div>
              <p className="supplier-name">{alt.name}</p>
              <p className="supplier-distance">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z" /><circle cx="12" cy="10" r="3" />
                </svg>
                {alt.distance}
              </p>
            </div>
            <div style={{ textAlign: 'right' }}>
              <p className="mandi-card-price" style={{ fontSize: 18 }}>₹{alt.price.toLocaleString()}</p>
              <p style={{ fontSize: 11, color: 'var(--gray-500)' }}>{alt.commodity}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
