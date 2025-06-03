import React from 'react';
import './footer.css';

export default function Footer() {
  return (
    <footer className="app-footer">
      <div className="footer-container">
        <div className="footer-logo">
          <img src="/images/logo.png" alt="Logo" />
          <span>Stock in News</span>
        </div>

        <div className="footer-links">
          <a href="/dashboard">Dashboard</a>
          <a href="/portfolio">Portfolio</a>
          <a href="/news">News</a>
          <a href="/about">About</a>
        </div>

        <div className="footer-copy">
          © {new Date().getFullYear()} Stock in News. All rights reserved.
        </div>
      </div>
    </footer>
  );
}
