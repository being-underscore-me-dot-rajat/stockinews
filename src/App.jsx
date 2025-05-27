import './App.css';
import React from 'react';
import Home from './home/Home';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Stock from './Stock/stock';
import Login from './Login/Login';
import Dashboard from './dashboard/dashboard';

function App() {
  return(
    <BrowserRouter>
            <Routes>
                <Route path="/" element={<Login />} />
                <Route path='/dashboard' element={<Dashboard/>}/>
                {/* <Route path="/" element={<Home />} />
                <Route path="/company-page" element={<Stock />} /> */}
            </Routes>
    </BrowserRouter>
  );
}

export default App;
