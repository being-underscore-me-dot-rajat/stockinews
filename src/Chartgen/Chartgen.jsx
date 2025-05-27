import React, { useEffect, useState } from 'react';
import { useLocation } from 'react-router-dom';
import Chart from 'chart.js/auto';

function CompanyPage() {
    const location = useLocation();
    const [chartData, setChartData] = useState(null);
    const [loading, setLoading] = useState(true);

    // Extract the company from URL
    const queryParams = new URLSearchParams(location.search);
    const company = queryParams.get('company'); // Full string like "RELIANCE.NS"

    useEffect(() => {
        if (!company) return;

        fetch(`http://127.0.0.1:5000/api/chart?ticker=${encodeURIComponent(company)}`)
            .then(response => response.json())
            .then(data => {
                setChartData(data);
                setLoading(false);
            })
            .catch(err => {
                console.error('Chart fetch error:', err);
                setLoading(false);
            });
    }, [company]);

    useEffect(() => {
        if (!chartData || !document.getElementById('stockChart')) return;

        const labels = chartData.map(point => {
            const date = new Date(point.Datetime);
            const day = date.getDate();
            const month = date.toLocaleString('default', { month: 'short' });
            const year = date.getFullYear();
            const time = date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
            return `${day}, ${month}, ${year} ${time}`;
        });

        const prices = chartData.map(point => point.Close);

        new Chart(document.getElementById('stockChart').getContext('2d'), {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: `${company} Close Price`,
                    data: prices,
                    borderColor: 'rgba(75, 192, 192, 1)',
                    borderWidth: 2,
                    fill: false,
                    tension: 0.1
                }]
            },
            options: {
                responsive: true,
                scales: {
                    x: {
                        title: { display: true, text: 'Date and Time' }
                    },
                    y: {
                        title: { display: true, text: 'Close Price (INR)' }
                    }
                }
            }
        });
    }, [chartData]);

    return (
        <div style={{ padding: '20px' }}>
            <h2>{company}</h2>
            {loading ? (
                <p>Loading chart...</p>
            ) : (
                <canvas id="stockChart" width="600" height="400"></canvas>
            )}
        </div>
    );
}

export default CompanyPage;
