import React from 'react';
import './Navbar.css';
import { useNavigate, useLocation } from 'react-router-dom';
import { useTheme } from '../../lib/ThemeContext';

export default function Navbar() {
  const navigate  = useNavigate();
  const location  = useLocation();
  const { theme, toggle } = useTheme();

  const handleLogout = () => {
    localStorage.removeItem('token');
    navigate('/');
  };

  const is = (path) => location.pathname === path;

  return (
    <nav className="sn-navbar">
      <div className="sn-navbar-inner">

        {/* Brand */}
        <a className="sn-brand" onClick={() => navigate('/dashboard')} role="button" tabIndex={0}>
          <img className="sn-brand-logo" src="/images/logo.png" alt="StockiNews" />
          <span className="sn-brand-name">Stocki<em>News</em></span>
        </a>

        <div className="sn-nav-sep" />

        {/* Nav links */}
        <div className="sn-nav-links">
          <button
            className={`sn-nav-link${is('/dashboard') ? ' sn-active' : ''}`}
            onClick={() => navigate('/dashboard')}
          >
            Dashboard
          </button>
          <button
            className={`sn-nav-link${is('/portfolio') ? ' sn-active' : ''}`}
            onClick={() => navigate('/portfolio')}
          >
            Portfolio
          </button>
          <button
            className={`sn-nav-link${is('/education') ? ' sn-active' : ''}`}
            onClick={() => navigate('/education')}
          >
            Learn
          </button>
        </div>

        {/* Right side */}
        <div className="sn-nav-right">
          <button
            className="sn-theme-toggle"
            onClick={toggle}
            title={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
            aria-label="Toggle theme"
          >
            {theme === 'dark' ? '☀' : '🌙'}
          </button>
          <div className="sn-nav-sep" />
          <button className="sn-signout" onClick={handleLogout}>
            Sign out
          </button>
        </div>

      </div>
    </nav>
  );
}
