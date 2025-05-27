import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Portfolio from './components/portfolio/portfolio';
import Marketwatch from './components/marketwatch/Marketwatch';
import Watchlist from './components/watchlist/watchlist';
import News from './components/news/news';

const containerStyle = {
  display: "grid",
  gridTemplateColumns: "1fr 1fr",
  gridTemplateRows: "300px 400px",
  gap: "20px",
  padding: "20px",
  height: "100vh",
  backgroundColor: "#f5f7fa",
  fontFamily: "Segoe UI, Tahoma, Geneva, Verdana, sans-serif",
};

export default function Dashboard() {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [msg, setMsg] = useState("Loading...");

  useEffect(() => {
    const token = localStorage.getItem("token");

    if (!token) {
      navigate("/"); // redirect if not logged in
      return;
    }

    const fetchUser = async () => {
      try {
        const res = await fetch("http://localhost:5000/me", {
          method: "GET",
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        const data = await res.json();

        if (res.ok) {
          setUser(data.user);
          setMsg(null);
        } else {
          setMsg("Unauthorized");
          localStorage.removeItem("token");
          navigate("/");
        }
      } catch (err) {
        console.error(err);
        setMsg("Error fetching user");
        navigate("/");
      }
    };

    fetchUser();
  }, [navigate]);

  if (msg) {
    return <div className="dashboard-msg">{msg}</div>;
  }

  return (
    <div style={containerStyle}>
      <Portfolio user={user} />
      <Marketwatch/>
      <Watchlist />
      <News />
    </div>
  );
}