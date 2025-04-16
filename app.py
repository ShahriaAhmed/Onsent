from datetime import datetime, timedelta
from flask import Flask, request, jsonify
import requests
from transformers import pipeline
from flask_cors import CORS

app = Flask(__name__)
CORS(app, origins=[
    "http://localhost:3000",                  # for local development
    "https://onsent.vercel.app", # your Vercel preview domain
    "https://www.onsent.xyz"              # your custom domain via GoDaddy
])
# Load FinBERT sentiment analysis model
sentiment_pipeline = pipeline("text-classification", model="ProsusAI/finbert")

# Load your NewsAPI key from a file named "API_KEY" (ensure it contains your key)


def analyze_news_sentiment(keyword, date):
    """Fetches news articles and analyzes their sentiment."""
    url = (
        "https://newsapi.org/v2/everything?"
        f"q={keyword}&"
        f"from={date}&"
        "sortBy=popularity&"
        "language=en&"  # Added filter
        f"apiKey={API_KEY}"
    )

    response = requests.get(url)
    data = response.json()

    if "articles" not in data:
        return {"error": "Invalid response from NewsAPI", "details": data}

    articles = data["articles"]
    # Filter articles where the keyword appears in the title or description

    filtered_articles = [
        article for article in articles
        if keyword.lower() in article.get("title", "").lower() or
           keyword.lower() in article.get("description", "").lower()
    ]

    results = []
    total_score = 0
    num_articles = 0

    for article in filtered_articles:
        title = article.get("title", "No title")
        url_article = article.get("url", "No URL")
        content = article.get("content", "")

        if content:
            sentiment = sentiment_pipeline(content)[0]
            sentiment_label = sentiment["label"]
            sentiment_score = sentiment["score"]

            # Tally overall score (you can adjust thresholds/logic as needed)
            if sentiment_label == "positive":
                total_score += sentiment_score
            elif sentiment_label == "negative":
                total_score -= sentiment_score
            num_articles += 1

            results.append({
                "title": title,
                "url": url_article,
                "sentiment": sentiment_label,
                "score": sentiment_score
            })
        else:
            results.append({
                "title": title,
                "url": url_article,
                "sentiment": "No content available",
                "score": None
            })

    if num_articles > 0:
        if total_score > 0.15:
            overall_sentiment = "Positive"
        elif total_score < -0.15:
            overall_sentiment = "Negative"
        else:
            overall_sentiment = "Neutral"
    else:
        overall_sentiment = "No relevant articles found."

    return {
        "keyword": keyword,
        "date": date,
        "total_score": total_score,
        "overall_sentiment": overall_sentiment,
        "articles": results
    }

def analyze_news_for_day(keyword, day_str):
    """Return an aggregate sentiment for a specific day."""
    url = (
        "https://newsapi.org/v2/everything?"
        f"q={keyword}&"
        f"from={day_str}&"
        f"to={day_str}&"
        "sortBy=popularity&"
        "language=en&"  # Added filter
        f"apiKey={API_KEY}"
    )
    response = requests.get(url)
    data = response.json()
    articles = data.get("articles", [])
    total_score = 0
    num_articles = 0

    for article in articles:
        content = article.get("content", "")
        if content:
            sentiment = sentiment_pipeline(content)[0]
            label = sentiment["label"]
            score = sentiment["score"]
            if label == "positive":
                total_score += score
            elif label == "negative":
                total_score -= score
            num_articles += 1

    if num_articles > 0:
        if total_score > 0.15:
            overall = "Positive"
        elif total_score < -0.15:
            overall = "Negative"
        else:
            overall = "Neutral"
    else:
        overall = "No data"

    return {"overall_sentiment": overall, "total_score": total_score, "articles_analyzed": num_articles}

@app.route("/", methods=["GET"])
def home():
    return "Flask API for FinBERT Sentiment Analysis is running!"

@app.route("/analyze-text", methods=["POST"])
def analyze_text():
    """Analyze sentiment for raw text."""
    data = request.get_json()
    if not data or "text" not in data:
        return jsonify({"error": "Missing 'text' in request body"}), 400

    text = data["text"]
    result = sentiment_pipeline(text)[0]
    return jsonify(result)

@app.route("/analyze-news", methods=["GET"])
def analyze_news():
    """Analyze news sentiment for a given ticker (keyword) and date."""
    keyword = request.args.get("ticker", default="nvidia", type=str)
    date = request.args.get("date", default="2025-02-10", type=str)
    result = analyze_news_sentiment(keyword, date)
    return jsonify(result)

@app.route("/analyze-last-week", methods=["GET"])
def analyze_last_week():
    """Return the sentiment analysis for each business day over the last week."""
    keyword = request.args.get("ticker", default="nvidia", type=str)

    # Determine last full business week (Monday-Friday)
    today = datetime.today().date()
    # Subtract 7 days to move to last week
    last_week = today - timedelta(days=7)
    # Find the Monday of last week (weekday() returns 0 for Monday, 6 for Sunday)
    monday_last_week = last_week - timedelta(days=last_week.weekday())

    # Collect business days Monday to Friday
    business_days = [monday_last_week + timedelta(days=i) for i in range(5)]

    results = {}
    for day in business_days:
        day_str = day.isoformat()  # format YYYY-MM-DD
        day_result = analyze_news_for_day(keyword, day_str)
        results[day_str] = day_result

    return jsonify({"ticker": keyword, "results": results})

if __name__ == "__main__":
    app.run(debug=True)
