from datetime import datetime
from typing import List, Dict
from sqlalchemy.orm import Session
from models.agent_results_model import AgentResults
import google.generativeai as genai
import os

# Configure Google Gemini API
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Choose a Gemini model (you can switch to "gemini-1.5-flash" for speed)
GEMINI_MODEL = "gemini-1.5-flash"


class ExplainerAgent:
    """
    Fetches stored outputs from the agents (PostgreSQL)
    and generates professional explanations using Google Gemini.
    """

    def __init__(self, db: Session):
        self.db = db

    # ---------- Fetch Data ----------
    def get_all_results(self) -> List[AgentResults]:
        """Return all stored agent outputs (most recent first)."""
        return (
            self.db.query(AgentResults)
            .order_by(AgentResults.created_at.desc())
            .limit(3)
            .all()
        )

    # ---------- Build Prompt ----------
    def _build_prompt(self, result: AgentResults) -> str:
        return f"""
You are a skilled stock market analyst.  
Explain the agents'outputs in **clear, simple, yet technically accurate language** so that both finance students and retail investors can understand.  

Follow this structure and keep it concise but insightful:

### Analysis of Agent Outputs

*Overall Sentiment:*  
- State whether the outlook is Bullish, Bearish, or Neutral.  
- Add 1-2 lines on why (e.g., trend strength, price momentum, or market signals).

*Signal Agent:*  
- Explain the recommendation (Buy, Sell, Hold).  
- Mention confidence score and technical indicators used (like RSI, moving averages).  
- Use simple terms (e.g., "RSI shows the stock is overbought, meaning price might fall").

*Risk Filter:*  
- Comment on volatility and potential drawdowns.  
- Explain what the numbers mean in practice (e.g., "higher volatility means price swings are larger and riskier").  
- Make it clear whether the stock is safe for cautious investors.

*Capital Allocator:*  
- Describe how much capital is suggested for this stock.  
- Explain position sizing in plain words (e.g., "investing 20% means for every ₹100, you put ₹20 here").  
- Add risk-reward balance.

*Conclusion:*  
- Summarize how all signals align.  
- Give a practical takeaway (e.g., "Good short-term opportunity, but risky for long-term holders").  

Data provided by agents:
- Signal: {result.signal_output}
- Risk: {result.risk_output}
- Allocator: {result.allocator_output}
"""

    # ---------- Generate Explanation ----------
    def generate_explanation(self, result: AgentResults) -> str:
        prompt = self._build_prompt(result)

        try:
            response = genai.GenerativeModel(GEMINI_MODEL).generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            return f"[Error generating explanation: {e}]"

    # ---------- Main API ----------
    def explain_all(self) -> Dict:
        """Generate explanations for all stored agent runs."""
        records = self.get_all_results()
        explanations = []

        for r in records:
            explanations.append(
                {
                    "run_id": r.id,
                    "ticker": r.ticker,
                    "created_at": r.created_at.isoformat(),
                    "explanation": self.generate_explanation(r),
                }
            )

        return {"explanations": explanations}
