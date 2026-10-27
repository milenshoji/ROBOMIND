// components/SimulationCanvas.tsx
import { useEffect, useRef, useCallback } from 'react';
import { Environment, RobotState, CellType } from '../types/simulation';

interface Props {
  environment: Environment;
  robot: RobotState;
  onCellClick?: (col: number, row: number) => void;
}

// Visual palette
const CELL_COLORS: Record<number, string> = {
  [CellType.FLOOR]:            '#1a1f2e',
  [CellType.WALL]:             '#0d1117',
  [CellType.OBSTACLE_STATIC]:  '#4a3728',
  [CellType.OBSTACLE_DYNAMIC]: '#7c2d12',
  [CellType.CHARGING_STATION]: '#1e3a2f',
  [CellType.RECEPTION]:        '#1a2744',
  [CellType.STORAGE]:          '#1f2937',
  [CellType.LABORATORY]:       '#1a2535',
  [CellType.CORRIDOR]:         '#161b27',
};

const CELL_BORDER: Record<number, string> = {
  [CellType.FLOOR]:            '#232a3a',
  [CellType.WALL]:             '#080c12',
  [CellType.OBSTACLE_STATIC]:  '#6b4c3b',
  [CellType.OBSTACLE_DYNAMIC]: '#ef4444',
  [CellType.CHARGING_STATION]: '#22c55e',
  [CellType.RECEPTION]:        '#3b82f6',
  [CellType.STORAGE]:          '#8b5cf6',
  [CellType.LABORATORY]:       '#06b6d4',
  [CellType.CORRIDOR]:         '#1e2534',
};

const ROOM_LABEL_COLORS: Record<string, string> = {
  reception:        '#60a5fa',
  storage_room:     '#a78bfa',
  laboratory:       '#22d3ee',
  corridor_h:       '#475569',
  corridor_v:       '#475569',
  charging_station: '#4ade80',
};

export default function SimulationCanvas({ environment, robot, onCellClick }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animFrameRef = useRef<number>(0);
  const robotAnimRef = useRef({ col: robot.col, row: robot.row, orientation: robot.orientation });

  // Lerp robot position for smooth animation
  useEffect(() => {
    robotAnimRef.current.col += (robot.col - robotAnimRef.current.col) * 0.35;
    robotAnimRef.current.row += (robot.row - robotAnimRef.current.row) * 0.35;
    robotAnimRef.current.orientation = robot.orientation;
  });

  const draw = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const W = canvas.width;
    const H = canvas.height;
    const cols = environment.width;
    const rows = environment.height;
    const cellW = W / cols;
    const cellH = H / rows;
    const cellSize = Math.min(cellW, cellH);

    ctx.clearRect(0, 0, W, H);

    // ── Draw cells ──────────────────────────
    const grid = environment.grid;
    for (let r = 0; r < rows; r++) {
      for (let c = 0; c < cols; c++) {
        const ct = grid[r][c];
        const x = c * cellSize;
        const y = r * cellSize;

        ctx.fillStyle = CELL_COLORS[ct] ?? '#111';
        ctx.fillRect(x, y, cellSize, cellSize);

        ctx.strokeStyle = CELL_BORDER[ct] ?? '#222';
        ctx.lineWidth = 0.5;
        ctx.strokeRect(x + 0.25, y + 0.25, cellSize - 0.5, cellSize - 0.5);
      }
    }

    // ── Planned path ──────────────────────
    if (robot.path && robot.path.length > 0) {
      ctx.beginPath();
      ctx.strokeStyle = 'rgba(59,130,246,0.45)';
      ctx.lineWidth = cellSize * 0.18;
      ctx.lineCap = 'round';
      ctx.lineJoin = 'round';
      for (let i = robot.path_index; i < robot.path.length; i++) {
        const [pc, pr] = robot.path[i];
        const px = pc * cellSize + cellSize / 2;
        const py = pr * cellSize + cellSize / 2;
        if (i === robot.path_index) ctx.moveTo(px, py);
        else ctx.lineTo(px, py);
      }
      ctx.stroke();

      // Destination marker
      const dest = robot.path[robot.path.length - 1];
      if (dest) {
        const [dc, dr] = dest;
        ctx.fillStyle = 'rgba(59,130,246,0.25)';
        ctx.beginPath();
        ctx.arc(dc * cellSize + cellSize / 2, dr * cellSize + cellSize / 2, cellSize * 0.45, 0, Math.PI * 2);
        ctx.fill();
        ctx.strokeStyle = '#3b82f6';
        ctx.lineWidth = 1.5;
        ctx.stroke();
      }
    }

    // ── Travelled path ────────────────────
    if (robot.travelled_path && robot.travelled_path.length > 1) {
      ctx.beginPath();
      ctx.strokeStyle = 'rgba(16,185,129,0.35)';
      ctx.lineWidth = cellSize * 0.12;
      ctx.lineCap = 'round';
      ctx.lineJoin = 'round';
      robot.travelled_path.forEach(([tc, tr], i) => {
        const tx = tc * cellSize + cellSize / 2;
        const ty = tr * cellSize + cellSize / 2;
        if (i === 0) ctx.moveTo(tx, ty);
        else ctx.lineTo(tx, ty);
      });
      ctx.stroke();
    }

    // ── Room labels ───────────────────────
    ctx.font = `bold ${Math.max(8, cellSize * 0.6)}px Inter, sans-serif`;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    for (const [key, room] of Object.entries(environment.rooms)) {
      const [cc, cr] = room.centre;
      const x = cc * cellSize + cellSize / 2;
      const y = cr * cellSize + cellSize / 2;
      ctx.fillStyle = (ROOM_LABEL_COLORS[key] ?? '#888') + 'cc';
      ctx.fillText(room.label, x, y);
    }

    // ── Objects ───────────────────────────
    for (const obj of Object.values(environment.objects)) {
      if (obj.picked_up) continue;
      const [oc, or_] = obj.position;
      const ox = oc * cellSize + cellSize / 2;
      const oy = or_ * cellSize + cellSize / 2;
      const r = cellSize * 0.28;
      ctx.fillStyle = obj.color;
      ctx.beginPath();
      ctx.roundRect(ox - r, oy - r, r * 2, r * 2, 3);
      ctx.fill();
      ctx.strokeStyle = 'rgba(255,255,255,0.5)';
      ctx.lineWidth = 1;
      ctx.stroke();
    }

    // ── Obstacles ─────────────────────────
    for (const obs of Object.values(environment.obstacles)) {
      const [oc, or_] = obs.position;
      const ox = oc * cellSize;
      const oy = or_ * cellSize;
      // Already colored by cell type, draw a cross on top
      ctx.strokeStyle = obs.is_dynamic ? '#ef4444' : '#b45309';
      ctx.lineWidth = 1.5;
      const m = cellSize * 0.2;
      ctx.beginPath();
      ctx.moveTo(ox + m, oy + m);
      ctx.lineTo(ox + cellSize - m, oy + cellSize - m);
      ctx.moveTo(ox + cellSize - m, oy + m);
      ctx.lineTo(ox + m, oy + cellSize - m);
      ctx.stroke();
    }

    // ── Robot ─────────────────────────────
    const rAnim = robotAnimRef.current;
    const rx = rAnim.col * cellSize + cellSize / 2;
    const ry = rAnim.row * cellSize + cellSize / 2;
    const robotR = cellSize * 0.38;
    const angleRad = (rAnim.orientation * Math.PI) / 180;

    // Glow
    const glow = ctx.createRadialGradient(rx, ry, 0, rx, ry, robotR * 2.2);
    const statusColor = getStatusGlow(robot.status);
    glow.addColorStop(0, statusColor + '55');
    glow.addColorStop(1, 'transparent');
    ctx.fillStyle = glow;
    ctx.beginPath();
    ctx.arc(rx, ry, robotR * 2.2, 0, Math.PI * 2);
    ctx.fill();

    // Body
    ctx.save();
    ctx.translate(rx, ry);
    ctx.rotate(angleRad);

    // Robot body circle
    ctx.beginPath();
    ctx.arc(0, 0, robotR, 0, Math.PI * 2);
    const bodyGrad = ctx.createRadialGradient(-robotR * 0.2, -robotR * 0.2, 0, 0, 0, robotR);
    bodyGrad.addColorStop(0, '#6ee7b7');
    bodyGrad.addColorStop(1, '#059669');
    ctx.fillStyle = bodyGrad;
    ctx.fill();
    ctx.strokeStyle = '#34d399';
    ctx.lineWidth = 1.5;
    ctx.stroke();

    // Direction indicator (arrow tip)
    ctx.beginPath();
    ctx.moveTo(robotR * 0.5, 0);
    ctx.lineTo(robotR * 1.15, -robotR * 0.3);
    ctx.lineTo(robotR * 1.15, robotR * 0.3);
    ctx.closePath();
    ctx.fillStyle = '#fff';
    ctx.fill();

    // Inner eye
    ctx.beginPath();
    ctx.arc(robotR * 0.1, 0, robotR * 0.22, 0, Math.PI * 2);
    ctx.fillStyle = '#064e3b';
    ctx.fill();
    ctx.beginPath();
    ctx.arc(robotR * 0.1, 0, robotR * 0.1, 0, Math.PI * 2);
    ctx.fillStyle = '#a7f3d0';
    ctx.fill();

    ctx.restore();

    // ── Carried object indicator ──────────
    if (robot.carried_object_id) {
      ctx.beginPath();
      ctx.arc(rx + robotR * 0.9, ry - robotR * 0.9, robotR * 0.35, 0, Math.PI * 2);
      ctx.fillStyle = '#FF3B30';
      ctx.fill();
      ctx.strokeStyle = '#fff';
      ctx.lineWidth = 1;
      ctx.stroke();
    }

    animFrameRef.current = requestAnimationFrame(draw);
  }, [environment, robot]);

  useEffect(() => {
    animFrameRef.current = requestAnimationFrame(draw);
    return () => cancelAnimationFrame(animFrameRef.current);
  }, [draw]);

  const handleClick = useCallback((e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!onCellClick) return;
    const canvas = canvasRef.current;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;
    const x = (e.clientX - rect.left) * scaleX;
    const y = (e.clientY - rect.top) * scaleY;
    const cellSize = canvas.width / environment.width;
    const col = Math.floor(x / cellSize);
    const row = Math.floor(y / cellSize);
    onCellClick(col, row);
  }, [environment.width, onCellClick]);

  function getStatusGlow(status: string): string {
    switch (status) {
      case 'MOVING':     return '#10b981';
      case 'PAUSED':     return '#f59e0b';
      case 'STOPPED':    return '#6b7280';
      case 'BLOCKED':    return '#ef4444';
      case 'REPLANNING': return '#8b5cf6';
      case 'IDLE':       return '#3b82f6';
      default:           return '#3b82f6';
    }
  }

  return (
    <canvas
      ref={canvasRef}
      width={environment.width * 28}
      height={environment.height * 28}
      onClick={handleClick}
      style={{ width: '100%', height: '100%', cursor: onCellClick ? 'crosshair' : 'default' }}
      aria-label="RoboMind simulation map"
      id="simulation-canvas"
    />
  );
}
