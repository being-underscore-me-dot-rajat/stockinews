import React from 'react'
import './portfolio.css'

export default function Portfolio({user}) {
  return (
     <div className="panelStyle">
      <h2 className="sectionTitleStyle">Portfolio</h2>
      <p>Welcome, {user.name} </p>
      <p>Total Value: $123,456</p>
      <ul>
        <li>AAPL - 50 shares</li>
        <li>TSLA - 10 shares</li>
        {/* Add real portfolio data here */}
      </ul>
    </div>
  )
}
