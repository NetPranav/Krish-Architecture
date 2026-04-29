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

const chartData = [
  { year: '18', rain: '40%', yield: '50%', x: '5%', y: '50%' },
  { year: '19', rain: '60%', yield: '35%', x: '23%', y: '65%' },
  { year: '20', rain: '30%', yield: '60%', x: '41%', y: '40%' },
  { year: '21', rain: '85%', yield: '10%', x: '59%', y: '90%' },
  { year: '22', rain: '70%', yield: '20%', x: '77%', y: '80%' },
  { year: '23', rain: '95%', yield: '0%', x: '95%', y: '100%' }
];

export default function WeatherHistoryPage() {
  const router = useRouter();
  const [fieldZone, setFieldZone] = useState('All Field Zones');
  const [crop, setCrop] = useState('All Crops');

  const toggleZone = () => setFieldZone(prev => prev === 'All Field Zones' ? 'North Plot' : prev === 'North Plot' ? 'South Plot' : 'All Field Zones');
  const toggleCrop = () => setCrop(prev => prev === 'All Crops' ? 'Cotton' : prev === 'Cotton' ? 'Soybean' : 'All Crops');

  return (
    <div className="dashboard-page" style={{ background: '#f8f9fa', minHeight: '100vh', paddingBottom: 40 }}>
      <TopBar location="Nashik, MH" weather="" />

      <div style={{ padding: '24px 16px 16px' }}>
        <h1 style={{ fontSize: 28, fontWeight: 800, color: '#1a1a1a', margin: 0, lineHeight: 1.2 }}>Historical Data</h1>
        <p style={{ fontSize: 15, color: '#666', marginTop: 8, lineHeight: 1.5 }}>Analyze past trends to optimize future harvests.</p>
      </div>

      {/* Filters */}
      <div style={{ display: 'flex', gap: 12, padding: '0 16px 16px', overflowX: 'auto', WebkitOverflowScrolling: 'touch' }}>
        <button onClick={toggleZone} style={{ display: 'flex', alignItems: 'center', gap: 8, background: '#fff', border: '1px solid #e0e0e0', padding: '10px 16px', borderRadius: 24, fontSize: 14, fontWeight: 600, color: '#333', boxShadow: '0 2px 6px rgba(0,0,0,0.02)', cursor: 'pointer', whiteSpace: 'nowrap', transition: 'all 0.2s' }}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
            <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z" /><circle cx="12" cy="10" r="3" />
          </svg>
          {fieldZone}
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
            <polyline points="6 9 12 15 18 9" />
          </svg>
        </button>
        <button onClick={toggleCrop} style={{ display: 'flex', alignItems: 'center', gap: 8, background: '#fff', border: '1px solid #e0e0e0', padding: '10px 16px', borderRadius: 24, fontSize: 14, fontWeight: 600, color: '#333', boxShadow: '0 2px 6px rgba(0,0,0,0.02)', cursor: 'pointer', whiteSpace: 'nowrap', transition: 'all 0.2s' }}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
            <path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" />
          </svg>
          {crop}
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
            <polyline points="6 9 12 15 18 9" />
          </svg>
        </button>
      </div>

      {/* AI Predicted Yield */}
      <div style={{ background: 'linear-gradient(135deg, #1B5E20 0%, #2E7D32 100%)', borderRadius: 20, padding: 24, margin: '0 16px 24px', color: 'white', position: 'relative', overflow: 'hidden', boxShadow: '0 12px 24px rgba(46,125,50,0.25)' }}>
        <div style={{ position: 'absolute', top: -20, right: -20, opacity: 0.1, transform: 'rotate(-15deg)' }}>
          <svg width="180" height="180" viewBox="0 0 24 24" fill="currentColor">
            <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z" />
          </svg>
        </div>
        
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
          <div style={{ background: 'rgba(255,255,255,0.2)', padding: 8, borderRadius: 12, backdropFilter: 'blur(8px)' }}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" />
            </svg>
          </div>
          <p style={{ fontSize: 13, fontWeight: 700, letterSpacing: 1, textTransform: 'uppercase', margin: 0, opacity: 0.9 }}>AI Predicted Yield</p>
        </div>
        
        <div style={{ display: 'flex', alignItems: 'baseline', gap: 8, marginBottom: 12 }}>
          <span style={{ fontSize: 56, fontWeight: 800, lineHeight: 1 }}>4.2</span>
          <span style={{ fontSize: 16, opacity: 0.9, fontWeight: 600 }}>Tons / Acre</span>
        </div>
        
        <p style={{ fontSize: 14, lineHeight: 1.5, opacity: 0.95, margin: 0, marginBottom: 24, maxWidth: '95%' }}>
          Expected <span style={{ color: '#A5D6A7', fontWeight: 800 }}>+12% increase</span> compared to 5-year average, driven by optimal early-season rainfall.
        </p>
        
        <button onClick={() => router.push('/weather')} style={{ background: '#fff', color: '#1B5E20', border: 'none', padding: '12px 24px', borderRadius: 30, fontSize: 14, fontWeight: 700, display: 'inline-flex', alignItems: 'center', gap: 8, cursor: 'pointer', boxShadow: '0 4px 12px rgba(0,0,0,0.15)', transition: 'all 0.2s' }}>
          View Details
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
            <polyline points="9 18 15 12 9 6" />
          </svg>
        </button>
      </div>

      {/* Yield vs Rainfall Chart */}
      <div style={{ background: '#fff', padding: 20, borderRadius: 20, margin: '0 16px 24px', border: '1px solid #eaeaea', boxShadow: '0 4px 16px rgba(0,0,0,0.04)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div>
            <h2 style={{ fontSize: 18, fontWeight: 800, color: '#1a1a1a', marginBottom: 4, marginTop: 0 }}>Yield vs. Rainfall</h2>
            <p style={{ fontSize: 13, color: '#666', margin: 0 }}>Historical correlation (2018-2023)</p>
          </div>
          <div style={{ background: '#E8F5E9', color: '#2E7D32', padding: '6px 12px', borderRadius: 20, fontSize: 12, fontWeight: 700 }}>
            Strong Positive
          </div>
        </div>
        
        <div style={{ position: 'relative', height: 180, marginTop: 32, marginBottom: 16 }}>
          {/* Y-Axis lines */}
          <div style={{ position: 'absolute', top: '0%', left: 0, right: 0, borderTop: '1px dashed #e5e5e5' }}></div>
          <div style={{ position: 'absolute', top: '33%', left: 0, right: 0, borderTop: '1px dashed #e5e5e5' }}></div>
          <div style={{ position: 'absolute', top: '66%', left: 0, right: 0, borderTop: '1px dashed #e5e5e5' }}></div>
          <div style={{ position: 'absolute', top: '100%', left: 0, right: 0, borderTop: '1px dashed #e5e5e5' }}></div>
          
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', height: '100%', padding: '0', position: 'relative', zIndex: 1 }}>
            {chartData.map((d, i) => (
              <div key={i} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 8, flex: 1, position: 'relative' }}>
                <div style={{ width: '100%', maxWidth: 24, height: d.rain, background: 'linear-gradient(to top, #90CAF9, #42A5F5)', borderRadius: '6px 6px 0 0', opacity: 0.85, transition: 'height 0.5s ease-out' }} />
                <span style={{ fontSize: 12, color: '#888', fontWeight: 600, position: 'absolute', bottom: -24 }}>'{d.year}</span>
              </div>
            ))}
          </div>

          {/* Line Overlay for Yield */}
          <svg style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', overflow: 'visible', zIndex: 2 }} preserveAspectRatio="none" viewBox="0 0 100 100">
            <polyline 
              points="8,50 25,35 42,60 58,10 75,20 92,0" 
              fill="none" 
              stroke="#2E7D32" 
              strokeWidth="2.5" 
              vectorEffect="non-scaling-stroke"
              strokeLinecap="round" 
              strokeLinejoin="round" 
            />
          </svg>
          
          {/* Dots overlay for precise positioning independent of svg stretching */}
          {chartData.map((d, i) => (
            <div key={i} style={{ position: 'absolute', left: d.x, top: d.y, width: 10, height: 10, background: '#fff', border: '2.5px solid #2E7D32', borderRadius: '50%', transform: 'translate(-50%, -50%)', zIndex: 3, boxShadow: '0 2px 4px rgba(0,0,0,0.15)' }} />
          ))}
        </div>

        <div style={{ display: 'flex', justifyContent: 'center', gap: 24, marginTop: 40, paddingTop: 16, borderTop: '1px solid #f0f0f0' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13, fontWeight: 600, color: '#555' }}>
            <div style={{ width: 12, height: 4, background: '#2E7D32', borderRadius: 2 }} />
            Avg Yield
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13, fontWeight: 600, color: '#555' }}>
            <div style={{ width: 14, height: 14, background: '#42A5F5', borderRadius: 3, opacity: 0.85 }} />
            Rainfall
          </div>
        </div>
      </div>

      {/* Monthly Rainfall Spikes */}
      <div style={{ background: '#fff', padding: 20, borderRadius: 20, margin: '0 16px 24px', border: '1px solid #eaeaea', boxShadow: '0 4px 16px rgba(0,0,0,0.04)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
          <h2 style={{ fontSize: 18, fontWeight: 800, color: '#1a1a1a', margin: 0 }}>Monthly Rainfall Spikes</h2>
          <div style={{ background: '#E3F2FD', padding: 10, borderRadius: 14 }}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#1565C0" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z" />
            </svg>
          </div>
        </div>
        
        <div style={{ display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between', height: 140, paddingTop: 20 }}>
          {rainfallData.map((d, i) => {
            const isHighlight = d.month === 'May';
            return (
              <div key={d.month} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 8, flex: 1 }}>
                {isHighlight && <span style={{ fontSize: 13, fontWeight: 800, color: '#1565C0', marginBottom: 2 }}>{d.value}</span>}
                <div 
                  style={{ 
                    height: d.value * 1.2, 
                    width: '100%', 
                    maxWidth: 36,
                    background: isHighlight ? 'linear-gradient(to top, #1976D2, #64B5F6)' : '#f0f0f0', 
                    borderRadius: '8px 8px 0 0',
                    transition: 'all 0.3s ease',
                    boxShadow: isHighlight ? '0 8px 16px rgba(25,118,210,0.25)' : 'none'
                  }} 
                />
                <span style={{ fontSize: 13, color: isHighlight ? '#1565C0' : '#888', fontWeight: isHighlight ? 800 : 600 }}>{d.month}</span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Weather Context */}
      <div style={{ padding: '8px 16px 12px' }}>
        <h2 style={{ fontSize: 20, fontWeight: 800, color: '#1a1a1a', margin: 0 }}>Context & Averages</h2>
      </div>

      <div style={{ padding: '0 16px 24px', display: 'flex', flexDirection: 'column', gap: 12 }}>
        {weatherContext.map((item) => (
          <div key={item.label} style={{ display: 'flex', alignItems: 'center', gap: 16, background: '#fff', padding: 16, borderRadius: 20, border: '1px solid #eaeaea', boxShadow: '0 4px 12px rgba(0,0,0,0.03)' }}>
            <div style={{ background: item.color === '#2E7D32' ? '#E8F5E9' : '#F5F5F5', width: 52, height: 52, borderRadius: 16, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke={item.color} strokeWidth="2.5">
                <path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z" />
              </svg>
            </div>
            <div style={{ flex: 1 }}>
              <p style={{ fontSize: 13, color: '#666', marginBottom: 4, fontWeight: 500 }}>{item.label}</p>
              <div style={{ display: 'flex', alignItems: 'baseline', gap: 10 }}>
                <p style={{ fontSize: 22, fontWeight: 800, color: '#1a1a1a', margin: 0 }}>{item.value}</p>
                <span style={{ fontSize: 13, fontWeight: 700, color: item.color, background: item.color === '#2E7D32' ? '#E8F5E9' : '#F5F5F5', padding: '4px 10px', borderRadius: 12 }}>{item.change}</span>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Back to Weather */}
      <div style={{ padding: '0 16px 24px' }}>
        <button onClick={() => router.push('/weather')} style={{ width: '100%', background: '#fff', color: '#1a1a1a', border: '1px solid #eaeaea', padding: '16px', borderRadius: 16, fontSize: 15, fontWeight: 700, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8, cursor: 'pointer', boxShadow: '0 4px 12px rgba(0,0,0,0.03)', transition: 'all 0.2s' }}>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
            <path d="M19 12H5M12 19l-7-7 7-7" />
          </svg>
          Back to Weather Hub
        </button>
      </div>
    </div>
  );
}
