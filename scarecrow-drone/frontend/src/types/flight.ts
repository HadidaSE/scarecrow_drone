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
  batteryLevel: number;
  currentFlight?: Flight;
}

export interface ConnectionStatus {
  wifiConnected: boolean;
  sshConnected: boolean;
  droneReady: boolean;
}
