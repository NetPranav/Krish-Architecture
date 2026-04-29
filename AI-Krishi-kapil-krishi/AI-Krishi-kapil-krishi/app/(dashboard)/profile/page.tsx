'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import TopBar from '@/app/components/ui/TopBar';
import { getProfile } from '@/app/lib/api';
import { changeAppLanguage } from '@/app/lib/TranslationService';

const defaultMenuItems = [
  { icon: 'user', label: 'Personal Information', sub: '', route: '' },
  { icon: 'location', label: 'Farm Location', sub: 'Nashik, Maharashtra', route: '' },
  { icon: 'bell', label: 'Notifications & Alerts', sub: '', route: '/alerts' },
  { icon: 'theme', label: 'Theme', sub: 'System', route: '' },
];

function MenuIcon({ type }: { type: string }) {
  const stroke = 'var(--gray-600)';
  switch (type) {
    case 'user':
      return (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke={stroke} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" /><circle cx="12" cy="7" r="4" />
        </svg>
      );
    case 'location':
      return (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke={stroke} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z" /><circle cx="12" cy="10" r="3" />
        </svg>
      );
    case 'bell':
      return (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke={stroke} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" /><path d="M13.73 21a2 2 0 0 1-3.46 0" />
        </svg>
      );
    case 'theme':
      return (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke={stroke} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
        </svg>
      );
    default:
      return null;
  }
}

export default function ProfilePage() {
  const router = useRouter();
  const [lang, setLang] = useState('English');
  const [profile, setProfile] = useState<any>({
    full_name: 'Ramesh Kumar',
    farm_name: 'Sunrise Farms',
    land_size: 15,
    land_unit: 'Acres',
    membership: 'Premium',
    location: 'Nashik, Maharashtra'
  });
  const [menuItems, setMenuItems] = useState(defaultMenuItems);

  useEffect(() => {
    getProfile().then(res => {
      if (res?.profile) {
        setProfile(res.profile);
        const mapLang: any = { en: 'English', hi: 'हिंदी', mr: 'मराठी' };
        if (res.profile.language && mapLang[res.profile.language]) {
          setLang(mapLang[res.profile.language]);
        }
        setMenuItems(prev => prev.map(m => 
          m.icon === 'location' ? { ...m, sub: res.profile.location || 'Nashik, Maharashtra' } : m
        ));
      }
    }).catch(() => {});
  }, []);

  return (
    <div className="dashboard-page">
      <TopBar location={profile.location || "Nashik, MH"} weather="" />

      {/* Profile Card */}
      <div className="profile-hero-card">
        <div className="profile-avatar">
          <div className="profile-avatar-circle">
            <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="1.5">
              <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" /><circle cx="12" cy="7" r="4" />
            </svg>
          </div>
        </div>
        <h1 className="profile-name">{profile.full_name}</h1>
        <p className="profile-details">{profile.farm_name} • {profile.land_size} {profile.land_unit} • {profile.membership} Member</p>
        <button className="profile-edit-btn">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
            <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
          </svg>
          Edit Profile
        </button>
      </div>

      {/* Account Preferences */}
      <div className="section-card profile-section">
        <p className="profile-section-label">ACCOUNT PREFERENCES</p>
        {menuItems.map((item) => (
          <div
            key={item.label}
            className="profile-menu-row"
            onClick={() => item.route && router.push(item.route)}
            role={item.route ? 'button' : undefined}
            tabIndex={item.route ? 0 : undefined}
          >
            <div className="profile-menu-icon">
              <MenuIcon type={item.icon} />
            </div>
            <div className="profile-menu-content">
              <p className="profile-menu-label">{item.label}</p>
              {item.sub && <p className="profile-menu-sub">{item.sub}</p>}
            </div>
            <div className="profile-menu-right">
              {item.sub && item.icon === 'theme' && (
                <span className="profile-menu-value">{item.sub}</span>
              )}
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--gray-400)" strokeWidth="2">
                <polyline points="9 18 15 12 9 6" />
              </svg>
            </div>
          </div>
        ))}
      </div>

      {/* Language */}
      <div className="section-card profile-section">
        <p className="profile-section-label" style={{ color: 'var(--green-800)' }}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--green-800)" strokeWidth="2">
            <circle cx="12" cy="12" r="10" /><line x1="2" y1="12" x2="22" y2="12" />
            <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
          </svg>
          LANGUAGE
        </p>
        <div className="profile-lang-row">
          {['English', 'हिंदी', 'मराठी'].map(l => (
            <button
              key={l}
              className={`profile-lang-btn ${lang === l ? 'profile-lang-btn--active' : ''}`}
              onClick={async () => {
                setLang(l);
                let code = 'en';
                if (l === 'हिंदी') code = 'hi';
                if (l === 'मराठी') code = 'mr';
                
                // Update frontend translation dynamically
                changeAppLanguage(code);
                
                // Persist setting to the backend
                try {
                  const { updateProfile } = await import('@/app/lib/api');
                  await updateProfile({ language: code });
                } catch (e) {
                  console.error('Failed to save language to backend', e);
                }
              }}
            >
              {l}
            </button>
          ))}
        </div>
        <p className="profile-lang-note">Restart required for some language changes to take effect.</p>
      </div>

      {/* Logout */}
      <div style={{ padding: '0 16px 8px' }}>
        <button className="profile-logout-btn" onClick={() => router.push('/login')}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" /><polyline points="16 17 21 12 16 7" /><line x1="21" y1="12" x2="9" y2="12" />
          </svg>
          Log Out
        </button>
      </div>

      {/* Footer Links */}
      <div className="profile-footer-links">
        <button className="profile-footer-link">Data Privacy</button>
        <button className="profile-footer-link">Terms of Service</button>
        <button className="profile-footer-link">Help Center</button>
      </div>
      <p className="profile-version">App Version 4.2.1 (Build 890)</p>
    </div>
  );
}
