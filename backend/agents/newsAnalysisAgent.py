import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
import httpx
from typing import List

from schemas.news_schema import NewsItem, NewsItemWithSentiment

load_dotenv()
ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")
NEWSDATA_API_KEY = os.getenv("NEWSDATA_API_KEY")


# Response model
class NewsAgent():

    def __init__(self):
        self.alpha_key = ALPHA_VANTAGE_API_KEY
        self.newsdata_key = NEWSDATA_API_KEY
        self.llm =ChatGoogleGenerativeAI(temperature=0.2, model="gemini-1.5-flash",google_api_key=os.getenv("GOOGLE_API_KEY"))

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


    def get_sentiment(self, title: str, summary:str) -> str:
        try:
            llm_input = {
            "title": title,
            "summary": summary,
            "sentiment": ""  # If required by your prompt template
        }

            response = self.chain.run(llm_input)
            return response.strip()  # Ensure we return only the label without extra spaces or newlines

        except Exception as e:
            print(f"Error in get_sentiment: {e}")
            return "NA"
    

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

        news_items = [
            NewsItem(
                title=article.get("title", "No Title"),
                summary=article.get("summary", "No Summary"),
                source="alpha"
            )
            for article in articles
        ]
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

        articles = data["results"][:10]
        news_items = []

        for article in articles:
            title = article.get("title", "No Title")
            summary = article.get("description", "")

            news_items.append(NewsItem(
                title=title,
                link=article.get("link", ""),
                summary=summary,
                source="newsdata"
            ))

        return news_items
    
    async def get_combined_news(self, symbol: str) -> List[NewsItem]:
        alpha_news = await self.get_alpha_news(symbol)
        newsdata_news = await self.get_newsdata_news(symbol)
        return (alpha_news + newsdata_news)[:5]
    

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
        articles = await self.get_combined_news(symbol)
        return self.add_sentiment_to_news(articles)

