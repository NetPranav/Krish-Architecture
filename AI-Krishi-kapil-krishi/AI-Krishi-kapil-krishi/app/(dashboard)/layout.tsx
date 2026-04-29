'use client';

import { usePathname } from 'next/navigation';
import BottomNav from '@/app/components/ui/BottomNav';
import MitraFab from '@/app/components/ui/MitraFab';

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const hideFab = pathname === '/mitra';

  return (
    <div className="app-shell">
      <div className="app-content">
        {children}
      </div>
      {!hideFab && <MitraFab />}
      <BottomNav />
    </div>
  );
}
