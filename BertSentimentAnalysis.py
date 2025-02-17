import requests
# Use a pipeline as a high-level helper
from transformers import pipeline

date = '2025-02-10'
keyword = "nvidia"
API_KEY = '30152960558340f79575de8edbbe176a'
pipe = pipeline("text-classification", model="ProsusAI/finbert")

url = (
    'https://newsapi.org/v2/everything?'
    f'q={keyword}&'
    f'from={date}&'  # FIXED: Removed extra space
    'sortBy=popularity&'
    f'apiKey={API_KEY}'
)

#rss_url = f'https://finance.yahoo.com/rss/headline?s={ticker}'
response = requests.get(url)
articles = response.json()["articles"]
articles = [article for article in articles if keyword.lower() in article['title'].lower() or keyword.lower() in article['description'].lower()]

total_score = 0
num_articles = 0

for i, article in enumerate(articles):

    print(f'Title: {article['title']}')
    print(f'Link: {article['url']}')
    sentiment = pipe(article['content'])[0]
    print(f'Sentiment {sentiment["label"]}, Score: {sentiment["score"]}')
    print("-"*40)
    
    if sentiment["label"] == "positive":
        total_score += sentiment["score"]
        num_articles += 1
    elif sentiment["label"] == "negative":
        total_score -= sentiment["score"]
        num_articles +=1
        
#final_score = total_score / num_articles
print(f'Overall Sentiment: {"Positive" if total_score >= 0.15 else "Negative" if total_score <= 0.15 else "Neutral"} {total_score}')
