import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain.chains import LLMChain
import numpy as np
from langchain.prompts import PromptTemplate
# from sentence_transformers import SentenceTransformer, util
import httpx
from typing import List
import time
import re

from schemas.news_schema import NewsItem, NewsItemWithSentiment

load_dotenv()
ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")
NEWSDATA_API_KEY = os.getenv("NEWSDATA_API_KEY")
RAPIDAPI_KEY = "77437aa3c7mshd81cb72df2a011ap1618bajsn6004189195f9"
RAPIDAPI_KEY2 = "0c62ca94f5mshb07d4edd154f5ecp1b7858jsnd835753779e4"
GOOGLE_API_KEY2 = "AIzaSyDPge6khhejK0Y1V1DkP5nF47LQrAXXm78"
# Response model
class NewsAgent():

    def __init__(self):
        self.alpha_key = ALPHA_VANTAGE_API_KEY
        self.newsdata_key = NEWSDATA_API_KEY
        self.llm =ChatGoogleGenerativeAI(temperature=0.2, model="gemini-1.5-flash",google_api_key=GOOGLE_API_KEY2)
        # self.nlp_model = SentenceTransformer("all-MiniLM-L6-v2")
        self.embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=GOOGLE_API_KEY2)
         # Prompt for sentiment classification

        self.prompt = PromptTemplate(
    input_variables=["title", "summary"],
    template="""
        Given the following news details:

        Title: {title}
        Summary: {summary}
        Sentiment: {sentiment}

        Classify the overall sentiment as one of: Positive, Neutral, Negative.
        Respond with only the label.
        """
        )
        self.chain = LLMChain(llm=self.llm, prompt=self.prompt)

    # def check_relevancy(self, symbol, article, threshold: float = 0.5) -> bool:

    #     query = f"{symbol} stock news"
    #     article_text = " ".join([
    #         article.title or "",
    #         article.summary or ""
    #     ])
    #     artilce_embeddings = self.nlp_model.encode([query, article_text], convert_to_tensor=True)

    #     similarity = util.pytorch_cos_sim(artilce_embeddings[0], artilce_embeddings[1]).item()
        
    #     return similarity > threshold
    def cosine_similarity(self,a, b):
        a, b = np.array(a), np.array(b)
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

    def check_relevancy(self, symbol, article, threshold=0.5):
        query = f"{symbol} stock news"
        article_text = f"{article.title} {article.summary}"

        emb_query = self.embeddings.embed_query(query)
        emb_article = self.embeddings.embed_query(article_text)

        similarity = self.cosine_similarity(emb_query, emb_article)
        return similarity > threshold


    def get_sentiment(self, title: str, summary:str) -> str:
        try:
            llm_input = {
            "title": title,
            "summary": summary,
            "sentiment": ""  # If required by your prompt template
        }

            response = self.chain.run(llm_input)
            time.sleep(5)
            return response.strip()  # Ensure we return only the label without extra spaces or newlines

        except Exception as e:
            print(f"Error in get_sentiment: {e}")
            return "NA"
        
    @staticmethod
    def is_english(text: str) -> bool:
        """Check if text is English by ensuring all chars are ASCII."""
        try:
            text.encode(encoding="utf-8").decode("ascii")
        except UnicodeDecodeError:
            return False
        return True
    
    @staticmethod
    def clean_summary(text: str) -> str:
        """Remove HTML tags from summary."""
        return re.sub(r"<.*?>", "", text)    

# Alpha Vantage fetcher
    async def get_alpha_news(self,symbol: str) -> list[NewsItem]:
        url = (
        f"https://www.alphavantage.co/query?"
        f"function=NEWS_SENTIMENT&tickers={symbol}&apikey={ALPHA_VANTAGE_API_KEY}"
    )

        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            data = response.json()

        if "feed" not in data:
            return []

        articles = data["feed"][:10]

        # news_items = [
        #     NewsItem(
        #         title=article.get("title", "No Title"),
        #         summary=article.get("summary", "No Summary"),
        #         source="alpha"
        #     )
        #     for article in articles
        # ]
        # return news_items
        news_items = []

        for article in articles:
            title = article.get("title", "No Title")
            summary = article.get("description", "")

            news_items.append(NewsItem(
                title=title,
                link=article.get("link", ""),
                summary=summary,
                source="alpha"
            ))

        return news_items

# NewsData fetcher
    async def get_newsdata_news(self,symbol: str) -> list[NewsItem]:
        url = (
            f"https://newsdata.io/api/1/news?apikey={NEWSDATA_API_KEY}"
            f"&q={symbol}&country=in&language=en&category=business"
        )
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            data = response.json()

        if "results" not in data:
            return []

        results = data.get("results", [])
        if not isinstance(results, list):
            print("Unexpected format:", results)
            return []

        articles = results[:10]
        news_items = []

        for article in articles:
            title = article.get("title", "No Title")
            summary = article.get("description", "")

            news_items.append(NewsItem(
                title=title,
                link=article.get("link", ""),
                summary=summary or "No sUMMARRY",
                source="newsdata"
            ))

        return news_items
    
    async def get_rapidapi_news(self, symbol: str) -> List[NewsItem]:
        """Fetch news from RapidAPI News API, fixed from/to dates."""

        url = "https://news-api14.p.rapidapi.com/v2/search/articles"

        # Fixed date range
        from_date = "2025-09-01T00:00:00Z"
        to_date = "2025-09-09T11:59:59Z"

        querystring = {
            "query": symbol,
            "language": "en",
            "from": from_date,
            "to": to_date,
            "limit": "10",
        }

        headers = {
            "X-RapidAPI-Key": RAPIDAPI_KEY,
            "X-RapidAPI-Host": "news-api14.p.rapidapi.com",
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    url, headers=headers, params=querystring, timeout=30.0
                )
                response.raise_for_status()
                data = response.json()
            except httpx.HTTPStatusError as exc:
                print(f"HTTP error: {exc.response.status_code} - {exc.response.text}")
                return []
            except httpx.RequestError as exc:
                print(f"Request error: {exc.request.url!r}")
                return []

        if "data" not in data or not data["data"]:
            return []

        news_items = []
        for article in data["data"]:
            title = article.get("title", "No Title")
            summary = self.clean_summary(article.get("excerpt", "No Summary"))

            # Only include English news
            if not self.is_english(title + summary):
                continue

            news_items.append(
                NewsItem(
                    title=title,
                    summary=summary,
                    link=article.get("url", ""),
                    source="rapidapi",
                )
            )

        return news_items

    
    async def get_combined_news(self, symbol: str) -> List[NewsItem]:
        alpha_news = await self.get_alpha_news(symbol)
        newsdata_news = await self.get_newsdata_news(symbol)
        rapid_news = await self.get_rapidapi_news(symbol)
        return (alpha_news + newsdata_news + rapid_news)[:10]
    

    def add_sentiment_to_news(self, news_items: list[NewsItem]) -> list[NewsItemWithSentiment]:
        result = []
        for item in news_items:
            try:
                sentiment = self.get_sentiment(item.title, item.summary)
            except Exception as e:
                print(f"Sentiment error for article '{item.title}': {e}")
                sentiment = "NA"

            result.append(NewsItemWithSentiment(
                title=item.title,
                summary=item.summary,
                link=item.link,
                sentiment=sentiment
            ))

        return result
    
    async def get_news_with_sentiment(self, symbol: str) -> List[NewsItemWithSentiment]:
        raw_articles = await self.get_combined_news(symbol)
        # raw_articles = await self.get_rapidapi_news(symbol)
        filtered_articles = []

        for article in raw_articles:
            if self.check_relevancy(symbol, article):
                filtered_articles.append(article)
            
            if len(filtered_articles) >=5:
                break

        if len(filtered_articles) <5:
            more_news = await self.get_combined_news(symbol=symbol)
            for article in more_news:
                if self.check_relevancy(symbol,article) and article not in filtered_articles:
                    filtered_articles.append(article)
                if len(filtered_articles) >=5:
                    break
        return self.add_sentiment_to_news(filtered_articles[:5])

