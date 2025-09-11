import os
import re
from dotenv import load_dotenv
from datetime import datetime, timedelta
from typing import List, Optional

import httpx
import numpy as np
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate

from schemas.news_schema import NewsItem, NewsItemWithSentiment

# ---------- Load Environment Variables ----------
load_dotenv()
# RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
# GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

RAPIDAPI_KEY = "77437aa3c7mshd81cb72df2a011ap1618bajsn6004189195f9"
GOOGLE_API_KEY = "AIzaSyDPge6khhejK0Y1V1DkP5nF47LQrAXXm78"

class NewsAgent:
    def _init_(self):
        # LLM for sentiment classification
        self.llm = ChatGoogleGenerativeAI(
            temperature=0.2,
            model="gemini-1.5-flash",
            google_api_key=GOOGLE_API_KEY,
        )

        # Embeddings for relevancy check
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model="models/embedding-001",
            google_api_key=GOOGLE_API_KEY,
        )

        # Prompt for sentiment classification
        self.prompt = PromptTemplate(
            input_variables=["title", "summary"],
            template="""
            Given the following news details:

            Title: {title}
            Summary: {summary}

            Classify the overall sentiment as one of: Positive, Neutral, Negative.
            Respond with only the label.
            """,
        )

        self.chain = LLMChain(llm=self.llm, prompt=self.prompt)

    # ---------- UTILS ----------
    def cosine_similarity(self, a, b):
        a, b = np.array(a), np.array(b)
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

    def check_relevancy(self, symbol, article, threshold=0.5):
        """Check if article is relevant to stock symbol using embeddings."""
        try:
            query = f"{symbol} stock news"
            article_text = f"{article.title} {article.summary}"

            emb_query = self.embeddings.embed_query(query)
            emb_article = self.embeddings.embed_query(article_text)

            similarity = self.cosine_similarity(emb_query, emb_article)
            return similarity > threshold
        except Exception as e:
            print(f"Relevancy check error: {e}")
            return True  # fallback: include article if embedding fails

    def get_sentiment(self, title: str, summary: str) -> str:
        """Sync call for sentiment classification."""
        try:
            llm_input = {"title": title, "summary": summary}
            response = self.chain.run(llm_input)
            return response.strip()
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

    # ---------- NEWS FETCHER ----------
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

    # ---------- PIPELINE ----------
    async def get_news_with_sentiment(self, symbol: str) -> List[NewsItemWithSentiment]:
        raw_articles = await self.get_rapidapi_news(symbol)

        # Apply relevancy filter
        filtered_articles = [a for a in raw_articles if self.check_relevancy(symbol, a)]
        if len(filtered_articles) < 5:
            filtered_articles = raw_articles[:5]

        result = []
        for item in filtered_articles[:5]:
            sentiment = self.get_sentiment(item.title, item.summary)
            result.append(
                NewsItemWithSentiment(
                    title=item.title,
                    summary=item.summary,
                    link=item.link,
                    sentiment=sentiment,
                )
            )

        return result