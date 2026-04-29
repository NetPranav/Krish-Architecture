'use client';

import { useState, useEffect, useMemo } from 'react';
import { useRouter } from 'next/navigation';
import TopBar from '@/app/components/ui/TopBar';
import StatusBanner from '@/app/components/ui/StatusBanner';
import { getWeatherCurrent, getWeatherForecast } from '@/app/lib/api';

const defaultHourly = [
  { time: 'Now', icon: '⛅', temp: '32°', rain_pct: 0 },
  { time: '14:00', icon: '☀️', temp: '34°', rain_pct: 0 },
  { time: '17:00', icon: '☀️', temp: '35°', rain_pct: 0 },
  { time: '20:00', icon: '⛅', temp: '31°', rain_pct: 5 },
  { time: '23:00', icon: '⛅', temp: '28°', rain_pct: 10 },
  { time: '02:00', icon: '🌧️', temp: '25°', rain_pct: 40 },
  { time: '05:00', icon: '🌧️', temp: '24°', rain_pct: 60 },
  { time: '08:00', icon: '⛅', temp: '26°', rain_pct: 20 },
];

const defaultWeekly = [
  { day: 'Today', rain: '10%', icon: '☀️', low: '22°', high: '35°', highlight: false },
  { day: 'Thu', rain: '20%', icon: '⛅', low: '23°', high: '33°', highlight: false },
  { day: 'Fri', rain: '90%', icon: '🌧️', low: '20°', high: '28°', highlight: true },
  { day: 'Sat', rain: '60%', icon: '🌦️', low: '21°', high: '29°', highlight: false },
  { day: 'Sun', rain: '', icon: '☀️', low: '22°', high: '32°', highlight: false },
];

const ICON_MAP: Record<string, string> = { clear: '☀️', clouds: '⛅', rain: '🌧️', drizzle: '🌦️', thunderstorm: '⛈️', snow: '❄️' };

export default function WeatherPage() {
  const router = useRouter();
  const [activeTimeSlot, setActiveTimeSlot] = useState('Now');
  const [current, setCurrent] = useState<any>({ temperature: 32, feels_like: 35, description: 'Partly Cloudy', humidity: 65, wind_speed: 12, wind_dir: 'NE', frost_safe: true, soil_moisture_status: 'Optimal' });
  const [hourlyForecast, setHourlyForecast] = useState(defaultHourly);
  const [weeklyForecast, setWeeklyForecast] = useState(defaultWeekly);

  useEffect(() => {
    getWeatherCurrent().then(res => { if (res) setCurrent(res); }).catch(() => {});
    getWeatherForecast().then(res => {
      if (res?.hourly) {
        setHourlyForecast(res.hourly.map((h: any) => ({ time: h.time, temp: `${h.temp}°`, icon: ICON_MAP[h.icon] || '⛅', rain_pct: h.rain_pct })));
      }
      if (res?.weekly) {
        setWeeklyForecast(res.weekly.map((w: any) => ({ day: w.day, rain: w.rain, low: `${w.low}°`, high: `${w.high}°`, icon: ICON_MAP[w.icon] || '⛅', highlight: w.highlight })));
      }
    }).catch(() => {});
  }, []);

  const forecastTimeline = useMemo(() => {
    return [
      ...hourlyForecast.map(h => h.time),
      ...weeklyForecast.slice(1, 4).map(w => w.day)
    ];
  }, [hourlyForecast, weeklyForecast]);

  useEffect(() => {
    if (forecastTimeline.length > 0 && !forecastTimeline.includes(activeTimeSlot)) {
      setActiveTimeSlot(forecastTimeline[0]);
    }
  }, [forecastTimeline, activeTimeSlot]);

  const activeRainPct = useMemo(() => {
    const h = hourlyForecast.find(x => x.time === activeTimeSlot);
    if (h && h.rain_pct !== undefined) return `${h.rain_pct}%`;
    const w = weeklyForecast.find(x => x.day === activeTimeSlot);
    if (w && w.rain) return w.rain;
    return '0%';
  }, [activeTimeSlot, hourlyForecast, weeklyForecast]);

  const alertDay = weeklyForecast.find(w => w.highlight);

  return (
    <div className="dashboard-page">
      <TopBar location="Nashik, MH" weather={`${current.temperature}°C, ${current.description}`} />

      {/* Weather Warning Banner */}
      {alertDay && (
        <StatusBanner
          type="warning"
          title={`Heavy Rain predicted for ${alertDay.day === 'Today' ? 'today' : alertDay.day}.`}
          message="Secure vulnerable equipment and delay pesticide application."
        />
      )}

      {/* Current Conditions */}
      <div className="section-card">
        <div className="weather-current-header">
          <div>
            <h2 className="section-title" style={{ marginBottom: 4 }}>Current Conditions</h2>
            <p className="weather-temp-large">{current.temperature}°</p>
            <p className="weather-realfeel">RealFeel {current.feels_like}°</p>
            <p className="weather-desc">⛅ {current.description}</p>
          </div>
          <div className="weather-safe-badge">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#2E7D32" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
            </svg>
            {current.frost_safe ? 'Safe from Frost' : '⚠️ Frost Risk'}
          </div>
        </div>

        <div className="weather-metrics-row">
          <div className="weather-metric">
            <p className="weather-metric-label">Humidity</p>
            <p className="weather-metric-value">{current.humidity || 65}%</p>
          </div>
          <div className="weather-metric">
            <p className="weather-metric-label">Wind</p>
            <p className="weather-metric-value">{current.wind_speed || 12} km/h</p>
            <p className="weather-metric-sub">{current.wind_dir || 'NE'}</p>
          </div>
          <div className="weather-metric">
            <p className="weather-metric-label">Soil Moisture</p>
            <p className="weather-metric-value" style={{ color: 'var(--green-800)' }}>Optimal</p>
          </div>
        </div>
      </div>

      {/* Rain Probability */}
      <div className="section-card">
        <h2 className="section-title">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--gray-700)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z" />
          </svg>
          Rain Probability
        </h2>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginBottom: 16 }}>
          <div style={{ fontSize: 48, fontWeight: 800, color: '#1565C0', lineHeight: 1 }}>{activeRainPct}</div>
          <div style={{ fontSize: 14, color: 'var(--gray-500)', lineHeight: 1.2 }}>Chance of rain<br/>for {activeTimeSlot}</div>
        </div>
        <div className="rain-timeline" style={{ display: 'flex', overflowX: 'auto', gap: 8, paddingBottom: 8 }}>
          {forecastTimeline.map((slot) => (
            <button
              key={slot}
              className={`rain-slot ${activeTimeSlot === slot ? 'rain-slot--active' : ''}`}
              onClick={() => setActiveTimeSlot(slot)}
              style={{
                padding: '8px 16px',
                borderRadius: 20,
                border: '1px solid var(--gray-200)',
                background: activeTimeSlot === slot ? '#E3F2FD' : '#fff',
                color: activeTimeSlot === slot ? '#1565C0' : 'var(--gray-600)',
                fontWeight: activeTimeSlot === slot ? 600 : 500,
                cursor: 'pointer',
                transition: 'all 0.2s',
                whiteSpace: 'nowrap'
              }}
            >
              {slot}
            </button>
          ))}
        </div>
      </div>

      {/* 48-Hour Forecast */}
      <div style={{ background: 'linear-gradient(135deg, #1B5E20 0%, #2E7D32 100%)', borderRadius: 20, padding: '24px 16px', margin: '0 16px 24px', color: 'white', position: 'relative', overflow: 'hidden', boxShadow: '0 12px 24px rgba(46,125,50,0.2)' }}>
        <h2 style={{ fontSize: 18, fontWeight: 800, margin: '0 0 16px', color: '#fff', display: 'flex', alignItems: 'center', gap: 8 }}>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
            <circle cx="12" cy="12" r="10" /><polyline points="12 6 12 12 16 14" />
          </svg>
          48-Hour Forecast
        </h2>
        <div style={{ display: 'flex', gap: 12, overflowX: 'auto', paddingBottom: 12, scrollbarWidth: 'none', WebkitOverflowScrolling: 'touch' }}>
          {hourlyForecast.map((h) => (
            <div 
              key={h.time} 
              onClick={() => setActiveTimeSlot(h.time)}
              style={{ 
                minWidth: 70, 
                display: 'flex', 
                flexDirection: 'column', 
                alignItems: 'center', 
                padding: '12px 8px', 
                borderRadius: 16,
                background: activeTimeSlot === h.time ? 'rgba(255,255,255,0.2)' : 'rgba(255,255,255,0.05)',
                border: activeTimeSlot === h.time ? '1px solid rgba(255,255,255,0.5)' : '1px solid rgba(255,255,255,0.1)',
                cursor: 'pointer',
                transition: 'all 0.2s',
                backdropFilter: 'blur(8px)',
                transform: activeTimeSlot === h.time ? 'scale(1.05)' : 'none'
              }}
            >
              <p style={{ fontSize: 13, fontWeight: 600, margin: '0 0 8px', color: activeTimeSlot === h.time ? '#fff' : 'rgba(255,255,255,0.8)' }}>{h.time}</p>
              <p style={{ fontSize: 24, margin: '0 0 8px' }}>{h.icon}</p>
              <p style={{ fontSize: 16, fontWeight: 800, margin: 0 }}>{h.temp}</p>
              {h.rain_pct !== undefined && h.rain_pct > 0 && <p style={{ fontSize: 11, fontWeight: 700, color: '#A5D6A7', margin: '6px 0 0' }}>{h.rain_pct}%</p>}
            </div>
          ))}
        </div>
      </div>

      {/* 7-Day Outlook */}
      <div className="section-card">
        <h2 className="section-title">7-Day Outlook</h2>
        <div className="weekly-forecast">
          {weeklyForecast.map((d) => (
            <div
              key={d.day}
              className={`weekly-row ${d.highlight ? 'weekly-row--highlight' : ''}`}
              onClick={() => setActiveTimeSlot(d.day)}
              style={{ cursor: 'pointer', background: activeTimeSlot === d.day ? 'var(--gray-100)' : 'transparent', transition: 'all 0.2s', borderRadius: 8 }}
            >
              <span className={`weekly-day ${d.highlight ? 'weekly-day--alert' : ''}`}>{d.day}</span>
              {d.rain ? (
                <span className={`weekly-rain ${d.highlight ? 'weekly-rain--alert' : ''}`}>
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z" />
                  </svg>
                  {d.rain}
                </span>
              ) : (
                <span className="weekly-rain" />
              )}
              <span className="weekly-icon">{d.icon}</span>
              <span className="weekly-low">{d.low}</span>
              <span className="weekly-high">{d.high}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Link to Historical Weather & Yield */}
      <div style={{ padding: '0 16px 16px' }}>
        <button
          className="product-cta-btn product-cta-btn--primary"
          onClick={() => router.push('/weather/history')}
        >
          📊 View Historical Weather & Yield
        </button>
      </div>
    </div>
  );
}

