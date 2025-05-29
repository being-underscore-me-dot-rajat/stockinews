import React, { useEffect, useState } from "react";
import './News.css';

export default function News() {
  const [news, setNews] = useState([]);

  useEffect(() => {
    const fetchNews = async () => {
      try {
        const res = await fetch("http://localhost:5000/news");
        const data = await res.json();
        if (res.ok) setNews(data.news || []);
        else console.error("Failed to load news");
      } catch (err) {
        console.error("News fetch error:", err);
      }
    };

    fetchNews();
  }, []);

  return (
    <div className="panelStyle">
      <h2 className="sectionTitleStyle">News</h2>
      {news.length === 0 ? (
        <p>No news available.</p>
      ) : (
        news.map((article, idx) => (
          <article key={idx}>
            <h3>
              <a href={article.url} target="_blank" rel="noopener noreferrer">
                {article.title}
              </a>
            </h3>
            <p>{article.description}</p>
          </article>
        ))
      )}
    </div>
  );
}
