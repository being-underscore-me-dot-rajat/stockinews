import React from 'react';
import { CircularProgressbar, buildStyles } from 'react-circular-progressbar';
import 'react-circular-progressbar/dist/styles.css';
import './sentiment.css'

const SentimentGauge = ({ score }) => {
    const normalizedScore = (score + 1) * 50; // maps -1 to 1 → 0 to 100

    const isPositive = score >= 0;
    const primaryColor = isPositive ? '#28C947' : '#FF3B3B'; // 🍏 or 🔥
    const bgGlow = isPositive ? '0 0 20px rgba(40, 201, 71, 0.6)' : '0 0 20px rgba(255, 59, 59, 0.5)';

    return (
        <div
            className="sentiment-container"
            style={{
                width: 180,
                height: 180,
                margin: '2rem auto',
                borderRadius: '50%',
                backgroundColor: '#2D2D37',
                boxShadow: bgGlow,
                padding: '1rem',
                animation: 'fadeIn 1s ease',
            }}
        >
            <CircularProgressbar
                value={normalizedScore}
                text={`${score.toFixed(2)}`}
                styles={buildStyles({
                    textColor: primaryColor,
                    pathColor: primaryColor,
                    trailColor: '#1E1E26',
                    textSize: '18px',
                })}
            />
        </div>
    );
};

export default SentimentGauge;
