import './App.css';
import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { ThemeProvider } from './lib/ThemeContext';
import Stock from './Stock/stock';
import Login from './Login/Login';
import Dashboard from './dashboard/dashboard';
import Portfoliopage from './Portfolio/Portfoliopage';
import Education from './education/Education';
import Logout from './home/navbar/logout';

function App() {
  return (
    <ThemeProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/"             element={<Login />} />
          <Route path="/dashboard"    element={<Dashboard />} />
          <Route path="/portfolio"    element={<Portfoliopage />} />
          <Route path="/education"    element={<Education />} />
          <Route path="/company-page" element={<Stock />} />
          <Route path="/logout"       element={<Logout />} />
        </Routes>
      </BrowserRouter>
    </ThemeProvider>
  );
}

export default App;
