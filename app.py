import requests
from flask import Flask, request, jsonify
from transformers import pipeline
from flask_cors import CORS  # Allow React to talk to Flask

app = Flask(__name__)
CORS(app)  # Enable CORS

# Load FinBERT sentiment analysis model
sentiment_pipeline = pipeline("text-classification", model="ProsusAI/finbert")

# Load your NewsAPI key from a file named "API_KEY" (ensure it contains your key)
API_KEY = '30152960558340f79575de8edbbe176a'

def analyze_news_sentiment(keyword, date):
    """Fetches news articles and analyzes their sentiment."""
    url = (
        "https://newsapi.org/v2/everything?"
        f"q={keyword}&"
        f"from={date}&"
        "sortBy=popularity&"
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

if __name__ == "__main__":
    app.run(debug=True)
