import React, { useEffect, useState } from "react";
import { Pie } from "react-chartjs-2";
import {
  Chart as ChartJS,
  ArcElement,
  Tooltip,
  Legend
} from "chart.js";
import { useNavigate } from "react-router-dom";
import './portfolio.css'; 

ChartJS.register(ArcElement, Tooltip, Legend);

export default function Portfolio({ user }) {
  const [portfolio, setPortfolio] = useState([]);
  const [loading, setLoading] = useState(true);
  const token = localStorage.getItem("token");

  useEffect(() => {
    const fetchPortfolio = async () => {
      try {
        const res = await fetch("http://localhost:5000/portfolio", {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });
        const data = await res.json();
        if (res.ok) {
          setPortfolio(data.portfolio);  // ✅ fix: access the actual array
        }
      } catch (error) {
        console.error("Failed to fetch portfolio", error);
      } finally {
        setLoading(false);
      }
    };

    fetchPortfolio();
  }, []);

  const totalInvestment = portfolio.reduce(
    (sum, stock) => sum + (stock.quantity || 0) * (stock.buy_price || 0),
    0
  );

  const currentValue = portfolio.reduce(
    (sum, stock) => sum + (stock.quantity || 0) * (stock.current_price || 0),
    0
  );

  const percentChange = totalInvestment
    ? ((currentValue - totalInvestment) / totalInvestment) * 100
    : 0;


  const pieData = {
    labels: portfolio.map((stock) => stock.ticker),
    datasets: [
      {
        label: "Investment Share",
        data: portfolio.map((stock) => stock.quantity * stock.buy_price),
        backgroundColor: ["#f87171", "#60a5fa", "#34d399", "#facc15", "#c084fc"],
        borderWidth: 1,
      },
    ],
  };

  const navigate = useNavigate();

  if (loading) {
    return (
        <div>
            <div className="loading-spinner" role="status">
                <span className="visually-hidden">Loading...</span>
            </div>
        </div>
    );}

  return (
    <div className='panelStyle' onClick={() => navigate("/portfolio")} style={{ cursor: "pointer" }}>
  <div className="panel-content">
    <div className="portfolio-text">
      <h2>Portfolio Overview</h2>
      <p><strong>Total Investment:</strong> ${totalInvestment.toFixed(2)}</p>
      <p><strong>Current Value:</strong> ${currentValue.toFixed(2)}</p>
      <p>
        <strong>Change:</strong> {percentChange.toFixed(2)}%
        {percentChange >= 0 ? " 🔼" : " 🔽"}
      </p>
    </div>
    <div className="chart-container">
      <Pie data={pieData} />
    </div>
  </div>
</div>
  );
}
