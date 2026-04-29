'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import TopBar from '@/app/components/ui/TopBar';

const commodities = [
  { name: 'Onion (Red)', nameHi: 'प्याज (लाल)', price: 2450, change: 120, unit: '₹/Quintal' },
  { name: 'Tomato', nameHi: 'टमाटर', price: 1800, change: -80, unit: '₹/Quintal' },
  { name: 'Potato', nameHi: 'आलू', price: 1200, change: 50, unit: '₹/Quintal' },
];

const mandis = [
  { name: 'Lasalgaon', distance: 45, price: 2450, arrival: '12,000 q', badge: 'Highest' },
  { name: 'Pimpalgaon', distance: 32, price: 2380, arrival: '8,500 q', badge: null },
  { name: 'Nashik APMC', distance: 12, price: 2300, arrival: '4,200 q', badge: 'Nearest' },
];

// SVG chart data for 15-day price forecast
const chartPoints = [
  { x: 0, y: 2200 }, { x: 1, y: 2180 }, { x: 2, y: 2220 },
  { x: 3, y: 2250 }, { x: 4, y: 2230 }, { x: 5, y: 2280 },
  { x: 6, y: 2300 }, { x: 7, y: 2320 }, { x: 8, y: 2350 },
  { x: 9, y: 2380 }, { x: 10, y: 2450 }, { x: 11, y: 2500 },
  { x: 12, y: 2550 }, { x: 13, y: 2580 }, { x: 14, y: 2620 },
];

function PriceChart() {
  const w = 320, h = 160, px = 30, py = 10;
  const minY = 2000, maxY = 3000;
  const scaleX = (i: number) => px + (i / 14) * (w - px * 2);
  const scaleY = (v: number) => h - py - ((v - minY) / (maxY - minY)) * (h - py * 2);

  const line = chartPoints.map((p, i) =>
    `${i === 0 ? 'M' : 'L'}${scaleX(p.x)},${scaleY(p.y)}`
  ).join(' ');

  const area = `${line} L${scaleX(14)},${h - py} L${scaleX(0)},${h - py} Z`;
  const todayIdx = 10;

  return (
    <svg viewBox={`0 0 ${w} ${h}`} width="100%" style={{ overflow: 'visible' }}>
      <defs>
        <linearGradient id="areaGrad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#2E7D32" stopOpacity="0.15" />
          <stop offset="100%" stopColor="#2E7D32" stopOpacity="0.02" />
        </linearGradient>
      </defs>
      {/* Y axis labels */}
      {[2000, 2500, 3000].map(v => (
        <g key={v}>
          <line x1={px} y1={scaleY(v)} x2={w - px} y2={scaleY(v)} stroke="#E0E0E0" strokeWidth="0.5" />
          <text x={px - 4} y={scaleY(v) + 4} textAnchor="end" fill="#9E9E9E" fontSize="9">{v}</text>
        </g>
      ))}
      {/* Area fill */}
      <path d={area} fill="url(#areaGrad)" />
      {/* Line - history (solid) */}
      <path d={chartPoints.slice(0, todayIdx + 1).map((p, i) =>
        `${i === 0 ? 'M' : 'L'}${scaleX(p.x)},${scaleY(p.y)}`
      ).join(' ')} fill="none" stroke="#2E7D32" strokeWidth="2.5" strokeLinecap="round" />
      {/* Line - forecast (dashed) */}
      <path d={chartPoints.slice(todayIdx).map((p, i) =>
        `${i === 0 ? 'M' : 'L'}${scaleX(p.x)},${scaleY(p.y)}`
      ).join(' ')} fill="none" stroke="#2E7D32" strokeWidth="2" strokeDasharray="4 3" strokeLinecap="round" />
      {/* Today dot */}
      <circle cx={scaleX(todayIdx)} cy={scaleY(chartPoints[todayIdx].y)} r="5" fill="#2E7D32" />
      <circle cx={scaleX(todayIdx)} cy={scaleY(chartPoints[todayIdx].y)} r="3" fill="#fff" />
      {/* Today line */}
      <line x1={scaleX(todayIdx)} y1={scaleY(chartPoints[todayIdx].y) + 8} x2={scaleX(todayIdx)} y2={h - py}
        stroke="#2E7D32" strokeWidth="1" strokeDasharray="3 2" />
      {/* X labels */}
      <text x={scaleX(0)} y={h} textAnchor="start" fill="#9E9E9E" fontSize="9">May 1</text>
      <text x={scaleX(todayIdx)} y={h} textAnchor="middle" fill="#1B5E20" fontSize="9" fontWeight="700">Today</text>
      <text x={scaleX(14)} y={h} textAnchor="end" fill="#9E9E9E" fontSize="9">May 15</text>
    </svg>
  );
}

export default function MandiInsightsPage() {
  const router = useRouter();
  const [lang, setLang] = useState<'en' | 'hi'>('en');
  const [search, setSearch] = useState('');
  const [filter, setFilter] = useState('Nearest');

  const filteredMandis = [...mandis].sort((a, b) => {
    if (filter === 'Nearest') return a.distance - b.distance;
    if (filter === 'Highest Price') return b.price - a.price;
    return 0;
  });

  const selectedCommodity = commodities[0];

  return (
    <div className="dashboard-page">
      <TopBar location="Nashik, MH" weather="" />

      {/* Title + Language Toggle */}
      <div className="mandi-ins-header">
        <h1 className="mandi-ins-title">Mandi Insights</h1>
        <div className="lang-toggle">
          <button className={`lang-btn ${lang === 'en' ? 'lang-btn--active' : ''}`} onClick={() => setLang('en')}>EN</button>
          <button className={`lang-btn ${lang === 'hi' ? 'lang-btn--active' : ''}`} onClick={() => setLang('hi')}>HI</button>
        </div>
      </div>

      {/* Search */}
      <div className="mandi-search">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--gray-400)" strokeWidth="2">
          <circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" />
        </svg>
        <input
          type="text"
          placeholder={lang === 'en' ? 'Search commodities...' : 'वस्तुएं खोजें...'}
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="mandi-search-input"
        />
      </div>

      {/* AI Recommendation */}
      <div className="mandi-rec-card">
        <div className="mandi-rec-header">
          <div className="mandi-rec-icon">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#E65100" strokeWidth="2">
              <path d="M12 2v20M2 12h20" />
            </svg>
          </div>
          <div style={{ flex: 1 }}>
            <p className="mandi-rec-label">{lang === 'en' ? 'Recommendation:' : 'सिफारिश:'}</p>
            <p className="mandi-rec-action">HOLD</p>
          </div>
          <button className="mandi-rec-info" aria-label="Info">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--gray-400)" strokeWidth="2">
              <circle cx="12" cy="12" r="10" /><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3" /><line x1="12" y1="17" x2="12.01" y2="17" />
            </svg>
          </button>
        </div>
        <p className="mandi-rec-text">
          {lang === 'en'
            ? 'Current price is slightly below the 30-day average. AI models predict a 5-8% increase in demand next week.'
            : 'वर्तमान मूल्य 30-दिन के औसत से थोड़ा कम है। AI मॉडल अगले सप्ताह मांग में 5-8% वृद्धि की भविष्यवाणी करते हैं।'}
        </p>
      </div>

      {/* Price Chart Card */}
      <div className="section-card" style={{ overflow: 'hidden' }}>
        <div className="chart-header">
          <div>
            <h2 className="chart-commodity">{lang === 'en' ? selectedCommodity.name : selectedCommodity.nameHi}</h2>
            <p className="chart-sub">
              {lang === 'en' ? '15-Day Price Forecast' : '15-दिन का मूल्य पूर्वानुमान'} ({selectedCommodity.unit})
            </p>
          </div>
          <div className="chart-price-box">
            <span className="chart-price">₹{selectedCommodity.price.toLocaleString()}</span>
            <span className={`chart-change ${selectedCommodity.change >= 0 ? 'chart-change--up' : 'chart-change--down'}`}>
              {selectedCommodity.change >= 0 ? '↗' : '↘'} {selectedCommodity.change >= 0 ? '+' : ''}₹{selectedCommodity.change} today
            </span>
          </div>
        </div>
        <div className="chart-container">
          <PriceChart />
        </div>
      </div>

      {/* Nearby Mandis */}
      <div className="mandi-section-header">
        <h2 className="mandi-section-title">{lang === 'en' ? 'Nearby Mandis' : 'आस-पास की मंडियाँ'}</h2>
      </div>

      <div className="mandi-filters">
        {['Nearest', 'Highest Price', 'Most Arrivals'].map(f => (
          <button
            key={f}
            className={`mandi-filter-chip ${filter === f ? 'mandi-filter-chip--active' : ''}`}
            onClick={() => setFilter(f)}
          >
            {f}
          </button>
        ))}
      </div>

      {/* Mandi Cards */}
      {filteredMandis.map((m) => (
        <div
          key={m.name}
          className="mandi-card"
          onClick={() => router.push('/mandi/detail')}
          role="button"
          tabIndex={0}
        >
          <div className="mandi-card-top">
            <div>
              <p className="mandi-card-name">{m.name}</p>
              <p className="mandi-card-dist">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z" /><circle cx="12" cy="10" r="3" />
                </svg>
                {m.distance} km
              </p>
            </div>
            <div className="mandi-card-right">
              <p className="mandi-card-price">₹{m.price.toLocaleString()}</p>
              {m.badge && <span className={`mandi-badge mandi-badge--${m.badge.toLowerCase()}`}>{m.badge}</span>}
            </div>
          </div>
          <div className="mandi-card-bottom">
            <span className="mandi-card-arrival">Arrival: {m.arrival}</span>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--gray-400)" strokeWidth="2">
              <polyline points="9 18 15 12 9 6" />
            </svg>
          </div>
        </div>
      ))}

      {/* Link to Product Analyzer */}
      <div style={{ padding: '8px 16px 16px' }}>
        <button
          className="product-cta-btn product-cta-btn--secondary"
          onClick={() => router.push('/mandi/product')}
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" />
          </svg>
          Analyze a Chemical Product
        </button>
      </div>
    </div>
  );
}
