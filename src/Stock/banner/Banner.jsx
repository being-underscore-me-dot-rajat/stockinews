// src/components/Banner.js
import React from 'react';
import './banner.css';

function Banner({ description, closeBanner }) {
    return (
        <>
            <div className="description-overlay">
                <h3>📌 About This Stock</h3>
                <p>
                    {description}
                </p>
                <button onClick={closeBanner}>Got it</button>
            </div>
        </>
    );
}

export default Banner;
