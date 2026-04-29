'use client';

interface StatusBannerProps {
  type: 'success' | 'warning' | 'info';
  title: string;
  message: string;
}

export default function StatusBanner({ type, title, message }: StatusBannerProps) {
  const styles: Record<string, { bg: string; border: string; icon: string; color: string }> = {
    success: { bg: '#E8F5E9', border: '#A5D6A7', icon: '#2E7D32', color: '#1B5E20' },
    warning: { bg: '#FFF3E0', border: '#FFCC80', icon: '#E65100', color: '#BF360C' },
    info: { bg: '#E3F2FD', border: '#90CAF9', icon: '#1565C0', color: '#0D47A1' },
  };

  const s = styles[type];

  const icons: Record<string, React.ReactNode> = {
    success: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke={s.icon} strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
        <polyline points="22 4 12 14.01 9 11.01" />
      </svg>
    ),
    warning: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke={s.icon} strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
        <line x1="12" y1="9" x2="12" y2="13" />
        <line x1="12" y1="17" x2="12.01" y2="17" />
      </svg>
    ),
    info: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke={s.icon} strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="10" />
        <line x1="12" y1="16" x2="12" y2="12" />
        <line x1="12" y1="8" x2="12.01" y2="8" />
      </svg>
    ),
  };

  return (
    <div
      className="status-banner"
      style={{ background: s.bg, borderColor: s.border }}
    >
      <span className="status-banner-icon">{icons[type]}</span>
      <div>
        <p className="status-banner-title" style={{ color: s.color }}>{title}</p>
        <p className="status-banner-msg" style={{ color: s.color }}>{message}</p>
      </div>
    </div>
  );
}
