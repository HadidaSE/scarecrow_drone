import React from 'react';
import { DroneStatus, ConnectionStatus } from '../types/flight';

interface DroneControlProps {
  droneStatus: DroneStatus;
  connectionStatus: ConnectionStatus;
  onConnect: () => void;
  onDisconnect: () => void;
  onStartFlight: () => void;
  onStopFlight: () => void;
  onAbortMission: () => void;
  isConnecting: boolean;
}

const DroneControl: React.FC<DroneControlProps> = ({
  droneStatus,
  connectionStatus,
  onConnect,
  onDisconnect,
  onStartFlight,
  onStopFlight,
  onAbortMission,
  isConnecting,
}) => {
  const { isFlying } = droneStatus;
  const { wifiConnected, sshConnected, droneReady } = connectionStatus;

  return (
    <div className="drone-control">
      <h2>Drone Control</h2>

      {/* WiFi Status */}
      <div className="status-panel">
        <div className={`status-indicator ${wifiConnected ? 'connected' : 'disconnected'}`}>
          <span className="status-dot"></span>
          WiFi: {wifiConnected ? 'Connected to Drone' : 'Not Connected'}
        </div>
      </div>

      {/* Show Connect button only when WiFi is connected but SSH is not */}
      {wifiConnected && !sshConnected && (
        <div className="connection-panel">
          <p>Drone WiFi detected. Click to establish connection.</p>
          <button
            className="btn btn-connect"
            onClick={onConnect}
            disabled={isConnecting}
          >
            {isConnecting ? 'Connecting...' : 'Connect to Drone'}
          </button>
        </div>
      )}

      {/* Show full controls only when both WiFi and SSH are connected */}
      {wifiConnected && sshConnected && (
        <>
          <div className="status-panel">
            <div className={`status-indicator ${droneReady ? 'connected' : 'disconnected'}`}>
              <span className="status-dot"></span>
              {droneReady ? 'Drone Ready' : 'Drone Not Ready'}
            </div>
          </div>

          <div className="control-buttons">
            {!isFlying ? (
              <button
                className="btn btn-start"
                onClick={onStartFlight}
                disabled={!droneReady}
              >
                Start Flight
              </button>
            ) : (
              <>
                <button
                  className="btn btn-stop"
                  onClick={onStopFlight}
                >
                  Return Home
                </button>
                <button
                  className="btn btn-abort"
                  onClick={onAbortMission}
                >
                  ABORT
                </button>
              </>
            )}

            <button
              className="btn btn-disconnect"
              onClick={onDisconnect}
              disabled={isFlying}
            >
              Disconnect
            </button>
          </div>

          {isFlying && (
            <div className="flight-status">
              <span className="pulse"></span>
              Flight in progress...
            </div>
          )}
        </>
      )}

      {/* Show message when not connected to WiFi */}
      {!wifiConnected && (
        <div className="connection-panel">
          <p className="warning">
            Please connect to the drone's WiFi network to continue.
          </p>
        </div>
      )}
    </div>
  );
};

export default DroneControl;
