'use client';

import { useRouter } from 'next/navigation';

export default function MitraFab() {
  const router = useRouter();

  return (
    <button
      className="mitra-fab"
      onClick={() => router.push('/mitra')}
      aria-label="Open Mitra AI Assistant"
    >
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
        <line x1="4" y1="8" x2="4" y2="16" />
        <line x1="8" y1="5" x2="8" y2="19" />
        <line x1="12" y1="3" x2="12" y2="21" />
        <line x1="16" y1="5" x2="16" y2="19" />
        <line x1="20" y1="8" x2="20" y2="16" />
      </svg>
    </button>
  );
}
