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
        # self.nlp_model = SentenceTransformer("all-MiniLM-L6-v2")
        self.embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=os.getenv("GOOGLE_API_KEY"))

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
    
    async def get_combined_news(self, symbol: str) -> List[NewsItem]:
        alpha_news = await self.get_alpha_news(symbol)
        newsdata_news = await self.get_newsdata_news(symbol)
        return (alpha_news + newsdata_news)[:10]
    

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

