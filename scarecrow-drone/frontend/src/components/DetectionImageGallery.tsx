import React from 'react';
import './DetectionImageGallery.css';

interface DetectionImageGalleryProps {
  images: string[];
}

const DetectionImageGallery: React.FC<DetectionImageGalleryProps> = ({ images }) => {
  const API_BASE_URL = 'http://localhost:5000';

  const getImageUrl = (imagePath: string): string => {
    // Extract filename from full path
    const filename = imagePath.split(/[/\\]/).pop() || '';
    return `${API_BASE_URL}/detection_images/${filename}`;
  };

  const openImageInNewTab = (imageUrl: string) => {
    window.open(imageUrl, '_blank');
  };

  if (!images || images.length === 0) {
    return (
      <div className="image-gallery-empty">
        <p>No detection images available for this flight.</p>
      </div>
    );
  }

  return (
    <div className="detection-image-gallery">
      <h3>Detection Images ({images.length})</h3>
      <div className="image-grid">
        {images.map((imagePath, index) => {
          const imageUrl = getImageUrl(imagePath);
          return (
            <div
              key={index}
              className="image-thumbnail"
              onClick={() => openImageInNewTab(imageUrl)}
              title="Click to open in new tab"
            >
              <img
                src={imageUrl}
                alt={`Detection ${index + 1}`}
                onError={(e) => {
                  (e.target as HTMLImageElement).src = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="200" height="200"%3E%3Crect width="200" height="200" fill="%23ddd"/%3E%3Ctext x="50%25" y="50%25" text-anchor="middle" dy=".3em" fill="%23999"%3EImage not found%3C/text%3E%3C/svg%3E';
                }}
              />
              <div className="image-label">Detection {index + 1}</div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default DetectionImageGallery;
