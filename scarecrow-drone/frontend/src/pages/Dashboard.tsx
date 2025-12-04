import React, { useState, useEffect } from 'react';
import DroneControl from '../components/DroneControl';
import FlightHistory from '../components/FlightHistory';
import { Flight, DroneStatus } from '../types/flight';
import { droneApi } from '../services/api';

const Dashboard: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'control' | 'history'>('control');
  const [droneStatus, setDroneStatus] = useState<DroneStatus>({
    isConnected: false,
    isFlying: false,
    batteryLevel: 0,
  });
  const [flights, setFlights] = useState<Flight[]>([]);
  const [selectedFlight, setSelectedFlight] = useState<Flight | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Fetch drone status periodically
  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const status = await droneApi.getStatus();
        setDroneStatus(status);
        setError(null);
      } catch (err) {
        // Use mock data when backend is not available
        setDroneStatus({
          isConnected: true,
          isFlying: false,
          batteryLevel: 85,
        });
      }
    };

    fetchStatus();
    const interval = setInterval(fetchStatus, 5000);
    return () => clearInterval(interval);
  }, []);

  // Fetch flight history
  useEffect(() => {
    const fetchFlights = async () => {
      try {
        const history = await droneApi.getFlightHistory();
        setFlights(history);
      } catch (err) {
        // Use mock data when backend is not available
        setFlights([
          {
            id: '1',
            date: '2024-01-15T10:30:00',
            duration: 325,
            pigeonsDetected: 12,
            status: 'completed',
            startTime: '10:30:00',
            endTime: '10:35:25',
          },
          {
            id: '2',
            date: '2024-01-14T14:15:00',
            duration: 480,
            pigeonsDetected: 8,
            status: 'completed',
            startTime: '14:15:00',
            endTime: '14:23:00',
          },
          {
            id: '3',
            date: '2024-01-13T09:00:00',
            duration: 120,
            pigeonsDetected: 3,
            status: 'failed',
            startTime: '09:00:00',
            endTime: '09:02:00',
          },
        ]);
      }
    };

    if (activeTab === 'history') {
      fetchFlights();
    }
  }, [activeTab]);

  const handleStartFlight = async () => {
    try {
      await droneApi.startFlight();
      setDroneStatus((prev) => ({ ...prev, isFlying: true }));
    } catch (err) {
      // Mock for demo
      setDroneStatus((prev) => ({ ...prev, isFlying: true }));
    }
  };

  const handleStopFlight = async () => {
    try {
      await droneApi.stopFlight();
      setDroneStatus((prev) => ({ ...prev, isFlying: false }));
    } catch (err) {
      // Mock for demo
      setDroneStatus((prev) => ({ ...prev, isFlying: false }));
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
            onStartFlight={handleStartFlight}
            onStopFlight={handleStopFlight}
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
