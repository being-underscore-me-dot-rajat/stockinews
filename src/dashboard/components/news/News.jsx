import React, { useEffect, useState } from "react";
import './News.css';

export default function News() {
  const [news, setNews] = useState([]);
  const [Loading,setLoading]=useState(true);

  useEffect(() => {
    const fetchNews = async () => {
      try {
        const res = await fetch("http://localhost:5000/news");
        const data = await res.json();
        if (res.ok) {setNews(data.news || []);setLoading(false);}
        else {console.error("Failed to load news");setLoading(false);}
      } catch (err) {
        console.error("News fetch error:", err);setLoading(false);
      }
    };

    fetchNews();
  }, []);

  if (Loading) {
    return (
        <div>
            <div className="spinner" role="status">
                <span className="visually-hidden">Loading...</span>
            </div>
        </div>
    );}

  return (
    <div className="panelStyle scrollPanel">
      <div className="sectionTitleStyle"><h2>News</h2></div>
    {news.length === 0 ? (
  <p>No news available.</p>
) : (
  <div className="scrollContent">
  {news.map((article, idx) => (
    
    <article key={idx}>
      <h3>
        <a href={article.url} target="_blank" rel="noopener noreferrer">
          {article.title}
        </a>
      </h3>
      {article.source?.name && (
        <span className="newsMeta">Source: {article.source.name}</span>
      )}
      {article.publishedAt && (
        <span className="newsMeta">
          • {new Date(article.publishedAt).toLocaleDateString(undefined, {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
          })}
        </span>
      )}
      <p>{article.description}</p>
    </article>
    
  ))}</div>
)}
 </div> );
}
