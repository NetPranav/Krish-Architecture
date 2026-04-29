'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import TopBar from '@/app/components/ui/TopBar';

type AlertCategory = 'Weather' | 'Disease' | 'Mandi' | 'Irrigation';

interface AlertItem {
  id: string;
  title: string;
  desc: string;
  time: string;
  category: AlertCategory;
  severity: 'critical' | 'warning' | 'info';
  group: string;
  route?: string;
}

const alerts: AlertItem[] = [
  {
    id: '1', title: 'Severe Weather Warning', time: '10:45 AM',
    desc: 'Heavy rainfall and thunderstorms expected in your area within the next 2 hours. Secure loose equipment.',
    category: 'Weather', severity: 'critical', group: 'TODAY', route: '/weather',
  },
  {
    id: '2', title: 'Pest Risk Elevated', time: '08:15 AM',
    desc: 'Conditions are highly favorable for Aphid infestation in Plot B (Tomatoes). Consider preventative spraying.',
    category: 'Disease', severity: 'warning', group: 'TODAY', route: '/scanner/capture',
  },
  {
    id: '3', title: 'Price Surge', time: 'Yesterday, 4:30 PM',
    desc: 'Onion prices at Nashik Mandi have increased by 15% today. Current rate: ₹2,400/qtl.',
    category: 'Mandi', severity: 'info', group: 'YESTERDAY', route: '/mandi',
  },
  {
    id: '4', title: 'Low Soil Moisture', time: 'Yesterday, 9:00 AM',
    desc: 'Soil moisture in Plot A (Wheat) has dropped below 30%. Irrigation recommended soon.',
    category: 'Irrigation', severity: 'warning', group: 'YESTERDAY', route: '/alerts/irrigation',
  },
  {
    id: '5', title: 'Market Summary', time: 'Mon, 10:00 AM',
    desc: 'Weekly market trends report is now available for download.',
    category: 'Mandi', severity: 'info', group: 'THIS WEEK', route: '/mandi',
  },
];

const categoryColors: Record<AlertCategory, { bg: string; border: string; icon: string }> = {
  Weather: { bg: '#FFEBEE', border: '#EF5350', icon: '#C62828' },
  Disease: { bg: '#FFF8E1', border: '#FFB300', icon: '#E65100' },
  Mandi: { bg: '#E8F5E9', border: '#66BB6A', icon: '#2E7D32' },
  Irrigation: { bg: '#FFF3E0', border: '#FFA726', icon: '#E65100' },
};

function AlertIcon({ category }: { category: AlertCategory }) {
  const color = categoryColors[category].icon;
  switch (category) {
    case 'Weather':
      return (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2">
          <path d="M18 10h-1.26A8 8 0 1 0 9 20h9a5 5 0 0 0 0-10z" />
        </svg>
      );
    case 'Disease':
      return (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2">
          <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
        </svg>
      );
    case 'Mandi':
      return (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2">
          <rect x="2" y="7" width="20" height="14" rx="2" ry="2" />
          <path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16" />
        </svg>
      );
    case 'Irrigation':
      return (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2">
          <path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z" />
        </svg>
      );
  }
}

export default function AlertsPage() {
  const router = useRouter();
  const [readIds, setReadIds] = useState<Set<string>>(new Set());

  const markAllRead = () => setReadIds(new Set(alerts.map(a => a.id)));
  const groups = ['TODAY', 'YESTERDAY', 'THIS WEEK'];

  return (
    <div className="dashboard-page">
      <TopBar location="Nashik, MH" weather="" />

      <div style={{ padding: '4px 16px 8px' }}>
        <h1 className="apmc-title">Alerts</h1>
      </div>

      {/* Action Bar */}
      <div className="alerts-action-bar">
        <button className="alerts-filter-btn">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="4" y1="21" x2="4" y2="14" /><line x1="4" y1="10" x2="4" y2="3" />
            <line x1="12" y1="21" x2="12" y2="12" /><line x1="12" y1="8" x2="12" y2="3" />
            <line x1="20" y1="21" x2="20" y2="16" /><line x1="20" y1="12" x2="20" y2="3" />
          </svg>
          Filter by Urgency
        </button>
        <button className="alerts-mark-btn" onClick={markAllRead}>
          Mark all as read
        </button>
      </div>

      {/* Alert Groups */}
      {groups.map(group => {
        const groupAlerts = alerts.filter(a => a.group === group);
        if (groupAlerts.length === 0) return null;
        return (
          <div key={group}>
            <p className="alerts-group-label">{group}</p>
            {groupAlerts.map(alert => {
              const colors = categoryColors[alert.category];
              const isRead = readIds.has(alert.id);
              return (
                <div
                  key={alert.id}
                  className={`alert-timeline-card ${isRead ? 'alert-timeline-card--read' : ''}`}
                  style={{ borderLeftColor: colors.border }}
                  onClick={() => {
                    setReadIds(prev => new Set(prev).add(alert.id));
                    if (alert.route) router.push(alert.route);
                  }}
                  role="button"
                  tabIndex={0}
                >
                  <div className="alert-timeline-icon" style={{ background: colors.bg }}>
                    <AlertIcon category={alert.category} />
                  </div>
                  <div className="alert-timeline-body">
                    <div className="alert-timeline-top">
                      <h3 className={`alert-timeline-title ${alert.severity === 'critical' ? 'alert-timeline-title--critical' : alert.severity === 'warning' ? 'alert-timeline-title--warning' : ''}`}>
                        {alert.title}
                      </h3>
                      <span className="alert-timeline-time">{alert.time}</span>
                    </div>
                    <p className="alert-timeline-desc">{alert.desc}</p>
                    <span className="alert-timeline-tag">{alert.category}</span>
                  </div>
                </div>
              );
            })}
          </div>
        );
      })}

      {/* Navigate to Irrigation Hub */}
      <div style={{ padding: '8px 16px 16px' }}>
        <button
          className="product-cta-btn product-cta-btn--primary"
          onClick={() => router.push('/alerts/irrigation')}
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z" />
          </svg>
          Open Irrigation Hub
        </button>
      </div>
    </div>
  );
}
