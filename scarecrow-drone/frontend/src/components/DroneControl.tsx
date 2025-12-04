import React from 'react';
import { DroneStatus } from '../types/flight';

interface DroneControlProps {
  droneStatus: DroneStatus;
  onStartFlight: () => void;
  onStopFlight: () => void;
}

const DroneControl: React.FC<DroneControlProps> = ({
  droneStatus,
  onStartFlight,
  onStopFlight,
}) => {
  const { isConnected, isFlying, batteryLevel } = droneStatus;

  return (
    <div className="drone-control">
      <h2>Drone Control</h2>

      <div className="status-panel">
        <div className={`status-indicator ${isConnected ? 'connected' : 'disconnected'}`}>
          <span className="status-dot"></span>
          {isConnected ? 'Connected' : 'Disconnected'}
        </div>

        <div className="battery-level">
          <span>Battery: </span>
          <div className="battery-bar">
            <div
              className="battery-fill"
              style={{
                width: `${batteryLevel}%`,
                backgroundColor: batteryLevel > 20 ? '#4CAF50' : '#f44336'
              }}
            ></div>
          </div>
          <span>{batteryLevel}%</span>
        </div>
      </div>

      <div className="control-buttons">
        {!isFlying ? (
          <button
            className="btn btn-start"
            onClick={onStartFlight}
            disabled={!isConnected || batteryLevel < 10}
          >
            Start Flight
          </button>
        ) : (
          <button
            className="btn btn-stop"
            onClick={onStopFlight}
          >
            Stop Flight
          </button>
        )}
      </div>

      {isFlying && (
        <div className="flight-status">
          <span className="pulse"></span>
          Flight in progress...
        </div>
      )}
    </div>
  );
};

export default DroneControl;
