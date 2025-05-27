import React from 'react'
import './marketwatch.css'

export default function Marketwatch() {
  return (
    <div className='panelStyle'>
      <h2 className='sectionTitleStyle'>Market Watch</h2>
      <p>Sensex: 54,000 ↑ 0.5%</p>
      <p>Nifty: 15,700 ↑ 0.3%</p>
      {/* Add live market data or charts here */}
    </div>  
  )
}
