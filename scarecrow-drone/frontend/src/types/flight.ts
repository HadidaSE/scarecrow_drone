export interface Flight {
  id: string;
  date: string;
  duration: number; // in seconds
  pigeonsDetected: number;
  status: 'completed' | 'in_progress' | 'failed';
  startTime: string;
  endTime?: string;
}

export interface DroneStatus {
  isConnected: boolean;
  isFlying: boolean;
  currentFlight?: Flight;
}

export interface ConnectionStatus {
  wifiConnected: boolean;
  sshConnected: boolean;
  droneReady: boolean;
}

export interface FlightSummary {
  flightId: string;
  droneId: number;
  duration: number;
  avgSpeed: number;
  avgAltitude: number;
  status: string;
  date: string;
  startTime: string;
  endTime: string;
}
