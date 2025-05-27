// src/components/Banner.js
import React from 'react';

function Banner({ description, closeBanner }) {
    return (
        <>
            {/* Modal Overlay */}
            <div 
                style={{
                    position: 'fixed',
                    top: 0,
                    left: 0,
                    width: '100vw',
                    height: '100vh',
                    // backgroundColor: 'rgba(0,0,0,0.5)',
                    zIndex: '999'
                }}
                onClick={closeBanner}
            />

            {/* Modal Box */}
            <div 
                style={{
                    position: 'fixed',
                    top: '50%',
                    left: '50%',
                    transform: 'translate(-50%, -50%)',
                    zIndex: '1000',
                    backgroundColor: 'white',
                    padding: '20px',
                    border: '1px solid black',
                    boxShadow: '0 0 15px rgba(0,0,0,0.2)',
                    borderRadius: '8px',
                    maxWidth: '500px',
                    textAlign: 'center'
                }}
            >
                {/* Close Button */}
                <button 
                    onClick={closeBanner} 
                    style={{
                        position: 'absolute',
                        top: '10px',
                        right: '10px',
                        background: 'red',
                        color: 'white',
                        border: 'none',
                        borderRadius: '50%',
                        cursor: 'pointer'
                    }}
                >
                    X
                </button>
                
                {/* Display Description */}
                <p className='desc'><strong>Description:</strong></p>
                <p className='desc1'>{description}</p>
            </div>
        </>
    );
}

export default Banner;
