import { Flight, DroneStatus, ConnectionStatus } from '../types/flight';

const API_BASE_URL = 'http://localhost:5000/api';

export const droneApi = {
  // Check WiFi connection to drone
  checkWifiConnection: async (): Promise<{ connected: boolean }> => {
    const response = await fetch(`${API_BASE_URL}/connection/wifi`);
    if (!response.ok) throw new Error('Failed to check WiFi connection');
    return response.json();
  },

  // Connect to drone via SSH
  connectSSH: async (): Promise<{ success: boolean; error?: string }> => {
    const response = await fetch(`${API_BASE_URL}/connection/ssh`, {
      method: 'POST',
    });
    if (!response.ok) throw new Error('Failed to connect via SSH');
    return response.json();
  },

  // Disconnect SSH
  disconnectSSH: async (): Promise<{ success: boolean }> => {
    const response = await fetch(`${API_BASE_URL}/connection/ssh`, {
      method: 'DELETE',
    });
    if (!response.ok) throw new Error('Failed to disconnect SSH');
    return response.json();
  },

  // Get full connection status
  getConnectionStatus: async (): Promise<ConnectionStatus> => {
    const response = await fetch(`${API_BASE_URL}/connection/status`);
    if (!response.ok) throw new Error('Failed to get connection status');
    return response.json();
  },

  // Get drone status
  getStatus: async (): Promise<DroneStatus> => {
    const response = await fetch(`${API_BASE_URL}/drone/status`);
    if (!response.ok) 
      throw new Error('Failed to get drone status');
    return response.json();
  },

  // Start flight
  startFlight: async (): Promise<{ success: boolean; flightId: string }> => {
    const response = await fetch(`${API_BASE_URL}/drone/start`, {
      method: 'POST',
    });
    if (!response.ok) 
      throw new Error('Failed to start flight');
    return response.json();
  },

  // Stop flight (return home)
  stopFlight: async (): Promise<{ success: boolean }> => {
    const response = await fetch(`${API_BASE_URL}/drone/stop`, {
      method: 'POST',
    });
    if (!response.ok) 
      throw new Error('Failed to stop flight');
    return response.json();
  },

  // Return to starting position
  returnHome: async (): Promise<{ success: boolean; error?: string }> => {
    const response = await fetch(`${API_BASE_URL}/drone/return-home`, {
      method: 'POST',
    });
    if (!response.ok) throw new Error('Failed to return home');
    return response.json();
  },

  // Emergency abort - terminate all tasks immediately
  abortMission: async (): Promise<{ success: boolean; error?: string }> => {
    const response = await fetch(`${API_BASE_URL}/drone/abort`, {
      method: 'POST',
    });
    if (!response.ok) throw new Error('Failed to abort mission');
    return response.json();
  },

  // Get flight history
  getFlightHistory: async (): Promise<Flight[]> => {
    const response = await fetch(`${API_BASE_URL}/flights`);
    if (!response.ok) 
      throw new Error('Failed to get flight history');
    return response.json();
  },

  // Get single flight details
  getFlight: async (flightId: string): Promise<Flight> => {
    const response = await fetch(`${API_BASE_URL}/flights/${flightId}`);
    if (!response.ok) 
      throw new Error('Failed to get flight details');
    return response.json();
  },
};
