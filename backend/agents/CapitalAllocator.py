# allocators/capital_allocator.py

from __future__ import annotations
from typing import Any, Dict, Optional, Literal
from schemas.capital_schema import CapitalAllocatorResponse, PortfolioState
import json
import os

try:
    from langchain_google_genai import ChatGoogleGenerativeAI
except ImportError:
    ChatGoogleGenerativeAI = None

class CapitalAllocator:
    """
    An advanced capital allocator using the Kelly Criterion for its rule-based mode.
    """

    def __init__(
        self,
        kelly_fraction: float = 0.5,  # Use a fraction of Kelly to be more conservative
        atr_multiplier: float = 2.0,  # Multiplier for ATR to set stop-loss
        mode: Literal["rule", "llm", "auto"] = "auto",
        llm_model: str = "gemini-1.5-flash",
        google_api_key: Optional[str] = None,
    ):
        if not (0 < kelly_fraction <= 1):
            raise ValueError("kelly_fraction must be between 0 and 1.")
        
        self.kelly_fraction = kelly_fraction
        self.atr_multiplier = atr_multiplier
        self.mode = mode

        # --- LLM Initialization (unchanged) ---
        self._llm = None
        if self.mode in ("llm", "auto"):
            if ChatGoogleGenerativeAI is None:
                raise RuntimeError("langchain_google_genai not installed; cannot use LLM mode.")
            self._llm = ChatGoogleGenerativeAI(
                model=llm_model,
                temperature=0.0,
                google_api_key=google_api_key or os.getenv("GOOGLE_API_KEY"),
            )

        self._prompt_template = (
"You are a portfolio risk and capital allocator. Decide capital to allocate for the given signal under strict risk constraints.\n"

"RULES:\n"

"- Never exceed cash_available, max_allocation_pct * total_equity, and max_exposure_per_ticker_pct.\n"

"- Prefer SKIP when confidence is low or news/trend conflict.\n"

"- If SELL and no position exists and shorting not permitted, use SKIP.\n"

"- Output STRICT JSON ONLY with this schema:\n"

"{\n"

'"ticker": str,\n'
' "intent": "ENTER"|"INCREASE"|"DECREASE"|"EXIT"|"SKIP",\n'
' "side": "LONG"|"SHORT"|"NA",\n'
' "allocation_cash": float,\n'
 ' "allocation_pct_of_equity": float,\n'
 ' "position_size_qty": float,\n'
 ' "suggested_stop_loss": float|null,\n'
 ' "suggested_take_profit": float|null,\n'
 ' "rationale": str\n'
 "}\n\n"

 "Signal:\n{signal_json}\n\n"
 "Portfolio:\n{portfolio_json}\n\n"
 "Risk notes:\n{risk_notes}\n"
)

    # ---------- Public API ----------
    def allocate(self, signal: Dict[str, Any], portfolio: Dict[str, Any], risk_notes: str = "") -> CapitalAllocatorResponse:
        pyd_portfolio = PortfolioState(**portfolio)

        if str(signal.get("signal", "")).upper() in ("HOLD", "SKIP"):
            return self._decision_from_cash(0.0, "SKIP", "NA", signal, pyd_portfolio, rationale="Signal is HOLD or SKIP.")

        if self.mode == "rule":
            return self._rule_allocate(signal, pyd_portfolio)

        if self.mode == "llm":
            return self._llm_allocate(signal, pyd_portfolio, risk_notes)

        # auto: try LLM first, fallback to rules
        try:
            return self._llm_allocate(signal, pyd_portfolio, risk_notes)
        except Exception as e:
            return self._rule_allocate(signal, pyd_portfolio, fallback_reason=f"LLM failed: {e}")

    # ---------- Rule-based (KELLY CRITERION) ----------
    def _rule_allocate(self, signal: Dict[str, Any], portfolio: PortfolioState, fallback_reason: Optional[str] = None) -> CapitalAllocatorResponse:
        # --- 1. Extract data and define risk ---
        equity = portfolio.total_equity
        cash = portfolio.cash_available
        current_price = float(signal.get("current_price", 0.0))
        predicted_price = float(signal.get("predicted_price", 0.0))
        atr = float(signal.get("sources", {}).get("ATR", 0.0))

        if current_price <= 0 or atr <= 0:
            return self._decision_from_cash(0.0, "SKIP", "NA", signal, portfolio, "Invalid price or ATR data.")

        stop_loss_distance = self.atr_multiplier * atr
        signal_action = str(signal.get("signal", "")).upper()

        # --- 2. Handle existing positions and determine intent ---
        ticker = signal["ticker"]
        existing_position = next((p for p in portfolio.open_positions if p.ticker == ticker), None)
        intent = "SKIP"
        side: Literal["LONG", "SHORT", "NA"] = "NA"

        if signal_action == "BUY":
            side = "LONG"
            intent = "ENTER" if not existing_position else "INCREASE"
            potential_gain = predicted_price - current_price if predicted_price > current_price else 0
            potential_loss = stop_loss_distance
        elif signal_action == "SELL":
            if existing_position:
                side = "LONG" # We are selling a long position
                intent = "EXIT" # For simplicity, we exit the full position
                # For exits, we don't need to calculate a new allocation
                return self._decision_from_cash(
                    existing_position.market_value, intent, side, signal, portfolio,
                    rationale="Rule-based decision to exit existing long position."
                )
            else: # No existing position, so this is a signal to go short
                side = "SHORT"
                intent = "ENTER"
                potential_gain = current_price - predicted_price
                potential_loss = stop_loss_distance
        
        # --- 3. Calculate Kelly Criterion ---
        # Ensure we don't proceed if the trade has no edge
        if potential_gain <= 0 or potential_loss <= 0:
            return self._decision_from_cash(0.0, "SKIP", "NA", signal, portfolio, "Trade has no statistical edge (gain/loss <= 0).")
            
        win_probability = float(signal.get("confidence", 0.5))
        loss_probability = 1 - win_probability
        win_loss_ratio = potential_gain / potential_loss

        # Kelly formula: f* = p - (q / R) where p=win prob, q=loss prob, R=win/loss ratio
        kelly_f = win_probability - (loss_probability / win_loss_ratio)
        
        # Apply conservative fraction
        safe_kelly_f = max(0.0, kelly_f * self.kelly_fraction)

        # --- 4. Calculate Allocation and Apply Constraints ---
        allocation_cash = equity * safe_kelly_f
        
        # Apply portfolio-level constraints
        max_alloc_equity = equity * portfolio.risk_limits.get("max_allocation_pct", 1.0)
        existing_mv = existing_position.market_value if existing_position else 0.0
        headroom_ticker = max(0.0, equity * portfolio.risk_limits.get("max_exposure_per_ticker_pct", 1.0) - existing_mv)
        
        final_alloc_cash = min(allocation_cash, cash, max_alloc_equity, headroom_ticker)

        rationale = (
            f"Kelly Criterion allocation. Win Prob: {win_probability:.2f}, W/L Ratio: {win_loss_ratio:.2f}. "
            f"Kelly Fraction: {safe_kelly_f:.2%}. Capped by portfolio limits."
            + (f" Fallback: {fallback_reason}" if fallback_reason else "")
        )

        # --- 5. Determine Stop-Loss/Take-Profit and Finalize ---
        sl_price = current_price - stop_loss_distance if side == "LONG" else current_price + stop_loss_distance
        tp_price = predicted_price # Use the model's prediction as the take-profit target

        return self._decision_from_cash(
            final_alloc_cash,
            intent if final_alloc_cash > 0 else "SKIP",
            side,
            signal,
            portfolio,
            rationale=rationale,
            stop_loss=sl_price,
            take_profit=tp_price,
        )

    # ---------- LLM-based ----------
    def _llm_allocate(self, signal: Dict[str, Any], portfolio: PortfolioState, risk_notes: str) -> CapitalAllocatorResponse:
        if self._llm is None:
            raise RuntimeError("LLM client not initialized.")

        prompt = self._prompt_template.format(
            signal_json=json.dumps(signal, ensure_ascii=False, indent=2),
           portfolio_json=portfolio.model_dump_json(indent=2),
            risk_notes=risk_notes or "No additional notes."
        )

        raw = self._llm.invoke(prompt).content.strip()
        data = json.loads(raw)  # must be strict JSON
        proposed = CapitalAllocatorResponse(**data)

        # hard safety clamps
        clipped = self._clip_decision(proposed, signal, portfolio)

        # sanity: if LLM gives 0 cash but not SKIP, fallback to rules
        if clipped.allocation_cash <= 0 and proposed.intent != "SKIP":
            raise ValueError("Non-positive allocation from LLM; refusing.")

        return clipped

    # ---------- Helpers ----------
    def _clip_decision(self, dec: CapitalAllocatorResponse, signal: Dict[str, Any], portfolio: PortfolioState) -> CapitalAllocatorResponse:
        equity = portfolio.total_equity
        cash = portfolio.cash_available
        limits = portfolio.risk_limits

        # per-ticker exposure headroom
        existing_mv = sum(p.market_value for p in portfolio.open_positions if p.ticker == dec.ticker)
        max_by_equity = equity * limits.get("max_allocation_pct", 0.0)
        max_by_ticker = equity * limits.get("max_exposure_per_ticker_pct", 0.0)
        headroom_ticker = max(0.0, max_by_ticker - existing_mv)

        # clamp cash and pct
        alloc_cash = min(max(0.0, dec.allocation_cash), cash, max_by_equity, headroom_ticker)
        alloc_pct = min(max(0.0, dec.allocation_pct_of_equity), limits.get("max_allocation_pct", 0.0))

        price = float(signal.get("current_price") or 0.0) or 1e-9
        qty = 0.0 if alloc_cash <= 0 else alloc_cash / price

        return CapitalAllocatorResponse(
            ticker=dec.ticker,
            intent=dec.intent,
            side=dec.side,
            allocation_cash=alloc_cash,
            allocation_pct_of_equity=alloc_pct,
            position_size_qty=qty,
            suggested_stop_loss=dec.suggested_stop_loss,
            suggested_take_profit=dec.suggested_take_profit,
            rationale=dec.rationale,
            prediction_for_time=signal.get("pred_time")
        )
    def _decision_from_cash(
        self,
        allocation_cash: float,
        intent: Literal["ENTER", "INCREASE", "DECREASE", "EXIT", "SKIP"],
        side: Literal["LONG", "SHORT", "NA"],
        signal: Dict[str, Any],
        portfolio: PortfolioState,
        rationale: str,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
    ) -> CapitalAllocatorResponse:
        equity = portfolio.total_equity
        price = float(signal.get("current_price") or 0.0) or 1e-9
        qty = 0.0 if allocation_cash <= 0 else allocation_cash / price
        pct = 0.0 if equity <= 0 else allocation_cash / equity

        return CapitalAllocatorResponse(
            ticker=signal["ticker"],
            intent=intent,
            side=side,
            allocation_cash=max(0.0, allocation_cash),
            allocation_pct_of_equity=max(0.0, pct),
            position_size_qty=max(0.0, qty),
            suggested_stop_loss=stop_loss,
            suggested_take_profit=take_profit,
            rationale=rationale,
            prediction_for_time=signal.get("pred_time")
        )