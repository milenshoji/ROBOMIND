// hooks/useSimulation.ts
import { useState, useEffect, useCallback, useRef } from 'react';
import { SimulationState } from '../types/simulation';

const API_BASE = '';   // Vite proxies /api → localhost:8000
const POLL_MS = 150;   // 150ms polling interval

interface UseSimulationReturn {
  state: SimulationState | null;
  connected: boolean;
  error: string | null;
  startMission: (waypoints?: number[][]) => Promise<void>;
  navigateTo: (location: string) => Promise<void>;
  pauseMission: () => Promise<void>;
  resumeMission: () => Promise<void>;
  stopMission: () => Promise<void>;
  resetSimulation: () => Promise<void>;
  addObstacle: (col: number, row: number, isDynamic?: boolean) => Promise<void>;
  removeObstacle: (obstacleId: string) => Promise<void>;
  setSpeed: (speed: number) => Promise<void>;
}

async function apiFetch(path: string, options?: RequestInit) {
  const resp = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!resp.ok) {
    const body = await resp.json().catch(() => ({}));
    throw new Error(body.detail || `HTTP ${resp.status}`);
  }
  return resp.json();
}

export function useSimulation(): UseSimulationReturn {
  const [state, setState] = useState<SimulationState | null>(null);
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const timerRef = useRef<number | null>(null);

  const poll = useCallback(async () => {
    try {
      const data = await apiFetch('/api/state');
      setState(data as SimulationState);
      setConnected(true);
      setError(null);
    } catch (e) {
      setConnected(false);
      setError((e as Error).message);
    }
  }, []);

  useEffect(() => {
    poll();
    timerRef.current = window.setInterval(poll, POLL_MS);
    return () => {
      if (timerRef.current !== null) window.clearInterval(timerRef.current);
    };
  }, [poll]);

  const startMission = useCallback(async (waypoints?: number[][]) => {
    try {
      await apiFetch('/api/missions', {
        method: 'POST',
        body: JSON.stringify({ waypoints }),
      });
    } catch (e) {
      setError((e as Error).message);
    }
  }, []);

  const navigateTo = useCallback(async (location: string) => {
    try {
      await apiFetch('/api/missions/navigate', {
        method: 'POST',
        body: JSON.stringify({ location }),
      });
    } catch (e) {
      setError((e as Error).message);
    }
  }, []);

  const pauseMission = useCallback(async () => {
    await apiFetch('/api/missions/pause', { method: 'POST', body: '{}' });
  }, []);

  const resumeMission = useCallback(async () => {
    await apiFetch('/api/missions/resume', { method: 'POST', body: '{}' });
  }, []);

  const stopMission = useCallback(async () => {
    await apiFetch('/api/missions/stop', { method: 'POST', body: '{}' });
  }, []);

  const resetSimulation = useCallback(async () => {
    await apiFetch('/api/simulation/reset', { method: 'POST', body: '{}' });
  }, []);

  const addObstacle = useCallback(async (col: number, row: number, isDynamic = true) => {
    await apiFetch('/api/obstacles', {
      method: 'POST',
      body: JSON.stringify({ col, row, is_dynamic: isDynamic }),
    });
  }, []);

  const removeObstacle = useCallback(async (obstacleId: string) => {
    await apiFetch(`/api/obstacles/${obstacleId}`, { method: 'DELETE' });
  }, []);

  const setSpeed = useCallback(async (speed: number) => {
    await apiFetch('/api/simulation/speed', {
      method: 'POST',
      body: JSON.stringify({ speed }),
    });
  }, []);

  return {
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
  };
}
