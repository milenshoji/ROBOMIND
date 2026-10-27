// App.tsx
import { useState, useCallback } from 'react';
import Header from './components/Header';
import SimulationCanvas from './components/SimulationCanvas';
import ControlPanel from './components/ControlPanel';
import StatusPanel from './components/StatusPanel';
import { useSimulation } from './hooks/useSimulation';
import './App.css';

export default function App() {
  const {
    state,
    connected,
    error,
    startMission,
    navigateTo,
    pauseMission,
    resumeMission,
    stopMission,
    resetSimulation,
    addObstacle,
    removeObstacle,
    setSpeed,
  } = useSimulation();

  const [clickMode, setClickMode] = useState<'obstacle' | null>(null);

  const handleCellClick = useCallback((col: number, row: number) => {
    if (clickMode === 'obstacle') {
      addObstacle(col, row, true);
    }
  }, [clickMode, addObstacle]);

  if (!state) {
    return (
      <div className="loading-screen">
        <div className="loading-spinner" />
        <p>{error ? `Backend offline — ${error}` : 'Connecting to RoboMind backend…'}</p>
      </div>
    );
  }

  const { robot, environment, running, paused, events } = state;

  return (
    <div className="app-layout">
      <Header connected={connected} robotStatus={robot.status} />

      {error && (
        <div className="error-banner" role="alert">
          ⚠️ {error}
        </div>
      )}

      <main className="main-area">
        {/* Left: Controls */}
        <aside className="left-panel">
          <ControlPanel
            running={running}
            paused={paused}
            robotStatus={robot.status}
            speed={robot.speed}
            onStart={startMission}
            onNavigateTo={navigateTo}
            onPause={pauseMission}
            onResume={resumeMission}
            onStop={stopMission}
            onReset={resetSimulation}
            onAddObstacle={addObstacle}
            onSetSpeed={setSpeed}
          />
        </aside>

        {/* Center: Canvas */}
        <section className="canvas-area" id="canvas-area">
          <div className="canvas-toolbar">
            <span className="canvas-label">Interactive Virtual Office</span>
            <button
              id="btn-click-obstacle"
              className={`toolbar-btn ${clickMode === 'obstacle' ? 'active' : ''}`}
              onClick={() => setClickMode(m => m === 'obstacle' ? null : 'obstacle')}
              title="Click on map to place obstacles"
            >
              🚧 {clickMode === 'obstacle' ? 'Click map to place' : 'Click-to-Place Obstacle'}
            </button>
          </div>
          <div className="canvas-wrap">
            <SimulationCanvas
              environment={environment}
              robot={robot}
              onCellClick={clickMode ? handleCellClick : undefined}
            />
          </div>
          {/* Map Legend */}
          <div className="map-legend">
            {[
              { color: '#1a2744', label: 'Reception' },
              { color: '#1f2937', label: 'Storage' },
              { color: '#1a2535', label: 'Laboratory' },
              { color: '#1e3a2f', label: 'Charging' },
              { color: '#161b27', label: 'Corridor' },
              { color: '#0d1117', label: 'Wall' },
              { color: '#7c2d12', label: 'Obstacle' },
              { color: '#10b981', label: 'Robot' },
              { color: '#3b82f6', label: 'Planned Path' },
              { color: '#34d399', label: 'Travelled' },
            ].map(({ color, label }) => (
              <div key={label} className="legend-item">
                <div className="legend-swatch" style={{ background: color }} />
                <span>{label}</span>
              </div>
            ))}
          </div>
        </section>

        {/* Right: Status */}
        <aside className="right-panel">
          <StatusPanel robot={robot} events={events} environment={environment} />
        </aside>
      </main>
    </div>
  );
}
