// types/simulation.ts

export interface Room {
  label: string;
  rect: [number, number, number, number]; // col_start, row_start, col_end, row_end
  centre: [number, number];
}

export interface SimObject {
  id: string;
  label: string;
  position: [number, number]; // [col, row]
  color: string;
  pickable: boolean;
  picked_up: boolean;
  delivered: boolean;
}

export interface Obstacle {
  id: string;
  position: [number, number];
  is_dynamic: boolean;
  label: string;
}

export interface Environment {
  width: number;
  height: number;
  grid: number[][];
  rooms: Record<string, Room>;
  objects: Record<string, SimObject>;
  obstacles: Record<string, Obstacle>;
}

export interface RobotState {
  position: [number, number];
  col: number;
  row: number;
  orientation: number;
  status: string;
  battery: number;
  carried_object_id: string | null;
  path: [number, number][];
  path_index: number;
  destination: [number, number] | null;
  travelled_path: [number, number][];
  mission_id: string | null;
  current_task: string;
  steps_taken: number;
  replanning_count: number;
  speed: number;
}

export interface SimEvent {
  id: string;
  timestamp: number;
  category: string;
  message: string;
  data: Record<string, unknown>;
}

export interface SimulationState {
  robot: RobotState;
  environment: Environment;
  running: boolean;
  paused: boolean;
  events: SimEvent[];
}

// Cell type enum matching backend
export enum CellType {
  FLOOR = 0,
  WALL = 1,
  OBSTACLE_STATIC = 2,
  OBSTACLE_DYNAMIC = 3,
  CHARGING_STATION = 4,
  RECEPTION = 5,
  STORAGE = 6,
  LABORATORY = 7,
  CORRIDOR = 8,
}
