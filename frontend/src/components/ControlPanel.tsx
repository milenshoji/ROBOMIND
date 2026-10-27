// components/ControlPanel.tsx
import { useState } from 'react';

interface Props {
  running: boolean;
  paused: boolean;
  robotStatus: string;
  speed: number;
  onStart: (waypoints?: number[][]) => void;
  onNavigateTo: (location: string) => void;
  onPause: () => void;
  onResume: () => void;
  onStop: () => void;
  onReset: () => void;
  onAddObstacle: (col: number, row: number) => void;
  onSetSpeed: (s: number) => void;
}

const QUICK_DESTINATIONS = [
  { key: 'reception',       label: '🏢 Reception' },
  { key: 'storage_room',    label: '📦 Storage Room' },
  { key: 'laboratory',      label: '🔬 Laboratory' },
  { key: 'charging_station',label: '⚡ Charging Station' },
];

export default function ControlPanel({
  running, paused, robotStatus, speed,
  onStart, onNavigateTo, onPause, onResume, onStop, onReset, onAddObstacle, onSetSpeed,
}: Props) {
  const [obsCol, setObsCol] = useState('');
  const [obsRow, setObsRow] = useState('');

  const canStart = !running;
  const canPause = running && !paused;
  const canResume = running && paused;
  const canStop = running;

  function handleAddObs() {
    const c = parseInt(obsCol);
    const r = parseInt(obsRow);
    if (!isNaN(c) && !isNaN(r)) {
      onAddObstacle(c, r);
      setObsCol('');
      setObsRow('');
    }
  }

  return (
    <div className="control-panel" id="control-panel">
      <section className="panel-section">
        <h2 className="section-title">Quick Navigate</h2>
        <div className="quick-nav-grid">
          {QUICK_DESTINATIONS.map(({ key, label }) => (
            <button
              key={key}
              id={`nav-${key}`}
              className="quick-nav-btn"
              onClick={() => onNavigateTo(key)}
              disabled={running && !paused}
            >
              {label}
            </button>
          ))}
        </div>
      </section>

      <section className="panel-section">
        <h2 className="section-title">Mission Controls</h2>
        <div className="mission-controls">
          <button
            id="btn-start"
            className="ctrl-btn primary"
            onClick={() => onStart()}
            disabled={!canStart}
          >
            ▶ Start Demo Mission
          </button>
          <div className="ctrl-row">
            <button
              id="btn-pause"
              className="ctrl-btn secondary"
              onClick={onPause}
              disabled={!canPause}
            >
              ⏸ Pause
            </button>
            <button
              id="btn-resume"
              className="ctrl-btn secondary"
              onClick={onResume}
              disabled={!canResume}
            >
              ▶ Resume
            </button>
          </div>
          <button
            id="btn-stop"
            className="ctrl-btn danger"
            onClick={onStop}
            disabled={!canStop}
          >
            ⏹ Stop
          </button>
          <button
            id="btn-reset"
            className="ctrl-btn ghost"
            onClick={onReset}
          >
            ↺ Reset Simulation
          </button>
        </div>
      </section>

      <section className="panel-section">
        <h2 className="section-title">
          Simulation Speed
          <span className="speed-badge">{speed.toFixed(1)}×</span>
        </h2>
        <input
          id="speed-slider"
          type="range"
          min="0.5"
          max="5"
          step="0.5"
          value={speed}
          onChange={(e) => onSetSpeed(parseFloat(e.target.value))}
          className="speed-slider"
        />
        <div className="speed-labels">
          <span>0.5×</span><span>5×</span>
        </div>
      </section>

      <section className="panel-section">
        <h2 className="section-title">Add Dynamic Obstacle</h2>
        <p className="section-hint">Enter grid coordinates or click on the map</p>
        <div className="obs-inputs">
          <input
            id="obs-col"
            type="number"
            placeholder="Col"
            value={obsCol}
            onChange={e => setObsCol(e.target.value)}
            className="coord-input"
          />
          <input
            id="obs-row"
            type="number"
            placeholder="Row"
            value={obsRow}
            onChange={e => setObsRow(e.target.value)}
            className="coord-input"
          />
          <button
            id="btn-add-obstacle"
            className="ctrl-btn warning"
            onClick={handleAddObs}
          >
            + Add
          </button>
        </div>
      </section>
    </div>
  );
}
