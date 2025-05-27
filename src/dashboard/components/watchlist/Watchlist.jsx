import React from 'react'
import './watchlist.css'

export default function Watchlist() {
  return (
    <div className="panelStyle">
      <h2 className="sectionTitleStyle">Watchlist</h2>
      <ul>
        <li>MSFT</li>
        <li>GOOG</li>
        <li>AMZN</li>
        {/* Add dynamic watchlist here */}
      </ul>
    </div>
  )
}
