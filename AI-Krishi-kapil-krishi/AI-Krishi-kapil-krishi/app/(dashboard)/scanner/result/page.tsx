'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Image from 'next/image';

const treatments = [
  {
    id: 'chemical',
    type: 'CHEMICAL',
    typeColor: '#C62828',
    name: 'Mancozeb 75% WP',
    desc: 'Fast-acting fungicide. Apply 2-2.5g per liter of water immediately.',
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--gray-500)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z" />
      </svg>
    ),
  },
  {
    id: 'organic',
    type: 'ORGANIC',
    typeColor: '#2E7D32',
    name: 'Copper Fungicide',
    desc: 'Approved for organic use. Apply preventatively or at first sign.',
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--gray-500)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
      </svg>
    ),
  },
];

const suppliers = [
  { name: 'Kisan Agro Center', distance: '2.4 km away' },
  { name: 'Green Farm Supplies', distance: '5.1 km away' },
];

export default function ScannerResultPage() {
  const router = useRouter();
  const [lang, setLang] = useState<'en' | 'hi'>('en');
  const [scanResult, setScanResult] = useState<any>(null);

  import('react').then(React => {
    React.useEffect(() => {
      const stored = sessionStorage.getItem('scanResult');
      if (stored) {
        try {
          setScanResult(JSON.parse(stored));
        } catch {}
      }
    }, []);
  });

  const content = {
    en: {
      title: 'Scanner Result',
      detected: 'DISEASE DETECTED',
      detectedSub: 'रोग पाया गया',
      disease: 'Late Blight',
      diseaseSub: 'पछेती झुलसा',
      diseaseDesc: 'A fast-spreading fungal disease affecting tomatoes and potatoes...',
      treatmentTitle: 'Treatment Options',
      treatmentSub: 'उपचार के विकल्प',
      buyLocal: '₹ Buy Locally',
      suppliersTitle: 'Local Suppliers',
      viewAll: 'View All on Map',
    },
    hi: {
      title: 'स्कैनर परिणाम',
      detected: 'रोग पाया गया',
      detectedSub: 'DISEASE DETECTED',
      disease: 'पछेती झुलसा',
      diseaseSub: 'Late Blight',
      diseaseDesc: 'एक तेजी से फैलने वाला कवक रोग जो टमाटर और आलू को प्रभावित करता है...',
      treatmentTitle: 'उपचार के विकल्प',
      treatmentSub: 'Treatment Options',
      buyLocal: '₹ स्थानीय खरीदें',
      suppliersTitle: 'स्थानीय आपूर्तिकर्ता',
      viewAll: 'मानचित्र पर देखें',
    },
  };

  const t = content[lang];

  return (
    <div className="dashboard-page">
      {/* Header */}
      <div className="result-header">
        <button className="profile-back" onClick={() => router.back()} aria-label="Go back">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="15 18 9 12 15 6" />
          </svg>
        </button>
        <h1 className="result-header-title">{t.title}</h1>
        <div className="lang-toggle">
          <button
            className={`lang-btn ${lang === 'en' ? 'lang-btn--active' : ''}`}
            onClick={() => setLang('en')}
          >
            EN
          </button>
          <button
            className={`lang-btn ${lang === 'hi' ? 'lang-btn--active' : ''}`}
            onClick={() => setLang('hi')}
          >
            HI
          </button>
        </div>
      </div>

      {/* Disease Detection Card */}
      <div className="disease-card">
        <div className="disease-image-container">
          <Image
            src="/images/diseased-leaf.png"
            alt="Diseased leaf scan"
            fill
            style={{ objectFit: 'cover' }}
          />
          <div className="disease-overlay">
            <div className="disease-badge-row">
              <span className="disease-detected-badge">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="12" cy="12" r="10" />
                  <line x1="12" y1="8" x2="12" y2="12" />
                  <line x1="12" y1="16" x2="12.01" y2="16" />
                </svg>
                {t.detected} / {t.detectedSub}
              </span>
              <span className="disease-match-badge">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                  <polyline points="20 6 9 17 4 12" />
                </svg>
                {scanResult?.confidence || 88}% Match
              </span>
            </div>
            <h2 className="disease-name">{lang === 'hi' ? scanResult?.disease_hi || t.disease : scanResult?.disease || t.disease}</h2>
            <p className="disease-name-sub">{lang === 'hi' ? scanResult?.disease || t.diseaseSub : scanResult?.disease_hi || t.diseaseSub}</p>
            <p className="disease-desc">{t.diseaseDesc}</p>
          </div>
        </div>
      </div>

      {/* Treatment Options */}
      <div className="section-card">
        <div className="treatment-header">
          <div className="treatment-icon-circle">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--green-800)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="10" />
              <circle cx="12" cy="12" r="3" />
              <line x1="12" y1="2" x2="12" y2="6" />
              <line x1="12" y1="18" x2="12" y2="22" />
              <line x1="2" y1="12" x2="6" y2="12" />
              <line x1="18" y1="12" x2="22" y2="12" />
            </svg>
          </div>
          <div>
            <h2 className="treatment-title">{t.treatmentTitle}</h2>
            <p className="treatment-sub">{t.treatmentSub}</p>
          </div>
        </div>

        {(scanResult?.treatment?.length ? scanResult.treatment : treatments).map((tr: any, idx: number) => (
          <div key={tr.id || idx} className="treatment-card">
            <div className="treatment-card-header">
              <span className="treatment-type-badge" style={{ color: tr.typeColor || '#C62828', borderColor: tr.typeColor || '#C62828' }}>
                {tr.type || 'TREATMENT'}
              </span>
              {tr.icon || (
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--gray-500)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z" />
                </svg>
              )}
            </div>
            <p className="treatment-name">{tr.name}</p>
            <p className="treatment-desc">{tr.desc}</p>
            <button className="treatment-buy-btn">
              {t.buyLocal}
            </button>
          </div>
        ))}
      </div>

      {/* Local Suppliers */}
      <div className="section-card">
        <div className="suppliers-header">
          <h2 className="section-title">{t.suppliersTitle}</h2>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--green-800)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <rect x="2" y="7" width="20" height="14" rx="2" ry="2" />
            <path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16" />
          </svg>
        </div>

        {suppliers.map((s) => (
          <div key={s.name} className="supplier-row">
            <div>
              <p className="supplier-name">{s.name}</p>
              <p className="supplier-distance">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z" />
                  <circle cx="12" cy="10" r="3" />
                </svg>
                {s.distance}
              </p>
            </div>
            <button className="supplier-call-btn" aria-label={`Call ${s.name}`}>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--green-800)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z" />
              </svg>
            </button>
          </div>
        ))}

        <button className="view-map-btn">{t.viewAll}</button>
      </div>
    </div>
  );
}
