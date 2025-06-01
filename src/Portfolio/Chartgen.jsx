import { Pie, Bar, Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  ArcElement,
  Tooltip,
  Legend,
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  TimeScale
} from 'chart.js';

ChartJS.register(
  ArcElement,
  Tooltip,
  Legend,
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  TimeScale
);

import './chartgen.css'
import React, { useEffect, useState } from 'react';
function Chartgen({portfolio}) {
const [historyData, setHistoryData] = useState(null);
  const token = localStorage.getItem('token');

  useEffect(() => {
  fetch('http://localhost:5000/api/portfolios/histories', {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    }
  })
    .then(res => res.json())
    .then(data => {
      if (data) {
        const dates = data.dates;
        const values = data.values;
        setHistoryData({
          labels: dates,
          datasets: [{
            label: 'Total Portfolio Value (₹)',
            data: values,
            fill: true,
            borderColor: 'rgba(54, 162, 235, 1)',
            backgroundColor: 'rgba(54, 162, 235, 0.2)',
            tension: 0.4,
            pointRadius: 3,
            pointHoverRadius: 6
          }]
        });
      }
    })
    .catch(err => console.error('Error loading history data:', err));
}, []);
const pieData = {
  labels: portfolio.map(item => item.ticker),
  datasets: [
    {
      label: 'Portfolio Distribution by Amount invested',
      data: portfolio.map(item => item.quantity*item.avg_price),
      backgroundColor: [
        '#FF6384', '#36A2EB', '#FFCE56', '#8E44AD', '#2ECC71', '#E67E22',
      ],
      borderWidth: 1,
    }
  ]
};

const barData = {
  labels: portfolio.map(item => item.ticker),
  datasets: [
    {
      label: 'Profit/Loss ₹',
      data: portfolio.map(item => ((item.current_price - item.avg_price) * item.quantity).toFixed(2)),
      backgroundColor: portfolio.map(item =>
        (item.current_price - item.avg_price) >= 0 ? 'rgba(46, 204, 113, 0.6)' : 'rgba(231, 76, 60, 0.6)'
      ),
      borderColor: portfolio.map(item =>
        (item.current_price - item.avg_price) >= 0 ? 'rgba(46, 204, 113, 1)' : 'rgba(231, 76, 60, 1)'
      ),
      borderWidth: 1
    }
  ]
};
return (
  <div className="charts-section">
    <h3>📈 Visual Portfolio Insights</h3>

    <div className="charts-row">
      <div className="chart-wrapper pie">
        <h4>Holdings Distribution</h4>
        <Pie data={pieData} />
      </div>

      <div className="chart-wrapper bar">
        <h4>Profit / Loss</h4>
        <Bar
          data={barData}
          options={{ responsive: true, plugins: { legend: { display: false } } }}
        />
      </div>
    </div>

    {historyData && (
      <div className="chart-wrapper line">
        <h4>Portfolio Value Over the Past Week</h4>
        <Line
          data={historyData}
          options={{
            responsive: true,
            plugins: {
              legend: { position: 'top' },
              tooltip: { mode: 'index', intersect: false },
            },
            scales: {
              x: {
                title: { display: true, text: 'Date' },
              },
              y: {
                title: { display: true, text: 'Value (₹)' },
              },
            },
          }}
        />
      </div>
    )}
  </div>
);}
export default Chartgen;