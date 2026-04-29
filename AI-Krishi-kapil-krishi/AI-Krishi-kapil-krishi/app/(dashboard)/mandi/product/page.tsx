'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import TopBar from '@/app/components/ui/TopBar';

const product = {
  name: 'GlyphoMax 41%',
  category: 'HERBICIDE',
  toxicity: 'HIGH',
  desc: 'Systemic non-selective weed killer',
  activeIngredient: 'Glyphosate 41% SL',
  dosage: '800ml - 1L / Acre',
};

const alternatives = [
  {
    name: 'EcoClear WeedMaster',
    desc: 'Ammonium Salt of Glyphosate 71% SG',
    match: 98,
    price: 450,
    priceNote: '15%',
    efficacy: 4.8,
    safety: 'Safer',
    safetyColor: '#2E7D32',
    cta: 'Locate Nearest Store',
  },
  {
    name: 'Paraquat Dichloride 24% SL',
    desc: 'Contact Herbicide Alternative',
    match: 85,
    price: 520,
    priceNote: 'Similar',
    efficacy: 4.5,
    safety: 'High Risk',
    safetyColor: '#C62828',
    cta: 'Check Availability',
  },
];

export default function AnalyzedProductPage() {
  const router = useRouter();
  const [search, setSearch] = useState('');

  return (
    <div className="dashboard-page">
      <TopBar location="Nashik, MH" weather="" />

      {/* Search */}
      <div className="product-search-row">
        <div className="mandi-search" style={{ flex: 1, margin: 0 }}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--gray-400)" strokeWidth="2">
            <circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" />
          </svg>
          <input
            type="text"
            placeholder="Search chemical, brand, o..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="mandi-search-input"
          />
        </div>
        <button className="product-ai-btn" aria-label="AI Scan">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
            <line x1="7" y1="12" x2="17" y2="12" />
            <line x1="12" y1="7" x2="12" y2="17" />
          </svg>
        </button>
      </div>

      <h2 className="product-section-title">Analyzed Product</h2>

      {/* Product Card */}
      <div className="section-card">
        <div className="product-card-header">
          <span className="product-category-badge">{product.category}</span>
          <div className="product-toxicity-badge">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#C62828" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
              <line x1="12" y1="9" x2="12" y2="13" /><line x1="12" y1="17" x2="12.01" y2="17" />
            </svg>
            <span>HIGH<br/>TOXICITY</span>
          </div>
        </div>
        <h3 className="product-name">{product.name}</h3>
        <p className="product-desc">{product.desc}</p>

        <div className="product-info-grid">
          <div className="product-info-item">
            <div className="product-info-icon">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--gray-500)" strokeWidth="2">
                <path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z" />
              </svg>
            </div>
            <p className="product-info-label">ACTIVE INGREDIENT</p>
            <p className="product-info-value">{product.activeIngredient}</p>
          </div>
          <div className="product-info-item">
            <div className="product-info-icon">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--gray-500)" strokeWidth="2">
                <circle cx="12" cy="12" r="10" /><polyline points="12 6 12 12 16 14" />
              </svg>
            </div>
            <p className="product-info-label">STANDARD DOSAGE</p>
            <p className="product-info-value">{product.dosage}</p>
          </div>
        </div>
      </div>

      {/* Alternatives */}
      <div className="product-alt-header">
        <h2 className="product-section-title" style={{ margin: 0 }}>Suggested Alternatives</h2>
        <button className="product-filter-btn">Filter</button>
      </div>

      {alternatives.map((alt) => (
        <div key={alt.name} className="section-card product-alt-card">
          <div className="product-alt-top">
            <div style={{ flex: 1 }}>
              <h3 className="product-alt-name">{alt.name}</h3>
              <p className="product-alt-desc">{alt.desc}</p>
            </div>
            <span className="product-match-badge">
              <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="3">
                <polyline points="20 6 9 17 4 12" />
              </svg>
              {alt.match}% Match
            </span>
          </div>

          <div className="product-stats-row">
            <div className="product-stat">
              <p className="product-stat-label">PRICE / L</p>
              <p className="product-stat-value">
                ₹{alt.price}
                <span className={`product-stat-note ${alt.priceNote.includes('%') ? 'product-stat-note--green' : ''}`}>
                  {alt.priceNote.includes('%') ? ` ↓${alt.priceNote}` : ` ${alt.priceNote}`}
                </span>
              </p>
            </div>
            <div className="product-stat">
              <p className="product-stat-label">EFFICACY</p>
              <p className="product-stat-value">{alt.efficacy} ★</p>
            </div>
            <div className="product-stat">
              <p className="product-stat-label">SAFETY</p>
              <p className="product-stat-value" style={{ color: alt.safetyColor }}>
                {alt.safety === 'Safer' ? '✓ ' : '⚠ '}{alt.safety}
              </p>
            </div>
          </div>

          <button
            className={`product-cta-btn ${alt.safety === 'Safer' ? 'product-cta-btn--primary' : 'product-cta-btn--secondary'}`}
          >
            {alt.safety === 'Safer' ? (
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z" /><circle cx="12" cy="10" r="3" />
              </svg>
            ) : (
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <rect x="2" y="7" width="20" height="14" rx="2" ry="2" />
                <path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16" />
              </svg>
            )}
            {alt.cta}
          </button>
        </div>
      ))}
    </div>
  );
}
