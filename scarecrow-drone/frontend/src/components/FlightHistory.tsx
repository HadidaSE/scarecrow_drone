import React, { useState, useEffect } from 'react';
import { Flight } from '../types/flight';
import DetectionImageGallery from './DetectionImageGallery';
import { droneApi } from '../services/api';

interface FlightHistoryProps {
  flights: Flight[];
  onSelectFlight: (flight: Flight) => void;
}

const FlightHistory: React.FC<FlightHistoryProps> = ({ flights, onSelectFlight }) => {
  const [selectedFlightId, setSelectedFlightId] = useState<string | null>(null);
  const [detectionImages, setDetectionImages] = useState<string[]>([]);
  const [loadingImages, setLoadingImages] = useState<boolean>(false);

  const formatDuration = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}m ${secs}s`;
  };

  const formatDate = (dateString: string): string => {
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
  };

  const getStatusColor = (status: Flight['status']): string => {
    switch (status) {
      case 'completed': return '#4CAF50';
      case 'in_progress': return '#2196F3';
      case 'failed': return '#f44336';
      default: return '#9e9e9e';
    }
  };

  const handleFlightClick = async (flight: Flight) => {
    onSelectFlight(flight);
    
    // Toggle selection
    if (selectedFlightId === flight.id) {
      setSelectedFlightId(null);
      setDetectionImages([]);
    } else {
      setSelectedFlightId(flight.id);
      setLoadingImages(true);
      
      try {
        const images = await droneApi.getDetectionImages(flight.id);
        setDetectionImages(images);
      } catch (error) {
        console.error('Failed to load detection images:', error);
        setDetectionImages([]);
      } finally {
        setLoadingImages(false);
      }
    }
  };

  return (
    <div className="flight-history">
      <h2>Flight History</h2>

      {flights.length === 0 ? (
        <div className="no-flights">
          <p>No flights recorded yet.</p>
        </div>
      ) : (
        <div className="flights-list">
          {flights.map((flight) => (
            <div key={flight.id} className="flight-card-wrapper">
              <div
                className={`flight-card ${selectedFlightId === flight.id ? 'selected' : ''}`}
                onClick={() => handleFlightClick(flight)}
              >
                <div className="flight-header">
                  <span className="flight-date">{formatDate(flight.date)}</span>
                  <span
                    className="flight-status"
                    style={{ backgroundColor: getStatusColor(flight.status), color: '#000' }}
                  >
                    {flight.status}
                  </span>
                </div>

                <div className="flight-details">
                  <div className="detail">
                    <span className="label">Duration:</span>
                    <span className="value">{formatDuration(flight.duration)}</span>
                  </div>
                  <div className="detail">
                    <span className="label">Pigeons Detected:</span>
                    <span className="value pigeon-count">{flight.pigeonsDetected}</span>
                  </div>
                </div>
              </div>

              {selectedFlightId === flight.id && (
                <div className="flight-images-section">
                  {loadingImages ? (
                    <div className="loading">Loading images...</div>
                  ) : (
                    <DetectionImageGallery images={detectionImages} />
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default FlightHistory;
