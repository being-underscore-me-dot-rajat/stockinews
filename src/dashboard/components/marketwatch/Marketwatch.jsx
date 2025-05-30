import React, { useEffect, useState } from "react";
import './marketwatch.css';

const MARKET_GROUPS = {
  index: ["^GSPC", "^DJI", "^IXIC", "^FTSE", "^GDAXI", "^FCHI", "^N225", "^HSI", "000001.SS", "^NSEI"],
  commodity: ["GC=F", "SI=F", "CL=F", "BZ=F", "NG=F", "HG=F"]
};

export default function MarketWatch() {
  const [data, setData] = useState([]);
  const [search, setSearch] = useState("");
  const [sortKey, setSortKey] = useState("name");
  const [sortAsc, setSortAsc] = useState(true);
  const [filterType, setFilterType] = useState("all");

  const token = localStorage.getItem("token");

  useEffect(() => {
    const fetchMarket = async () => {
      try {
        const res = await fetch("http://localhost:5000/marketwatch", {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });
        const result = await res.json();
        if (res.ok) {
          setData(result.market);
        }
      } catch (err) {
        console.error("Market data error:", err);
      }
    };

    fetchMarket();
  }, []);

  const getGroup = (symbol) => {
    if (MARKET_GROUPS.index.includes(symbol)) return "Index";
    if (MARKET_GROUPS.commodity.includes(symbol)) return "Commodity";
    return "Other";
  };

  const filtered = data
    .filter(item =>
      item.name?.toLowerCase().includes(search.toLowerCase()) ||
      item.symbol.toLowerCase().includes(search.toLowerCase())
    )
    .filter(item => {
      if (filterType === "all") return true;
      return getGroup(item.symbol).toLowerCase() === filterType;
    })
    .sort((a, b) => {
      const valA = a[sortKey];
      const valB = b[sortKey];
      if (valA == null || valB == null) return 0;
      return sortAsc ? valA - valB : valB - valA;
    });

  return (
    <div className="panelStyle">
      <h2>Market Watch</h2>

      {/* Controls */}
      <div style={{ display: "flex", gap: "1rem", flexWrap: "wrap", marginBottom: "1rem" }}>
        <input
          type="text"
          placeholder="Search by name or symbol..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          style={{ padding: "0.5rem", flexGrow: 1 }}
        />
        <select onChange={(e) => setFilterType(e.target.value)} value={filterType}>
          <option value="all">All</option>
          <option value="index">Indices</option>
          <option value="commodity">Commodities</option>
        </select>
        <select onChange={(e) => setSortKey(e.target.value)} value={sortKey}>
          <option value="name">Name</option>
          <option value="price">Price</option>
          <option value="percent_change">Change %</option>
        </select>
        <button onClick={() => setSortAsc(!sortAsc)}>
          Sort {sortAsc ? "▲" : "▼"}
        </button>
      </div>

      {/* Market Data Grid */}
      <div style={{ display: "grid", gap: "1rem", gridTemplateColumns: "repeat(auto-fill, minmax(250px, 1fr))" }}>
        {filtered.map((item, idx) => (
          <div key={idx} style={{
            border: "1px solid #ddd",
            borderRadius: "1rem",
            padding: "1rem",
            background: "#fafafa"
          }}>
            <h4>{item.name || item.symbol}</h4>
            <p><strong>Symbol:</strong> {item.symbol}</p>
            <p><strong>Price:</strong> ${item.price?.toFixed(2) ?? "N/A"}</p>
            <p>
              <strong>Change:</strong>{" "}
              <span style={{ color: item.percent_change >= 0 ? "green" : "red" }}>
                {item.percent_change?.toFixed(2) ?? "0.00"}%
              </span>
            </p>
            <small>{getGroup(item.symbol)}</small>
          </div>
        ))}
      </div>
    </div>
  );
}
