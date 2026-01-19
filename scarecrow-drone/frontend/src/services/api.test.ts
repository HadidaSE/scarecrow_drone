import { droneApi } from './api';

// Mock the global fetch function
const mockFetch = jest.fn();
global.fetch = mockFetch;

describe('droneApi', () => {
  beforeEach(() => {
    mockFetch.mockClear();
  });

  describe('checkWifiConnection', () => {
    it('returns connected status when successful', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ connected: true }),
      });

      const result = await droneApi.checkWifiConnection();

      expect(result.connected).toBe(true);
      expect(mockFetch).toHaveBeenCalledWith('http://localhost:5000/api/connection/wifi');
    });

    it('throws error when request fails', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
      });

      await expect(droneApi.checkWifiConnection()).rejects.toThrow('Failed to check WiFi connection');
    });
  });

  describe('connectSSH', () => {
    it('returns success when SSH connection succeeds', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ success: true }),
      });

      const result = await droneApi.connectSSH();

      expect(result.success).toBe(true);
      expect(mockFetch).toHaveBeenCalledWith('http://localhost:5000/api/connection/ssh', {
        method: 'POST',
      });
    });

    it('returns error when SSH connection fails', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ success: false, error: 'Connection refused' }),
      });

      const result = await droneApi.connectSSH();

      expect(result.success).toBe(false);
      expect(result.error).toBe('Connection refused');
    });

    it('throws error when request fails', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
      });

      await expect(droneApi.connectSSH()).rejects.toThrow('Failed to connect via SSH');
    });
  });

  describe('disconnectSSH', () => {
    it('returns success when disconnection succeeds', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ success: true }),
      });

      const result = await droneApi.disconnectSSH();

      expect(result.success).toBe(true);
      expect(mockFetch).toHaveBeenCalledWith('http://localhost:5000/api/connection/ssh', {
        method: 'DELETE',
      });
    });
  });

  describe('getConnectionStatus', () => {
    it('returns full connection status', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          wifiConnected: true,
          sshConnected: true,
          droneReady: true,
        }),
      });

      const result = await droneApi.getConnectionStatus();

      expect(result.wifiConnected).toBe(true);
      expect(result.sshConnected).toBe(true);
      expect(result.droneReady).toBe(true);
    });
  });

  describe('getStatus', () => {
    it('returns drone status', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          isConnected: true,
          isFlying: false,
        }),
      });

      const result = await droneApi.getStatus();

      expect(result.isConnected).toBe(true);
      expect(result.isFlying).toBe(false);
    });
  });

  describe('startFlight', () => {
    it('returns success with flightId when flight starts', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ success: true, flightId: '123' }),
      });

      const result = await droneApi.startFlight();

      expect(result.success).toBe(true);
      expect(result.flightId).toBe('123');
      expect(mockFetch).toHaveBeenCalledWith('http://localhost:5000/api/drone/start', {
        method: 'POST',
      });
    });
  });

  describe('stopFlight', () => {
    it('returns pigeon count when flight stops', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
          pigeonsDetected: 5,
          framesProcessed: 100,
          message: 'Flight completed',
        }),
      });

      const result = await droneApi.stopFlight();

      expect(result.success).toBe(true);
      expect(result.pigeonsDetected).toBe(5);
      expect(result.framesProcessed).toBe(100);
    });
  });

  describe('returnHome', () => {
    it('returns success when drone returns home', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ success: true }),
      });

      const result = await droneApi.returnHome();

      expect(result.success).toBe(true);
      expect(mockFetch).toHaveBeenCalledWith('http://localhost:5000/api/drone/return-home', {
        method: 'POST',
      });
    });
  });

  describe('abortMission', () => {
    it('returns success and detection count when mission aborted', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
          pigeonsDetected: 3,
          framesProcessed: 50,
          message: 'Flight aborted',
        }),
      });

      const result = await droneApi.abortMission();

      expect(result.success).toBe(true);
      expect(result.pigeonsDetected).toBe(3);
    });
  });

  describe('getFlightHistory', () => {
    it('returns array of flights', async () => {
      const mockFlights = [
        { id: '1', date: '2025-01-19', duration: 300, pigeonsDetected: 5 },
        { id: '2', date: '2025-01-18', duration: 250, pigeonsDetected: 3 },
      ];

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockFlights,
      });

      const result = await droneApi.getFlightHistory();

      expect(result).toHaveLength(2);
      expect(result[0].id).toBe('1');
    });
  });

  describe('getFlight', () => {
    it('returns single flight details', async () => {
      const mockFlight = {
        id: '1',
        date: '2025-01-19',
        duration: 300,
        pigeonsDetected: 5,
        status: 'completed',
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockFlight,
      });

      const result = await droneApi.getFlight('1');

      expect(result.id).toBe('1');
      expect(result.pigeonsDetected).toBe(5);
    });
  });

  describe('getFlightSummary', () => {
    it('returns flight summary with stats', async () => {
      const mockSummary = {
        flightId: '1',
        droneId: 1,
        duration: 300,
        avgSpeed: 5.5,
        avgAltitude: 10.2,
        status: 'completed',
        date: '2025-01-19',
        startTime: '10:00:00',
        endTime: '10:05:00',
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockSummary,
      });

      const result = await droneApi.getFlightSummary('1');

      expect(result.flightId).toBe('1');
      expect(result.avgAltitude).toBe(10.2);
    });
  });

  describe('getDetectionImages', () => {
    it('returns array of image paths', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          images: ['image1.jpg', 'image2.jpg'],
        }),
      });

      const result = await droneApi.getDetectionImages('1');

      expect(result).toHaveLength(2);
      expect(result[0]).toBe('image1.jpg');
    });

    it('returns empty array when no images', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({}),
      });

      const result = await droneApi.getDetectionImages('1');

      expect(result).toEqual([]);
    });
  });

  describe('getFlightRecording', () => {
    it('returns recording path when available', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          recording: 'recordings/flight_1.mp4',
        }),
      });

      const result = await droneApi.getFlightRecording('1');

      expect(result).toBe('recordings/flight_1.mp4');
    });

    it('returns null when no recording', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({}),
      });

      const result = await droneApi.getFlightRecording('1');

      expect(result).toBeNull();
    });
  });
});
