// SentimentGauge.js
import React from 'react';
import { CircularProgressbar, buildStyles } from 'react-circular-progressbar';
import 'react-circular-progressbar/dist/styles.css';

const SentimentGauge = ({ score }) => {
    // Normalize the score between 0 and 100 for the gauge
    const normalizedScore = (score + 1) * 50; // Convert -1 to 1 range into 0 to 100

    return (
        <div style={{ width: 150, height: 150 }}>
            <CircularProgressbar
                value={normalizedScore}
                // text={`${score.toFixed(2)}`} 
                styles={buildStyles({
                    textColor: score >= 0 ? "green" : "red",
                    pathColor: score >= 0 ? "green" : "red",
                    trailColor: "#ddd"
                })}
            />
        </div>
    );
};

export default SentimentGauge;
