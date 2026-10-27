// components/Header.tsx
interface Props {
  connected: boolean;
  robotStatus: string;
}

const STATUS_LABELS: Record<string, string> = {
  IDLE:       'Idle',
  MOVING:     'Moving',
  PAUSED:     'Paused',
  STOPPED:    'Stopped',
  BLOCKED:    'Blocked',
  REPLANNING: 'Replanning',
  SEARCHING:  'Searching',
  PICKING_UP: 'Picking Up',
  CARRYING:   'Carrying',
  DELIVERING: 'Delivering',
  CHARGING:   'Charging',
  ERROR:      'Error',
};

const STATUS_COLORS: Record<string, string> = {
  IDLE:       '#3b82f6',
  MOVING:     '#10b981',
  PAUSED:     '#f59e0b',
  STOPPED:    '#6b7280',
  BLOCKED:    '#ef4444',
  REPLANNING: '#8b5cf6',
  ERROR:      '#ef4444',
};

export default function Header({ connected, robotStatus }: Props) {
  const statusColor = STATUS_COLORS[robotStatus] ?? '#6b7280';
  const statusLabel = STATUS_LABELS[robotStatus] ?? robotStatus;

  return (
    <header className="app-header" id="app-header">
      <div className="header-brand">
        <div className="logo-icon">
          <svg width="32" height="32" viewBox="0 0 32 32" fill="none" aria-hidden="true">
            <rect width="32" height="32" rx="8" fill="#10b981" fillOpacity="0.15"/>
            <circle cx="16" cy="16" r="8" stroke="#10b981" strokeWidth="2"/>
            <circle cx="16" cy="16" r="3" fill="#10b981"/>
            <line x1="16" y1="4" x2="16" y2="8" stroke="#10b981" strokeWidth="2" strokeLinecap="round"/>
            <line x1="16" y1="24" x2="16" y2="28" stroke="#10b981" strokeWidth="2" strokeLinecap="round"/>
            <line x1="4" y1="16" x2="8" y2="16" stroke="#10b981" strokeWidth="2" strokeLinecap="round"/>
            <line x1="24" y1="16" x2="28" y2="16" stroke="#10b981" strokeWidth="2" strokeLinecap="round"/>
          </svg>
        </div>
        <div>
          <h1 className="brand-title">RoboMind</h1>
          <p className="brand-subtitle">Robotic Digital Twin Platform · Phase 1</p>
        </div>
      </div>

      <div className="header-status">
        <div className="status-chip" style={{ '--chip-color': statusColor } as React.CSSProperties}>
          <span className="status-dot" style={{ background: statusColor }} />
          <span>Robot: {statusLabel}</span>
        </div>
        <div className={`connection-chip ${connected ? 'connected' : 'disconnected'}`}>
          <span className="status-dot" />
          <span>{connected ? 'Backend Connected' : 'Backend Offline'}</span>
        </div>
      </div>
    </header>
  );
}
