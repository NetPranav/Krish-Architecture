'use client';

import { useRouter } from 'next/navigation';

interface TopBarProps {
  location: string;
  weather: string;
}

export default function TopBar({ location, weather }: TopBarProps) {
  const router = useRouter();

  return (
    <div className="top-bar">
      <div className="top-bar-left">
        <div
          className="top-bar-avatar"
          onClick={() => router.push('/profile')}
          role="button"
          tabIndex={0}
          style={{ cursor: 'pointer' }}
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
            <circle cx="12" cy="7" r="4" />
          </svg>
        </div>
        <div>
          <p className="top-bar-location">{location}</p>
          <p className="top-bar-weather">{weather}</p>
        </div>
      </div>
      <button className="top-bar-bell" aria-label="Notifications" onClick={() => router.push('/alerts')}>
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
          <path d="M13.73 21a2 2 0 0 1-3.46 0" />
        </svg>
      </button>
    </div>
  );
}
