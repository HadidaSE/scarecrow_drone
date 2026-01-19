import React from 'react';
import { render, screen } from '@testing-library/react';
import App from './App';

test('renders Scarecrow Drone dashboard', () => {
  render(<App />);
  // The app should render with a heading containing "Drone Control"
  const headingElement = screen.getByRole('heading', { name: /Drone Control/i });
  expect(headingElement).toBeInTheDocument();
});

test('renders WiFi status indicator', () => {
  render(<App />);
  // Should show WiFi status (use getAllByText since there might be multiple)
  const wifiElements = screen.getAllByText(/WiFi:/i);
  expect(wifiElements.length).toBeGreaterThan(0);
});
