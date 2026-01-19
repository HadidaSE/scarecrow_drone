import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import DroneControl from './DroneControl';
import { DroneStatus, ConnectionStatus } from '../types/flight';

describe('DroneControl', () => {
  const mockDroneStatus: DroneStatus = {
    isConnected: false,
    isFlying: false,
  };

  const mockConnectionStatus: ConnectionStatus = {
    wifiConnected: false,
    sshConnected: false,
    droneReady: false,
  };

  const mockHandlers = {
    onConnect: jest.fn(),
    onDisconnect: jest.fn(),
    onStartFlight: jest.fn(),
    onStopFlight: jest.fn(),
    onAbortMission: jest.fn(),
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders drone control heading', () => {
    render(
      <DroneControl
        droneStatus={mockDroneStatus}
        connectionStatus={mockConnectionStatus}
        onConnect={mockHandlers.onConnect}
        onDisconnect={mockHandlers.onDisconnect}
        onStartFlight={mockHandlers.onStartFlight}
        onStopFlight={mockHandlers.onStopFlight}
        onAbortMission={mockHandlers.onAbortMission}
        isConnecting={false}
        flightStartTime={null}
      />
    );

    expect(screen.getByText('Drone Control')).toBeInTheDocument();
  });

  it('shows WiFi disconnected message when not connected', () => {
    render(
      <DroneControl
        droneStatus={mockDroneStatus}
        connectionStatus={mockConnectionStatus}
        onConnect={mockHandlers.onConnect}
        onDisconnect={mockHandlers.onDisconnect}
        onStartFlight={mockHandlers.onStartFlight}
        onStopFlight={mockHandlers.onStopFlight}
        onAbortMission={mockHandlers.onAbortMission}
        isConnecting={false}
        flightStartTime={null}
      />
    );

    expect(screen.getByText(/WiFi: Not Connected/i)).toBeInTheDocument();
    expect(screen.getByText(/connect to the drone's WiFi network/i)).toBeInTheDocument();
  });

  it('shows connect button when WiFi is connected but SSH is not', () => {
    const wifiConnectedStatus: ConnectionStatus = {
      wifiConnected: true,
      sshConnected: false,
      droneReady: false,
    };

    render(
      <DroneControl
        droneStatus={mockDroneStatus}
        connectionStatus={wifiConnectedStatus}
        onConnect={mockHandlers.onConnect}
        onDisconnect={mockHandlers.onDisconnect}
        onStartFlight={mockHandlers.onStartFlight}
        onStopFlight={mockHandlers.onStopFlight}
        onAbortMission={mockHandlers.onAbortMission}
        isConnecting={false}
        flightStartTime={null}
      />
    );

    expect(screen.getByText('WiFi: Connected to Drone')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Connect to Drone/i })).toBeInTheDocument();
  });

  it('calls onConnect when connect button is clicked', () => {
    const wifiConnectedStatus: ConnectionStatus = {
      wifiConnected: true,
      sshConnected: false,
      droneReady: false,
    };

    render(
      <DroneControl
        droneStatus={mockDroneStatus}
        connectionStatus={wifiConnectedStatus}
        onConnect={mockHandlers.onConnect}
        onDisconnect={mockHandlers.onDisconnect}
        onStartFlight={mockHandlers.onStartFlight}
        onStopFlight={mockHandlers.onStopFlight}
        onAbortMission={mockHandlers.onAbortMission}
        isConnecting={false}
        flightStartTime={null}
      />
    );

    fireEvent.click(screen.getByRole('button', { name: /Connect to Drone/i }));
    expect(mockHandlers.onConnect).toHaveBeenCalledTimes(1);
  });

  it('shows connecting state when isConnecting is true', () => {
    const wifiConnectedStatus: ConnectionStatus = {
      wifiConnected: true,
      sshConnected: false,
      droneReady: false,
    };

    render(
      <DroneControl
        droneStatus={mockDroneStatus}
        connectionStatus={wifiConnectedStatus}
        onConnect={mockHandlers.onConnect}
        onDisconnect={mockHandlers.onDisconnect}
        onStartFlight={mockHandlers.onStartFlight}
        onStopFlight={mockHandlers.onStopFlight}
        onAbortMission={mockHandlers.onAbortMission}
        isConnecting={true}
        flightStartTime={null}
      />
    );

    const connectButton = screen.getByRole('button', { name: /Connecting.../i });
    expect(connectButton).toBeDisabled();
  });

  it('shows full controls when both WiFi and SSH are connected', () => {
    const fullyConnectedStatus: ConnectionStatus = {
      wifiConnected: true,
      sshConnected: true,
      droneReady: true,
    };

    render(
      <DroneControl
        droneStatus={mockDroneStatus}
        connectionStatus={fullyConnectedStatus}
        onConnect={mockHandlers.onConnect}
        onDisconnect={mockHandlers.onDisconnect}
        onStartFlight={mockHandlers.onStartFlight}
        onStopFlight={mockHandlers.onStopFlight}
        onAbortMission={mockHandlers.onAbortMission}
        isConnecting={false}
        flightStartTime={null}
      />
    );

    expect(screen.getByText('Drone Ready')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Start Flight/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Disconnect/i })).toBeInTheDocument();
  });

  it('disables Start Flight button when drone is not ready', () => {
    const sshConnectedNotReady: ConnectionStatus = {
      wifiConnected: true,
      sshConnected: true,
      droneReady: false,
    };

    render(
      <DroneControl
        droneStatus={mockDroneStatus}
        connectionStatus={sshConnectedNotReady}
        onConnect={mockHandlers.onConnect}
        onDisconnect={mockHandlers.onDisconnect}
        onStartFlight={mockHandlers.onStartFlight}
        onStopFlight={mockHandlers.onStopFlight}
        onAbortMission={mockHandlers.onAbortMission}
        isConnecting={false}
        flightStartTime={null}
      />
    );

    expect(screen.getByRole('button', { name: /Start Flight/i })).toBeDisabled();
  });

  it('calls onStartFlight when start button is clicked', () => {
    const fullyConnectedStatus: ConnectionStatus = {
      wifiConnected: true,
      sshConnected: true,
      droneReady: true,
    };

    render(
      <DroneControl
        droneStatus={mockDroneStatus}
        connectionStatus={fullyConnectedStatus}
        onConnect={mockHandlers.onConnect}
        onDisconnect={mockHandlers.onDisconnect}
        onStartFlight={mockHandlers.onStartFlight}
        onStopFlight={mockHandlers.onStopFlight}
        onAbortMission={mockHandlers.onAbortMission}
        isConnecting={false}
        flightStartTime={null}
      />
    );

    fireEvent.click(screen.getByRole('button', { name: /Start Flight/i }));
    expect(mockHandlers.onStartFlight).toHaveBeenCalledTimes(1);
  });

  it('shows stop and abort buttons when drone is flying', () => {
    const fullyConnectedStatus: ConnectionStatus = {
      wifiConnected: true,
      sshConnected: true,
      droneReady: true,
    };

    const flyingStatus: DroneStatus = {
      isConnected: true,
      isFlying: true,
    };

    render(
      <DroneControl
        droneStatus={flyingStatus}
        connectionStatus={fullyConnectedStatus}
        onConnect={mockHandlers.onConnect}
        onDisconnect={mockHandlers.onDisconnect}
        onStartFlight={mockHandlers.onStartFlight}
        onStopFlight={mockHandlers.onStopFlight}
        onAbortMission={mockHandlers.onAbortMission}
        isConnecting={false}
        flightStartTime={new Date()}
      />
    );

    expect(screen.getByRole('button', { name: /Stop Flight/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /ABORT/i })).toBeInTheDocument();
    expect(screen.getByText(/Flight in progress/i)).toBeInTheDocument();
  });

  it('calls onStopFlight when stop button is clicked', () => {
    const fullyConnectedStatus: ConnectionStatus = {
      wifiConnected: true,
      sshConnected: true,
      droneReady: true,
    };

    const flyingStatus: DroneStatus = {
      isConnected: true,
      isFlying: true,
    };

    render(
      <DroneControl
        droneStatus={flyingStatus}
        connectionStatus={fullyConnectedStatus}
        onConnect={mockHandlers.onConnect}
        onDisconnect={mockHandlers.onDisconnect}
        onStartFlight={mockHandlers.onStartFlight}
        onStopFlight={mockHandlers.onStopFlight}
        onAbortMission={mockHandlers.onAbortMission}
        isConnecting={false}
        flightStartTime={new Date()}
      />
    );

    fireEvent.click(screen.getByRole('button', { name: /Stop Flight/i }));
    expect(mockHandlers.onStopFlight).toHaveBeenCalledTimes(1);
  });

  it('calls onAbortMission when abort button is clicked', () => {
    const fullyConnectedStatus: ConnectionStatus = {
      wifiConnected: true,
      sshConnected: true,
      droneReady: true,
    };

    const flyingStatus: DroneStatus = {
      isConnected: true,
      isFlying: true,
    };

    render(
      <DroneControl
        droneStatus={flyingStatus}
        connectionStatus={fullyConnectedStatus}
        onConnect={mockHandlers.onConnect}
        onDisconnect={mockHandlers.onDisconnect}
        onStartFlight={mockHandlers.onStartFlight}
        onStopFlight={mockHandlers.onStopFlight}
        onAbortMission={mockHandlers.onAbortMission}
        isConnecting={false}
        flightStartTime={new Date()}
      />
    );

    fireEvent.click(screen.getByRole('button', { name: /ABORT/i }));
    expect(mockHandlers.onAbortMission).toHaveBeenCalledTimes(1);
  });

  it('disables disconnect button when drone is flying', () => {
    const fullyConnectedStatus: ConnectionStatus = {
      wifiConnected: true,
      sshConnected: true,
      droneReady: true,
    };

    const flyingStatus: DroneStatus = {
      isConnected: true,
      isFlying: true,
    };

    render(
      <DroneControl
        droneStatus={flyingStatus}
        connectionStatus={fullyConnectedStatus}
        onConnect={mockHandlers.onConnect}
        onDisconnect={mockHandlers.onDisconnect}
        onStartFlight={mockHandlers.onStartFlight}
        onStopFlight={mockHandlers.onStopFlight}
        onAbortMission={mockHandlers.onAbortMission}
        isConnecting={false}
        flightStartTime={new Date()}
      />
    );

    expect(screen.getByRole('button', { name: /Disconnect/i })).toBeDisabled();
  });

  it('disables start flight button when already flying', () => {
    const fullyConnectedStatus: ConnectionStatus = {
      wifiConnected: true,
      sshConnected: true,
      droneReady: true,
    };

    const flyingStatus: DroneStatus = {
      isConnected: true,
      isFlying: true,
    };

    render(
      <DroneControl
        droneStatus={flyingStatus}
        connectionStatus={fullyConnectedStatus}
        onConnect={mockHandlers.onConnect}
        onDisconnect={mockHandlers.onDisconnect}
        onStartFlight={mockHandlers.onStartFlight}
        onStopFlight={mockHandlers.onStopFlight}
        onAbortMission={mockHandlers.onAbortMission}
        isConnecting={false}
        flightStartTime={new Date()}
      />
    );

    expect(screen.getByRole('button', { name: /Start Flight/i })).toBeDisabled();
  });

  it('shows flight duration timer when flying', () => {
    const fullyConnectedStatus: ConnectionStatus = {
      wifiConnected: true,
      sshConnected: true,
      droneReady: true,
    };

    const flyingStatus: DroneStatus = {
      isConnected: true,
      isFlying: true,
    };

    render(
      <DroneControl
        droneStatus={flyingStatus}
        connectionStatus={fullyConnectedStatus}
        onConnect={mockHandlers.onConnect}
        onDisconnect={mockHandlers.onDisconnect}
        onStartFlight={mockHandlers.onStartFlight}
        onStopFlight={mockHandlers.onStopFlight}
        onAbortMission={mockHandlers.onAbortMission}
        isConnecting={false}
        flightStartTime={new Date()}
      />
    );

    expect(screen.getByText('Flight Duration:')).toBeInTheDocument();
  });

  it('calls onDisconnect when disconnect button is clicked', () => {
    const fullyConnectedStatus: ConnectionStatus = {
      wifiConnected: true,
      sshConnected: true,
      droneReady: true,
    };

    render(
      <DroneControl
        droneStatus={mockDroneStatus}
        connectionStatus={fullyConnectedStatus}
        onConnect={mockHandlers.onConnect}
        onDisconnect={mockHandlers.onDisconnect}
        onStartFlight={mockHandlers.onStartFlight}
        onStopFlight={mockHandlers.onStopFlight}
        onAbortMission={mockHandlers.onAbortMission}
        isConnecting={false}
        flightStartTime={null}
      />
    );

    fireEvent.click(screen.getByRole('button', { name: /Disconnect/i }));
    expect(mockHandlers.onDisconnect).toHaveBeenCalledTimes(1);
  });
});
