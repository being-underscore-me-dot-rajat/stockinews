import { StrictMode } from 'react';
import ReactDOM from 'react-dom/client';
import React from 'react';
import './index.css';
import App from './App';
import { applyChartDefaults } from './lib/chartTheme';

// Apply Chart.js dark theme globally before any chart renders
applyChartDefaults();

ReactDOM.createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>
);
