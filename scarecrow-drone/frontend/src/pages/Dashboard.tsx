import React, { useState, useEffect } from 'react';
import DroneControl from '../components/DroneControl';
import FlightHistory from '../components/FlightHistory';
import { Flight, DroneStatus, ConnectionStatus } from '../types/flight';
import { droneApi } from '../services/api';

const Dashboard: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'control' | 'history'>('control');
  const [droneStatus, setDroneStatus] = useState<DroneStatus>({
    isConnected: false,
    isFlying: false,
    batteryLevel: 0,
  });
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>({
    wifiConnected: false,
    sshConnected: false,
    droneReady: false,
  });
  const [flights, setFlights] = useState<Flight[]>([]);
  const [selectedFlight, setSelectedFlight] = useState<Flight | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isConnecting, setIsConnecting] = useState(false);

  // Check connection status periodically
  useEffect(() => {
    const checkConnection = async () => {
      try {
        const status = await droneApi.getConnectionStatus();
        setConnectionStatus(status);
        setError(null);
      } catch (err) {
        // Backend not available - check WiFi only
        try {
          const wifi = await droneApi.checkWifiConnection();
          setConnectionStatus({
            wifiConnected: wifi.connected,
            sshConnected: false,
            droneReady: false,
          });
        } catch {
          setConnectionStatus({
            wifiConnected: false,
            sshConnected: false,
            droneReady: false,
          });
        }
      }
    };

    checkConnection();
    const interval = setInterval(checkConnection, 3000);
    return () => clearInterval(interval);
  }, []);

  // Fetch drone status when SSH is connected
  useEffect(() => {
    if (!connectionStatus.sshConnected) return;

    const fetchStatus = async () => {
      try {
        const status = await droneApi.getStatus();
        setDroneStatus(status);
        setError(null);
      } catch (err) {
        // Keep last known status
      }
    };

    fetchStatus();
    const interval = setInterval(fetchStatus, 2000);
    return () => clearInterval(interval);
  }, [connectionStatus.sshConnected]);

  // Fetch flight history
  useEffect(() => {
    const fetchFlights = async () => {
      try {
        const history = await droneApi.getFlightHistory();
        setFlights(history);
      } catch (err) {
        setFlights([]);
      }
    };

    if (activeTab === 'history') {
      fetchFlights();
    }
  }, [activeTab]);

  const handleConnect = async () => {
    setIsConnecting(true);
    setError(null);
    try {
      const result = await droneApi.connectSSH();
      if (result.success) {
        setConnectionStatus(prev => ({ ...prev, sshConnected: true }));
      } else {
        setError(result.error || 'Failed to connect to drone');
      }
    } catch (err) {
      setError('Failed to connect to drone');
    } finally {
      setIsConnecting(false);
    }
  };

  const handleDisconnect = async () => {
    try {
      await droneApi.disconnectSSH();
      setConnectionStatus(prev => ({ ...prev, sshConnected: false, droneReady: false }));
      setDroneStatus({ isConnected: false, isFlying: false, batteryLevel: 0 });
    } catch (err) {
      setError('Failed to disconnect');
    }
  };

  const handleStartFlight = async () => {
    try {
      const result = await droneApi.startFlight();
      if (result.success) {
        setDroneStatus((prev) => ({ ...prev, isFlying: true }));
      } else {
        setError('Failed to start flight');
      }
    } catch (err) {
      setError('Failed to start flight');
    }
  };

  const handleStopFlight = async () => {
    try {
      const result = await droneApi.stopFlight();
      if (result.success) {
        setDroneStatus((prev) => ({ ...prev, isFlying: false }));
      } else {
        setError('Failed to stop flight');
      }
    } catch (err) {
      setError('Failed to stop flight');
    }
  };

  const handleAbortMission = async () => {
    try {
      const result = await droneApi.abortMission();
      if (result.success) {
        setDroneStatus((prev) => ({ ...prev, isFlying: false }));
      } else {
        setError(result.error || 'Failed to abort mission');
      }
    } catch (err) {
      setError('Failed to abort mission');
    }
  };

  const handleSelectFlight = (flight: Flight) => {
    setSelectedFlight(flight);
  };

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <h1>Scarecrow Drone</h1>
        <p>Intel Aero Drone Control</p>
      </header>

      <nav className="dashboard-nav">
        <button
          className={`nav-btn ${activeTab === 'control' ? 'active' : ''}`}
          onClick={() => setActiveTab('control')}
        >
          Drone Control
        </button>
        <button
          className={`nav-btn ${activeTab === 'history' ? 'active' : ''}`}
          onClick={() => setActiveTab('history')}
        >
          Flight History
        </button>
      </nav>

      {error && <div className="error-message">{error}</div>}

      <main className="dashboard-content">
        {activeTab === 'control' ? (
          <DroneControl
            droneStatus={droneStatus}
            connectionStatus={connectionStatus}
            onConnect={handleConnect}
            onDisconnect={handleDisconnect}
            onStartFlight={handleStartFlight}
            onStopFlight={handleStopFlight}
            onAbortMission={handleAbortMission}
            isConnecting={isConnecting}
          />
        ) : (
          <FlightHistory
            flights={flights}
            onSelectFlight={handleSelectFlight}
          />
        )}
      </main>

      {selectedFlight && (
        <div className="modal-overlay" onClick={() => setSelectedFlight(null)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h3>Flight Details</h3>
            <p><strong>Date:</strong> {new Date(selectedFlight.date).toLocaleString()}</p>
            <p><strong>Duration:</strong> {Math.floor(selectedFlight.duration / 60)}m {selectedFlight.duration % 60}s</p>
            <p><strong>Pigeons Detected:</strong> {selectedFlight.pigeonsDetected}</p>
            <p><strong>Status:</strong> {selectedFlight.status}</p>
            <button className="btn" onClick={() => setSelectedFlight(null)}>Close</button>
          </div>
        </div>
      )}
    </div>
  );
};

export default Dashboard;
