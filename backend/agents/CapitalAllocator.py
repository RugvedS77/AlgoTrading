# allocators/capital_allocator.py
from __future__ import annotations
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Literal
import numpy as np
from schemas.capital_schema import PortfolioState, AllocationDecision
import json
import math
import os

# Optional: only needed if you want LLM mode
try:
    from langchain_google_genai import ChatGoogleGenerativeAI # type: ignore
except Exception:
    ChatGoogleGenerativeAI = None

# ---------- Capital Allocator ----------
class CapitalAllocator:
    """
    One allocator with both rule and LLM logic.
    - mode="rule": rule-based only
    - mode="llm":  LLM proposal + safety clamps
    - mode="auto": try LLM, fallback to rules on any error
    """

    def __init__(
        self,
        total_capital_hint: Optional[float] = None,           # optional hint if portfolio not passed in
        risk_per_trade: float = 0.02,                         # used by rule mode
        max_allocation_pct: float = 0.2,                      # used by rule mode
        llm_model: str = "gemini-1.5-flash",
        google_api_key: Optional[str] = None,
        temperature: float = 0.0,
        mode: Literal["rule", "llm", "auto"] = "auto",
    ):
        self.total_capital_hint = total_capital_hint
        self.risk_per_trade = risk_per_trade
        self.max_allocation_pct = max_allocation_pct
        self.mode = mode

        self._llm = None
        if self.mode in ("llm", "auto"):
            if ChatGoogleGenerativeAI is None:
                raise RuntimeError("langchain_google_genai not installed; cannot use LLM mode.")
            self._llm = ChatGoogleGenerativeAI(
                model=llm_model,
                temperature=temperature,
                google_api_key=google_api_key or os.getenv("GOOGLE_API_KEY"),
            )

        # static prompt
        self._prompt_template = (
            "You are a portfolio risk and capital allocator. Decide capital to allocate for the given signal under strict risk constraints.\n"
            "RULES:\n"
            "- Never exceed cash_available, max_allocation_pct * total_equity, and max_exposure_per_ticker_pct.\n"
            "- Prefer SKIP when confidence is low or news/trend conflict.\n"
            "- If SELL and no position exists and shorting not permitted, use SKIP.\n"
            "- Output STRICT JSON ONLY with this schema:\n"
            "{\n"
            '  "ticker": str,\n'
            '  "intent": "ENTER"|"INCREASE"|"DECREASE"|"EXIT"|"SKIP",\n'
            '  "side": "LONG"|"SHORT"|"NA",\n'
            '  "allocation_cash": float,\n'
            '  "allocation_pct_of_equity": float,\n'
            '  "position_size_qty": float,\n'
            '  "suggested_stop_loss": float|null,\n'
            '  "suggested_take_profit": float|null,\n'
            '  "rationale": str\n'
            "}\n\n"
            "Signal:\n{signal_json}\n\n"
            "Portfolio:\n{portfolio_json}\n\n"
            "Risk notes:\n{risk_notes}\n"
        )

    

    # ---------- Public API ----------
    def allocate(self, signal: Dict[str, Any], portfolio: Dict[str, Any], risk_notes: str = "") -> AllocationDecision:
        """
        signal: dict from your SignalAgent (ticker, signal, confidence, sources{}, current_price, predicted_price, timestamp)
        portfolio: dict matching PortfolioState
        """
        pyd_portfolio = PortfolioState(**portfolio)

        # short-circuit HOLD
        if str(signal.get("signal", "")).upper() == "HOLD":
            return self._decision_from_cash(0.0, "SKIP", "NA", signal, pyd_portfolio, rationale="Signal is HOLD.")

        if self.mode == "rule":
            return self._rule_allocate(signal, pyd_portfolio)

        if self.mode == "llm":
            return self._llm_allocate(signal, pyd_portfolio, risk_notes)

        # auto: try LLM first, fallback to rules
        try:
            return self._llm_allocate(signal, pyd_portfolio, risk_notes)
        except Exception as e:
            return self._rule_allocate(signal, pyd_portfolio, fallback_reason=f"LLM failed: {e}")

    # ---------- Rule-based ----------
    def _rule_allocate(self, signal: Dict[str, Any], portfolio: PortfolioState, fallback_reason: Optional[str] = None) -> AllocationDecision:
        equity = portfolio.total_equity
        cash = portfolio.cash_available

        confidence = float(signal.get("confidence", 0.0))
        movement = str(signal.get("sources", {}).get("movement", "flat")).lower()
        tilt = 1.0 + (0.1 if movement == "up" else -0.1 if movement == "down" else 0.0)

        base = equity * self.risk_per_trade * max(0.0, min(1.0, confidence)) * tilt

        # cap by service-level limits
        alloc_cap = min(base, cash, equity * self.max_allocation_pct)

        # also cap by per-ticker exposure
        ticker = signal["ticker"]
        existing_mv = sum(p.market_value for p in portfolio.open_positions if p.ticker == ticker)
        headroom_ticker = max(0.0, equity * portfolio.risk_limits.max_exposure_per_ticker_pct - existing_mv)
        alloc_cap = min(alloc_cap, headroom_ticker)

        side = "LONG" if str(signal["signal"]).upper() == "BUY" else ("SHORT" if str(signal["signal"]).upper() == "SELL" else "NA")
        rationale = (
            f"Rule-based allocation. Confidence tilt {tilt:.2f}. "
            f"Caps applied (cash/equity/ticker)."
            + (f" Fallback: {fallback_reason}" if fallback_reason else "")
        )

        return self._decision_from_cash(alloc_cap, "ENTER" if alloc_cap > 0 else "SKIP", side, signal, portfolio, rationale=rationale)

    # ---------- LLM-based ----------
    def _llm_allocate(self, signal: Dict[str, Any], portfolio: PortfolioState, risk_notes: str) -> AllocationDecision:
        if self._llm is None:
            raise RuntimeError("LLM client not initialized.")

        prompt = self._prompt_template.format(
            signal_json=json.dumps(signal, ensure_ascii=False),
            portfolio_json=portfolio.json(),
            risk_notes=risk_notes or "No additional notes."
        )

        raw = self._llm.invoke(prompt).content.strip()
        data = json.loads(raw)  # must be strict JSON
        proposed = AllocationDecision(**data)

        # hard safety clamps
        clipped = self._clip_decision(proposed, signal, portfolio)

        # sanity: if LLM gives 0 cash but not SKIP, fallback to rules
        if clipped.allocation_cash <= 0 and proposed.intent != "SKIP":
            raise ValueError("Non-positive allocation from LLM; refusing.")

        return clipped

    # ---------- Helpers ----------
    def _clip_decision(self, dec: AllocationDecision, signal: Dict[str, Any], portfolio: PortfolioState) -> AllocationDecision:
        equity = portfolio.total_equity
        cash = portfolio.cash_available
        limits = portfolio.risk_limits

        # per-ticker exposure headroom
        existing_mv = sum(p.market_value for p in portfolio.open_positions if p.ticker == dec.ticker)
        max_by_equity = equity * limits.max_allocation_pct
        max_by_ticker = equity * limits.max_exposure_per_ticker_pct
        headroom_ticker = max(0.0, max_by_ticker - existing_mv)

        # clamp cash and pct
        alloc_cash = min(max(0.0, dec.allocation_cash), cash, max_by_equity, headroom_ticker)
        alloc_pct = min(max(0.0, dec.allocation_pct_of_equity), limits.max_allocation_pct)

        price = float(signal.get("current_price") or 0.0) or 1e-9
        qty = 0.0 if alloc_cash <= 0 else alloc_cash / price

        return AllocationDecision(
            ticker=dec.ticker,
            intent=dec.intent,
            side=dec.side,
            allocation_cash=alloc_cash,
            allocation_pct_of_equity=alloc_pct,
            position_size_qty=qty,
            suggested_stop_loss=dec.suggested_stop_loss,
            suggested_take_profit=dec.suggested_take_profit,
            rationale=dec.rationale,
        )

    def _decision_from_cash(
        self,
        allocation_cash: float,
        intent: Literal["ENTER", "INCREASE", "DECREASE", "EXIT", "SKIP"],
        side: Literal["LONG", "SHORT", "NA"],
        signal: Dict[str, Any],
        portfolio: PortfolioState,
        rationale: str,
    ) -> AllocationDecision:
        equity = portfolio.total_equity or self.total_capital_hint or 0.0
        price = float(signal.get("current_price") or 0.0) or 1e-9
        qty = 0.0 if allocation_cash <= 0 else allocation_cash / price
        pct = 0.0 if equity <= 0 else min(allocation_cash / equity, portfolio.risk_limits.max_allocation_pct)

        return AllocationDecision(
            ticker=signal["ticker"],
            intent=intent,
            side=side,
            allocation_cash=max(0.0, allocation_cash),
            allocation_pct_of_equity=max(0.0, pct),
            position_size_qty=max(0.0, qty),
            suggested_stop_loss=None,
            suggested_take_profit=None,
            rationale=rationale,
        )


# ---------- Example usage ----------
if __name__ == "__main__":
    signal = {
        "ticker": "ONGC",
        "signal": "BUY",
        "confidence": 0.72,
        "sources": {"trend_score": 0.65, "news_score": -0.10, "price_diff": 0.015, "movement": "up"},
        "current_price": 270.5,
        "predicted_price": 278.2,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    portfolio = {
        "total_equity": 1_000_000.0,
        "cash_available": 200_000.0,
        "open_positions": [],
        "risk_limits": {
            "max_allocation_pct": 0.15,
            "max_risk_per_trade_pct": 0.02,
            "max_exposure_per_ticker_pct": 0.20,
        },
        "realized_drawdown_30d_pct": 0.05,
        "portfolio_volatility_30d_pct": 0.18,
    }

    # RULE ONLY
    rule_alloc = CapitalAllocator(mode="rule", risk_per_trade=0.02, max_allocation_pct=0.15)
    print("RULE:", rule_alloc.allocate(signal, portfolio).dict())

    # LLM (auto with fallback)
    llm_alloc = CapitalAllocator(mode="auto", risk_per_trade=0.02, max_allocation_pct=0.15)
    print("AUTO:", llm_alloc.allocate(signal, portfolio).dict())
