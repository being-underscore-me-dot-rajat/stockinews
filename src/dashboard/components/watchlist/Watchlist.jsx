import './watchlist.css'
import React, { useState, useEffect } from "react";

export default function Watchlist() {
  const [watchlist, setWatchlist] = useState([]);
  const [newSymbol, setNewSymbol] = useState("");
  const token = localStorage.getItem("token");

  const fetchWatchlist = async () => {
    try {
      const res = await fetch("http://localhost:5000/watchlist", {
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await res.json();
      if (res.ok) setWatchlist(data);
    } catch (err) {
      console.error("Fetch watchlist error:", err);
    }
  };

  const addSymbol = async () => {
    if (!newSymbol.trim()) return;
    try {
      const res = await fetch("http://localhost:5000/watchlist", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ symbol: newSymbol.toUpperCase() }),
      });
      if (res.ok) {
        setNewSymbol("");
        fetchWatchlist();
      }
    } catch (err) {
      console.error("Add symbol error:", err);
    }
  };

  const removeSymbol = async (symbol) => {
    try {
      const res = await fetch(`http://localhost:5000/watchlist/${symbol}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) fetchWatchlist();
    } catch (err) {
      console.error("Remove symbol error:", err);
    }
  };

  useEffect(() => {
    fetchWatchlist();
  }, []);

  return (
    <div className="panelStyle">
      <h2>Watchlist</h2>

      {/* Add form */}
      <div style={{ display: "flex", gap: "0.5rem", marginBottom: "1rem" }}>
        <input
          type="text"
          placeholder="Add symbol (e.g., TSLA)"
          value={newSymbol}
          onChange={(e) => setNewSymbol(e.target.value)}
          style={{ flexGrow: 1, padding: "0.5rem" }}
        />
        <button onClick={addSymbol}>Add</button>
      </div>

      {/* Watchlist Grid */}
      <div style={{ display: "grid", gap: "1rem", gridTemplateColumns: "repeat(auto-fill, minmax(250px, 1fr))" }}>
        {watchlist.map((item, idx) => (
          <div key={idx} style={{ border: "1px solid #ccc", borderRadius: "1rem", padding: "1rem" }}>
            <h4>{item.name || item.symbol}</h4>
            <p><strong>Symbol:</strong> {item.symbol}</p>
            <p><strong>Price:</strong> ${item.price?.toFixed(2) ?? "N/A"}</p>
            <p style={{ color: item.percent_change >= 0 ? "green" : "red" }}>
              <strong>Change:</strong> {item.percent_change?.toFixed(2) ?? 0}%
            </p>
            <button onClick={() => removeSymbol(item.symbol)} style={{ marginTop: "0.5rem" }}>
              Remove
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}

