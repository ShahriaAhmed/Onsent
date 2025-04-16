import React, { useState, useEffect } from 'react';
import { Line } from 'react-chartjs-2';
import './App.css';

import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

function App() {
  const [activeTab, setActiveTab] = useState("text");
  const [text, setText] = useState("");
  const [textResult, setTextResult] = useState(null);
  const [ticker, setTicker] = useState("");
  const [date, setDate] = useState("");
  const [newsResult, setNewsResult] = useState(null);
  const [lastWeekData, setLastWeekData] = useState(null);

  const API_URL = 'https://onsent-2fuz.onrender.com'


  const handleTextSubmit = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch(`${API_URL}/analyze-text`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text }),
      });
      const data = await response.json();
      setTextResult(data);
    } catch (error) {
      console.error("Error analyzing text:", error);
    }
  };

  const handleNewsSubmit = async (e) => {
    e.preventDefault();
    setLastWeekData(null);
    try {
      const response = await fetch(`${API_URL}/analyze-news?ticker=${ticker}&date=${date}`);
      const data = await response.json();
      setNewsResult(data);
    } catch (error) {
      console.error("Error analyzing news:", error);
    }
  };

  const handleLastWeekSubmit = async () => {
    setNewsResult(null);
    try {
      const sentimentResponse = await fetch(`${API_URL}/analyze-last-week?ticker=${ticker || "nvidia"}`);
      const sentimentData = await sentimentResponse.json();
      setLastWeekData(sentimentData.results);

    } catch (error) {
      console.error("Error retrieving last week's data:", error);
    }
  };

  const chartData = lastWeekData ? {
    labels: Object.keys(lastWeekData),
    datasets: [
      {
        label: 'Sentiment Score',
        data: Object.values(lastWeekData).map(day => {
          const score = day?.total_score || 0;
          return Math.round(score * 1000) / 1000;
        }),
        fill: false,
        borderColor: 'blue',
        tension: 0.1,
      }
    ]
  } : null;

  const chartOptions = {
    scales: {
      y: {
        type: 'linear',
        position: 'left',
        title: { display: true, text: 'Sentiment Score' },
      }
    }
  };

  return (
    <div className="container">
      <h1>Sentiment Analyzer</h1>

      <div className="tabs">
        <button className={activeTab === "text" ? "active" : ""} onClick={() => setActiveTab("text")}>Text</button>
        <button className={activeTab === "news" ? "active" : ""} onClick={() => setActiveTab("news")}>News</button>
      </div>

      {activeTab === "text" && (
        <section className="section">
          <h2>Analyze Text</h2>
          <form onSubmit={handleTextSubmit}>
            <textarea
              placeholder="Enter text to get sentiment..."
              value={text}
              onChange={(e) => setText(e.target.value)}
              rows="5"
              style={{ width: "100%" }}
            />
            <br />
            <button type="submit">Analyze Text</button>
          </form>
          {textResult && (
            <div className="result">
              <h3>Analysis Result:</h3>
              <p><strong>Sentiment:</strong> {textResult.label}</p>
              <p><strong>Score:</strong> {Number(textResult.score).toFixed(3)}</p>
            </div>
          )}
        </section>
      )}

      {activeTab === "news" && (
        <section className="section">
          <h2>News Sentiment Analysis</h2>
          <form onSubmit={handleNewsSubmit}>
            <input
              type="text"
              placeholder="Enter ticker or keywords"
              value={ticker}
              onChange={(e) => setTicker(e.target.value)}
              required
            />
            <br /><br />
            <input
              type="date"
              value={date}
              onChange={(e) => setDate(e.target.value)}
              required
            />
            <br /><br />
            <button type="submit">Analyze News (Day)</button>
          </form>
          <br />
          <button onClick={handleLastWeekSubmit}>Analyze News (Last Week)</button>

          {newsResult && (
            <div className="result">
              <h3>Overall Sentiment: {newsResult.overall_sentiment}</h3>
              <p><strong>Total Score:</strong> {Number(newsResult.total_score).toFixed(3)}</p>
              <h4>Articles:</h4>
              <ul>
                {newsResult.articles && newsResult.articles.map((article, index) => (
                  <li key={index}>
                    <a href={article.url} target="_blank" rel="noopener noreferrer">{article.title}</a><br />
                    Sentiment: {article.sentiment} {article.score != null ? `(Score: ${Number(article.score).toFixed(3)})` : ""}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {lastWeekData && chartData && (
            <div className="result">
              <h3>Last Week's Sentiment</h3>
              {chartData && <Line data={chartData} options={chartOptions} />}
            </div>
          )}
        </section>
      )}
    </div>
  );
}

export default App;
