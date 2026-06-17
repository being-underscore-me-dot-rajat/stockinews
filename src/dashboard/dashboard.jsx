import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { API_BASE } from '../lib/api';
import Portfolio   from './components/portfolio/portfolio';
import Marketwatch from './components/marketwatch/Marketwatch';
import Watchlist   from './components/watchlist/watchlist';
import News        from './components/news/news';
import Briefing    from './components/briefing/Briefing';
import Navbar      from '../home/navbar/Navbar';
import Footer      from '../home/navbar/footer/Footer';
import './dashboard.css';

export default function Dashboard() {
  const navigate = useNavigate();
  const [user,    setUser]    = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) { navigate('/'); return; }
    fetch(`${API_BASE}/me`, { headers: { Authorization: `Bearer ${token}` } })
      .then(r => r.json())
      .then(d => {
        if (d.user) { setUser(d.user); setLoading(false); }
        else { localStorage.removeItem('token'); navigate('/', { replace: true }); }
      })
      .catch(() => navigate('/'));
  }, [navigate]);

  if (loading) {
    return (
      <>
        <Navbar />
        <div className="db-loading">
          <div className="spinner" />
          <span>Loading dashboard…</span>
        </div>
      </>
    );
  }

  return (
    <>
      <Navbar />
      <div className="db-wrap">

        {/* Row 1 — Portfolio summary bar */}
        <Portfolio user={user} />

        {/* Row 2 — AI Briefing (left, wider) + Watchlist (right) */}
        <div className="db-row db-row-mid">
          <Briefing />
          <Watchlist />
        </div>

        {/* Row 3 — Market Watch (left) + News (right) */}
        <div className="db-row db-row-bottom">
          <Marketwatch />
          <News />
        </div>

      </div>
      <Footer />
    </>
  );
}
