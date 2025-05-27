// src/Stock/Stock.js
import React, { useEffect, useState, useMemo, useRef } from 'react';
import { useSearchParams } from 'react-router-dom';
import './stock.css';
import Navbar from '../home/navbar/Navbar';
import Banner from '../banner/Banner';
import SentimentGauge from '../Sentiment/SenitmentGauge';
import { Chart } from 'chart.js/auto';



function Stock() {
    const [searchParams] = useSearchParams();
    const company = searchParams.get('company');
    const [newsData, setNewsData] = useState([]);
    const [chartData, setChartData] = useState([]);
    const [loading, setLoading] = useState(true);
    const [selectedDescription, setSelectedDescription] = useState('');
    const [isBannerOpen, setIsBannerOpen] = useState(false);
    const [timeRange, setTimeRange] = useState('7d');  // default to 7D


    const chartRef = useRef(null);
    const chartInstanceRef = useRef(null); // <-- this keeps Chart instance

    // Reusable mean function
    const calculateMean = (arr) => arr.length ? arr.reduce((acc, num) => acc + num, 0) / arr.length : 0;

    const avgSentiment = useMemo(() => {
        const scores = newsData.map(article => article.sentiment_score);
        return calculateMean(scores);
    }, [newsData]);

        useEffect(() => {
        if (!company) return;
        setLoading(true);
        fetch(`http://127.0.0.1:5000/api/details?company=${company}`)
            .then(response => response.json())
            .then(data => {
                setNewsData(data);
                setLoading(false);
            })
            .catch(error => {
                console.error('Error fetching company data:', error);
                setLoading(false);
            });
    }, [company]);
    useEffect(() => {
    if (!company || !timeRange) return;

    // Extract ticker for API call
    const ticker = company.split(':')[0].trim();

    fetch(`http://127.0.0.1:5000/api/chart?ticker=${ticker}&period=${timeRange}`)
        .then(response => response.json())
        .then(data => {
            setChartData(data);
        })
        .catch(error => {
            console.error('Error fetching chart data:', error);
        });
}, [company, timeRange]);


    // Render chart when chartData updates
    useEffect(() => {
        if (!chartData.length || !chartRef.current) return;

        const ctx = chartRef.current.getContext('2d');
        if (!ctx) return;

        if (chartInstanceRef.current) {
            chartInstanceRef.current.destroy();
        }

        const labels = chartData.map(point => {
            const date = new Date(point.Datetime);
            const day = date.getDate();
            const month = date.toLocaleString('default', { month: 'short' });
            const year = date.getFullYear();
            const time = date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
            return `${day}, ${month}, ${year} ${time}`;
        });

        const prices = chartData.map(point => point.Close);

        chartInstanceRef.current = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Close Price',
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
                        title: { display: true, text: 'Time' }
                    },
                    y: {
                        title: { display: true, text: 'Price (INR)' }
                    }
                }
            }
        });
    }, [chartData]);

        // UI rendering
        if (loading) {
            return <div className="spinner-grow text-danger" role="status"></div>;
        }

        return (
            <div>
                <Navbar />
                <div className="container mt-5">
                    <div className="d-flex flex-row flex-nowrap justify-content-center">
                        {newsData.map((article, index) => (
                            <div key={index} className='card me-3'>
                                <div className='card-body'>
                                    <a href={article.url} target="_blank" rel="noopener noreferrer" className="btn btn-primary">{article.title}</a>
                                    <br />
                                    <a href="#" onClick={() => setIsBannerOpen(true) || setSelectedDescription(article.description)} className='card-text'>
                                        Show Description
                                    </a>
                                    <p>Sentiment = {article.sentiment}</p>
                                </div>
                            </div>
                        ))}
                    </div>

                </div>
                <div className="container mt-5">
                    <h4>Stock Price Chart</h4>

                    {/* Time Range Buttons */}
                    <div className="mb-3">
                        <button className="btn btn-outline-primary me-2" onClick={() => setTimeRange('7d')}>7 Days</button>
                        <button className="btn btn-outline-primary me-2" onClick={() => setTimeRange('1mo')}>1 Month</button>
                        <button className="btn btn-outline-primary me-2" onClick={() => setTimeRange('6mo')}>6 Months</button>
                        <button className="btn btn-outline-primary" onClick={() => setTimeRange('1y')}>1 Year</button>
                        <button className="btn btn-outline-primary" onClick={() => setTimeRange('max')}>Max</button>
                    </div>

                    <canvas ref={chartRef} width="800" height="400"></canvas>
                </div>


                <SentimentGauge score={avgSentiment} />

                {isBannerOpen && (
                    <Banner
                        description={selectedDescription}
                        closeBanner={() => {
                            setIsBannerOpen(false);
                            setSelectedDescription('');
                        }}
                    />
                )}
            </div>
        );

    }
    export default Stock;