import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Portfolio from './components/portfolio/portfolio';
import Marketwatch from './components/marketwatch/Marketwatch';
import Watchlist from './components/watchlist/watchlist';
import News from './components/news/news';
import Navbar from '../home/navbar/Navbar';
import './dashboard.css';

export default function Dashboard() {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [msg, setMsg] = useState("Loading...");

  useEffect(() => {
    const token = localStorage.getItem("token");
    console.log(token)

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
          navigate("/", { replace: true });
        }
      } catch (err) {
        console.error(err);
        setMsg("Error fetching user");
        navigate("/");
      }
    };

    fetchUser();
  }, [navigate]);

  if (msg === "Loading...") {
  return <div style={{ textAlign: "center", marginTop: "100px" }}>Loading Dashboard...</div>;
}


  return (
    <>
    <Navbar/>
    <div>
      <Portfolio user={user} />
      <Marketwatch/>
      <Watchlist/>
      <News />
    </div>
    </>
  );
}