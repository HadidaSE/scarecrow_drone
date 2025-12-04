import { Flight, DroneStatus } from '../types/flight';

const API_BASE_URL = 'http://localhost:5000/api';

export const droneApi = {
  // Get drone status
  getStatus: async (): Promise<DroneStatus> => {
    const response = await fetch(`${API_BASE_URL}/drone/status`);
    if (!response.ok) throw new Error('Failed to get drone status');
    return response.json();
  },

  // Start flight
  startFlight: async (): Promise<{ success: boolean; flightId: string }> => {
    const response = await fetch(`${API_BASE_URL}/drone/start`, {
      method: 'POST',
    });
    if (!response.ok) throw new Error('Failed to start flight');
    return response.json();
  },

  // Stop flight
  stopFlight: async (): Promise<{ success: boolean }> => {
    const response = await fetch(`${API_BASE_URL}/drone/stop`, {
      method: 'POST',
    });
    if (!response.ok) throw new Error('Failed to stop flight');
    return response.json();
  },

  // Get flight history
  getFlightHistory: async (): Promise<Flight[]> => {
    const response = await fetch(`${API_BASE_URL}/flights`);
    if (!response.ok) throw new Error('Failed to get flight history');
    return response.json();
  },

  // Get single flight details
  getFlight: async (flightId: string): Promise<Flight> => {
    const response = await fetch(`${API_BASE_URL}/flights/${flightId}`);
    if (!response.ok) throw new Error('Failed to get flight details');
    return response.json();
  },
};
