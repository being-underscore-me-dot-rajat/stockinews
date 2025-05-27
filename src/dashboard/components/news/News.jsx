import React from 'react'
import './News.css'

export default function News() {
  return (
    <div className="panelStyle">
      <h2 className="sectionTitleStyle">News</h2>
      <article>
        <h3>Apple releases new iPhone</h3>
        <p>Apple Inc. announced the launch of their latest iPhone model...</p>
      </article>
      <article>
        <h3>Market trends this week</h3>
        <p>Markets showed bullish trends despite global uncertainties...</p>
      </article>
    </div>
  )
}
