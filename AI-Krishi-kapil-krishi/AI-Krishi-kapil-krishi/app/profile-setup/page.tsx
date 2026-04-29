'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import StatusBanner from '@/app/components/ui/StatusBanner';

const soilTypes = ['Loamy', 'Clay', 'Sandy', 'Silt'];

export default function ProfileSetupPage() {
  const router = useRouter();
  const [landSize, setLandSize] = useState('');
  const [landUnit, setLandUnit] = useState('Acres');
  const [selectedSoil, setSelectedSoil] = useState('Loamy');
  const [voiceAssistance, setVoiceAssistance] = useState(true);
  const [showSuccess, setShowSuccess] = useState(true);
  const [loading, setLoading] = useState(false);

  const handleSave = () => {
    setLoading(true);
    setTimeout(() => {
      router.push('/dashboard');
    }, 800);
  };

  return (
    <div className="profile-setup-page">
      {/* Top Header */}
      <div className="profile-header">
        <button className="profile-back" onClick={() => router.back()} aria-label="Go back">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="15 18 9 12 15 6" />
          </svg>
        </button>
        <h1 className="profile-header-title">Profile Setup</h1>
        <div style={{ width: 22 }} />
      </div>

      {/* Step Indicator */}
      <div className="profile-steps">
        <div className="profile-step profile-step--done" />
        <div className="profile-step profile-step--done" />
        <div className="profile-step profile-step--active" />
      </div>

      {/* Success Banner */}
      {showSuccess && (
        <div style={{ marginBottom: 16 }}>
          <StatusBanner
            type="success"
            title="Profile Updated!"
            message="Your farm details have been saved successfully."
          />
        </div>
      )}

      {/* Farm Location — Step 1 */}
      <div className="section-card">
        <div className="profile-section-header">
          <h2 className="section-title">Farm Location</h2>
          <span className="step-label">Step 1 of 3</span>
        </div>
        <p className="profile-desc">
          Pinpoint your main field to receive accurate weather and hyper-local alerts.
        </p>

        {/* Map placeholder */}
        <div className="map-container">
          <div className="map-placeholder">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#2E7D32" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z" />
              <circle cx="12" cy="10" r="3" />
            </svg>
          </div>
          <button className="locate-btn" id="btn-locate-me">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="10" />
              <circle cx="12" cy="12" r="3" />
              <line x1="12" y1="2" x2="12" y2="6" />
              <line x1="12" y1="18" x2="12" y2="22" />
              <line x1="2" y1="12" x2="6" y2="12" />
              <line x1="18" y1="12" x2="22" y2="12" />
            </svg>
            Locate Me
          </button>
        </div>
      </div>

      {/* Land Details — Step 2 */}
      <div className="section-card">
        <div className="profile-section-header">
          <h2 className="section-title">Land Details</h2>
          <span className="step-label">Step 2 of 3</span>
        </div>

        <div className="form-field">
          <label className="form-label" htmlFor="land-size">Total Land Size</label>
          <div className="land-input-row">
            <input
              id="land-size"
              type="number"
              placeholder="e.g., 5.5"
              value={landSize}
              onChange={(e) => setLandSize(e.target.value)}
              className="form-input land-size-input"
            />
            <select
              value={landUnit}
              onChange={(e) => setLandUnit(e.target.value)}
              className="land-unit-select"
            >
              <option value="Acres">Ac</option>
              <option value="Hectares">Ha</option>
              <option value="Bigha">Bi</option>
            </select>
          </div>
        </div>

        <div className="form-field">
          <label className="form-label">Primary Soil Type</label>
          <div className="soil-chips">
            {soilTypes.map((soil) => (
              <button
                key={soil}
                type="button"
                className={`soil-chip ${selectedSoil === soil ? 'soil-chip--active' : ''}`}
                onClick={() => setSelectedSoil(soil)}
              >
                {soil}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Preferences */}
      <div className="section-card">
        <h2 className="section-title" style={{ marginBottom: 16 }}>Preferences</h2>

        <div className="pref-row">
          <div className="pref-icon">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#2E7D32" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" />
              <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
              <line x1="12" y1="19" x2="12" y2="23" />
              <line x1="8" y1="23" x2="16" y2="23" />
            </svg>
          </div>
          <div className="pref-info">
            <p className="pref-title">Voice Assistance</p>
            <p className="pref-desc">Enable spoken AI insights and alerts in your regional language.</p>
          </div>
          <button
            type="button"
            className={`toggle-switch ${voiceAssistance ? 'toggle-switch--on' : ''}`}
            onClick={() => setVoiceAssistance(!voiceAssistance)}
            role="switch"
            aria-checked={voiceAssistance}
          >
            <span className="toggle-knob" />
          </button>
        </div>

        <p className="pref-lang">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#2E7D32" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="10" />
            <line x1="2" y1="12" x2="22" y2="12" />
            <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
          </svg>
          Currently set to: Marathi
        </p>
      </div>

      {/* Save Button */}
      <button
        className="btn btn-primary"
        id="btn-save-profile"
        onClick={handleSave}
        disabled={loading}
        style={{ opacity: loading ? 0.7 : 1, marginTop: 8 }}
      >
        {loading ? 'Saving...' : 'Save & Explore Dashboard →'}
      </button>
    </div>
  );
}
