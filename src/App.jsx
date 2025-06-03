import './App.css';
import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Stock from './Stock/stock';
import Login from './Login/Login';
import Dashboard from './dashboard/dashboard';
import Portfoliopage from './Portfolio/Portfoliopage';
import Logout from './home/navbar/logout';

function App() {
  return(
    <BrowserRouter>
            <Routes>
                <Route path="/" element={<Login />} />
                <Route path='/dashboard' element={<Dashboard/>}/>
                <Route path='/portfolio' element={<Portfoliopage/>} />
                <Route path="/company-page" element={<Stock />} />
                <Route path="/logout" element={<Logout />} />
            </Routes>
    </BrowserRouter>
  );
}

export default App;
