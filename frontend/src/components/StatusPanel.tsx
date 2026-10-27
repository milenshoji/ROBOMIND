// components/StatusPanel.tsx
import { RobotState, SimEvent, Environment } from '../types/simulation';

interface Props {
  robot: RobotState;
  events: SimEvent[];
  environment: Environment;
}

function BatteryBar({ level }: { level: number }) {
  const pct = Math.max(0, Math.min(100, level));
  const color = pct > 50 ? '#10b981' : pct > 20 ? '#f59e0b' : '#ef4444';
  return (
    <div className="battery-bar-wrap">
      <div className="battery-bar-track">
        <div className="battery-bar-fill" style={{ width: `${pct}%`, background: color }} />
      </div>
      <span style={{ color }}>{pct.toFixed(1)}%</span>
    </div>
  );
}

function Telemetry({ label, value, mono = false }: { label: string; value: string | number; mono?: boolean }) {
  return (
    <div className="telemetry-row">
      <span className="tele-label">{label}</span>
      <span className={`tele-value ${mono ? 'mono' : ''}`}>{value}</span>
    </div>
  );
}

const EVENT_ICONS: Record<string, string> = {
  SYSTEM:     '🔧',
  MISSION:    '🎯',
  NAVIGATION: '🗺️',
  SAFETY:     '⚠️',
  OBSTACLE:   '🚧',
};

export default function StatusPanel({ robot, events, environment }: Props) {
  const sortedEvents = [...events].reverse().slice(0, 20);

  const obstacleCount = Object.keys(environment.obstacles).length;
  const objectCount = Object.values(environment.objects).filter(o => !o.picked_up).length;

  return (
    <div className="status-panel" id="status-panel">
      {/* Telemetry */}
      <section className="panel-section">
        <h2 className="section-title">Robot Telemetry</h2>
        <div className="telemetry-grid">
          <Telemetry label="Status" value={robot.status} />
          <Telemetry label="Task" value={robot.current_task} />
          <Telemetry label="Position" value={`(${Math.round(robot.col)}, ${Math.round(robot.row)})`} mono />
          <Telemetry label="Orientation" value={`${Math.round(robot.orientation)}°`} mono />
          <Telemetry label="Steps Taken" value={robot.steps_taken} mono />
          <Telemetry label="Path Remaining" value={Math.max(0, robot.path.length - robot.path_index)} mono />
          <Telemetry label="Replanning Count" value={robot.replanning_count} mono />
          <Telemetry label="Carrying" value={robot.carried_object_id ?? '—'} />
          <Telemetry label="Obstacles" value={obstacleCount} />
          <Telemetry label="Objects on Map" value={objectCount} />
          <div className="telemetry-row">
            <span className="tele-label">Battery</span>
            <BatteryBar level={robot.battery} />
          </div>
        </div>
      </section>

      {/* Active obstacles list */}
      {obstacleCount > 0 && (
        <section className="panel-section">
          <h2 className="section-title">Active Obstacles</h2>
          <div className="obstacle-list">
            {Object.values(environment.obstacles).map(obs => (
              <div key={obs.id} className="obstacle-chip">
                <span className={`obs-type ${obs.is_dynamic ? 'dynamic' : 'static'}`}>
                  {obs.is_dynamic ? '🔴' : '⬛'}
                </span>
                <span>{obs.label}</span>
                <span className="obs-pos">({obs.position[0]},{obs.position[1]})</span>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Event timeline */}
      <section className="panel-section event-section">
        <h2 className="section-title">Event Timeline</h2>
        <div className="event-log" id="event-log">
          {sortedEvents.length === 0 && (
            <p className="empty-log">No events yet. Start a mission.</p>
          )}
          {sortedEvents.map(ev => (
            <div key={ev.id} className={`event-entry cat-${ev.category.toLowerCase()}`}>
              <span className="ev-icon">{EVENT_ICONS[ev.category] ?? '📝'}</span>
              <div className="ev-body">
                <span className="ev-msg">{ev.message}</span>
                <span className="ev-time">{new Date(ev.timestamp * 1000).toLocaleTimeString()}</span>
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
