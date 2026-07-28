"""
Chat & LLM Service - Handles AI-powered chat and insights.
Integrates with Anthropic Claude for streaming responses with full context injection.
Includes token budget management and conversation history.
"""

import os
import logging
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, AsyncGenerator, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class ChatMessageType(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class TokenBudget:
    """Manages per-user token budgets to control LLM costs."""

    def __init__(self):
        self.daily_limit = int(os.getenv("CHAT_DAILY_TOKEN_LIMIT", "100000"))
        self.per_message_limit = int(os.getenv("CHAT_MAX_TOKENS_PER_MESSAGE", "4096"))
        self.context_window = int(os.getenv("CHAT_CONTEXT_WINDOW_TOKENS", "8000"))

    def get_user_usage(self, db, user_id: str) -> Dict[str, Any]:
        """Get current token usage for a user today."""
        try:
            today = datetime.utcnow().strftime("%Y-%m-%d")
            response = db.supabase.table("chat_messages") \
                .select("token_count") \
                .eq("user_id", user_id) \
                .gte("created_at", f"{today}T00:00:00") \
                .eq("role", "assistant") \
                .execute()

            total_used = sum(msg.get("token_count", 0) for msg in (response.data or []))
            return {
                "used": total_used,
                "remaining": max(0, self.daily_limit - total_used),
                "limit": self.daily_limit,
                "exceeded": total_used >= self.daily_limit,
            }
        except Exception as e:
            logger.warning(f"Token budget check failed: {e}")
            return {"used": 0, "remaining": self.daily_limit, "limit": self.daily_limit, "exceeded": False}

    def check_budget(self, db, user_id: str) -> bool:
        """Check if user has remaining token budget."""
        usage = self.get_user_usage(db, user_id)
        return not usage["exceeded"]


class ChatService:
    """Manages user chat interactions with real LLM integration."""

    def __init__(self, db):
        self.db = db
        self.context_limit = 20
        self.token_budget = TokenBudget()
        self._anthropic_client = None

        self.system_prompt = """You are AlphaAI, an expert cryptocurrency trading assistant built into the AlphaForge platform. You help users understand their portfolio, signals, risk exposure, and market conditions.

Key capabilities:
- Analyze user's current portfolio positions and P&L
- Explain trading signals and their reasoning (drivers)
- Assess risk exposure and suggest risk management
- Discuss market sentiment and technical indicators
- Help with strategy selection and copy trading decisions

Guidelines:
- Always reference the user's actual data when available
- Be concise but informative (2-4 paragraphs max per response)
- Use financial terminology correctly
- Include actionable insights when possible
- Link to relevant platform features when appropriate
- Never give financial advice — frame as analysis and education
- If asked about specific trade actions, remind users to verify risk limits

When you reference data, use the provided context. If data is unavailable, say so honestly."""

    @property
    def anthropic_client(self):
        """Lazy-init Anthropic client."""
        if self._anthropic_client is None:
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if api_key:
                try:
                    import anthropic
                    self._anthropic_client = anthropic.Anthropic(api_key=api_key)
                except ImportError:
                    logger.warning("anthropic package not installed, using fallback responses")
            else:
                logger.info("No ANTHROPIC_API_KEY set, using template-based responses")
        return self._anthropic_client

    async def save_message(
        self,
        user_id: str,
        message: str,
        role: str = "user",
        token_count: int = 0,
        context: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """Save a chat message to database."""
        try:
            msg_data = {
                "user_id": user_id,
                "message": message,
                "role": role,
                "token_count": token_count,
                "context": json.dumps(context) if context else None,
                "created_at": datetime.utcnow().isoformat(),
            }

            response = self.db.supabase.table("chat_messages").insert(msg_data).execute()

            if response.data:
                return {"success": True, "message_id": response.data[0]["id"]}

        except Exception as e:
            logger.error(f"Failed to save chat message: {e}")

        return {"success": False, "error": str(e)}

    async def get_chat_history(
        self,
        user_id: str,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Retrieve chat history for a user."""
        try:
            response = self.db.supabase.table("chat_messages") \
                .select("*") \
                .eq("user_id", user_id) \
                .order("created_at", desc=True) \
                .limit(limit) \
                .execute()

            messages = response.data or []
            messages.reverse()
            return messages

        except Exception as e:
            logger.error(f"Failed to fetch chat history: {e}")
            return []

    async def get_context_for_response(
        self,
        user_id: str,
        portfolio_service=None,
        signal_processor=None,
        signal_id: Optional[str] = None,
        strategy_id: Optional[str] = None,
        page_context: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Build comprehensive context information for AI response from all available services."""
        context: Dict[str, Any] = {
            "user_id": user_id,
            "page_context": page_context,
            "timestamp": datetime.utcnow().isoformat(),
        }

        try:
            if portfolio_service:
                portfolio = await portfolio_service.get_portfolio_summary(user_id)
                context["portfolio"] = portfolio

            signals_response = self.db.supabase.table("signals") \
                .select("*") \
                .order("created_at", desc=True) \
                .limit(10) \
                .execute()
            context["recent_signals"] = signals_response.data or []

            if signal_id:
                sig_resp = self.db.supabase.table("signals") \
                    .select("*") \
                    .eq("id", signal_id) \
                    .single() \
                    .execute()
                if sig_resp.data:
                    context["focused_signal"] = sig_resp.data

            positions_response = self.db.supabase.table("positions") \
                .select("*") \
                .eq("user_id", user_id) \
                .execute()
            context["open_positions"] = positions_response.data or []

            strategies_response = self.db.supabase.table("strategies") \
                .select("*") \
                .limit(5) \
                .execute()
            context["strategies"] = strategies_response.data or []

            if strategy_id:
                strat_resp = self.db.supabase.table("strategies") \
                    .select("*") \
                    .eq("id", strategy_id) \
                    .single() \
                    .execute()
                if strat_resp.data:
                    context["focused_strategy"] = strat_resp.data

        except Exception as e:
            logger.error(f"Failed to build context: {e}")

        return context

    def _format_context_for_llm(self, context: Dict[str, Any]) -> str:
        """Format the context dictionary into a readable string for the LLM system prompt."""
        parts = []

        portfolio = context.get("portfolio")
        if portfolio:
            parts.append(
                f"Portfolio Summary:\n"
                f"- Total Equity: ${portfolio.get('total_equity', 0):,.2f}\n"
                f"- Unrealized PnL: ${portfolio.get('unrealized_pnl', 0):,.2f}\n"
                f"- Realized PnL: ${portfolio.get('realized_pnl', 0):,.2f}\n"
                f"- Open Positions: {portfolio.get('open_positions', 0)}\n"
                f"- Total Trades: {portfolio.get('total_trades', 0)}"
            )

        positions = context.get("open_positions", [])
        if positions:
            pos_lines = []
            for p in positions[:5]:
                pos_lines.append(
                    f"  - {p.get('asset', 'N/A')} {p.get('direction', 'N/A')} "
                    f"entry={p.get('entry_price', 0)} current={p.get('current_price', 0)} "
                    f"pnl={p.get('unrealized_pnl', 0):.2f} ({p.get('unrealized_pnl_percent', 0):.1f}%)"
                )
            parts.append("Open Positions:\n" + "\n".join(pos_lines))

        signals = context.get("recent_signals", [])
        if signals:
            sig_lines = []
            for s in signals[:5]:
                sig_lines.append(
                    f"  - {s.get('ticker', 'N/A')} {s.get('signal_type', 'N/A')} "
                    f"confidence={s.get('confidence', 0):.0%} "
                    f"entry={s.get('entry_price', 0)} SL={s.get('stop_loss_price', 0)} "
                    f"TP={s.get('take_profit_price', 0)}"
                )
            parts.append("Recent Signals:\n" + "\n".join(sig_lines))

        focused_signal = context.get("focused_signal")
        if focused_signal:
            parts.append(
                f"Focused Signal (user is viewing this):\n"
                f"  Asset: {focused_signal.get('ticker', 'N/A')}\n"
                f"  Direction: {focused_signal.get('signal_type', 'N/A')}\n"
                f"  Confidence: {focused_signal.get('confidence', 0):.0%}\n"
                f"  Entry: {focused_signal.get('entry_price', 0)}\n"
                f"  Stop Loss: {focused_signal.get('stop_loss_price', 0)}\n"
                f"  Take Profit: {focused_signal.get('take_profit_price', 0)}\n"
                f"  Rationale: {focused_signal.get('rationale', 'N/A')}\n"
                f"  Drivers: {json.dumps(focused_signal.get('drivers', []))}"
            )

        strategies = context.get("strategies", [])
        if strategies:
            strat_lines = []
            for st in strategies[:3]:
                strat_lines.append(
                    f"  - {st.get('name', 'N/A')}: win_rate={st.get('win_rate', 0):.1f}% "
                    f"sharpe={st.get('sharpe_ratio', 0):.2f} "
                    f"trades={st.get('total_trades', 0)}"
                )
        return "\n\n".join(parts) if parts else "No portfolio or signal data available."

    async def generate_response(
        self,
        user_id: str,
        message: str,
        context: Dict[str, Any],
        signal_id: Optional[str] = None,
        strategy_id: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        """Generate AI response with streaming, using Anthropic Claude or fallback."""
        if not self.token_budget.check_budget(self.db, user_id):
            yield "You've reached your daily message limit. Please try again tomorrow."
            return

        await self.save_message(user_id, message, "user")

        history = await self.get_chat_history(user_id, limit=self.context_limit)

        if self.anthropic_client:
            async for chunk in self._stream_claude_response(user_id, message, context, history):
                yield chunk
        else:
            response_text = await self._generate_fallback_response(message, context)
            await self.save_message(user_id, response_text, "assistant", token_count=0, context=context)
            yield response_text

    async def _stream_claude_response(
        self,
        user_id: str,
        message: str,
        context: Dict[str, Any],
        history: List[Dict[str, Any]],
    ) -> AsyncGenerator[str, None]:
        """Stream response from Anthropic Claude."""
        context_str = self._format_context_for_llm(context)

        messages = []
        for msg in history[-self.context_limit:]:
            role = msg.get("role", "user")
            if role in ("user", "assistant"):
                messages.append({"role": role, "content": msg.get("message", "")})

        messages.append({"role": "user", "content": message})

        full_response = ""
        token_count = 0

        try:
            with self.anthropic_client.messages.stream(
                model=os.getenv("CHAT_MODEL", "claude-sonnet-4-20250514"),
                max_tokens=self.token_budget.per_message_limit,
                system=f"{self.system_prompt}\n\nCurrent User Context:\n{context_str}",
                messages=messages,
            ) as stream:
                for text in stream.text_stream:
                    full_response += text
                    token_count += len(text.split()) * 1.3
                    yield text

            await self.save_message(
                user_id,
                full_response,
                "assistant",
                token_count=int(token_count),
                context=context,
            )

        except Exception as e:
            logger.error(f"Claude streaming error: {e}")
            fallback = await self._generate_fallback_response(message, context)
            await self.save_message(user_id, fallback, "assistant", token_count=0, context=context)
            yield fallback

    async def _generate_fallback_response(
        self,
        message: str,
        context: Dict[str, Any],
    ) -> str:
        """Generate template-based response when LLM is unavailable."""
        message_lower = message.lower()
        portfolio = context.get("portfolio", {})
        open_positions = context.get("open_positions", [])
        signals = context.get("recent_signals", [])

        if any(word in message_lower for word in ["portfolio", "balance", "equity"]):
            total_equity = portfolio.get("total_equity", 100000)
            pnl = portfolio.get("unrealized_pnl", 0)
            return (
                f"Your portfolio currently has ${total_equity:,.2f} in total equity "
                f"with ${pnl:,.2f} unrealized P&L. You have {len(open_positions)} open positions. "
                f"Would you like me to analyze any specific position?"
            )

        elif any(word in message_lower for word in ["signal", "trade", "recommendation"]):
            if signals:
                top = signals[0]
                return (
                    f"Latest signal: {top.get('signal_type', 'N/A')} {top.get('ticker', 'N/A')} "
                    f"with {top.get('confidence', 0):.0%} confidence. "
                    f"Entry: ${top.get('entry_price', 0):,.2f}, "
                    f"SL: ${top.get('stop_loss_price', 0):,.2f}, "
                    f"TP: ${top.get('take_profit_price', 0):,.2f}. "
                    f"Would you like to copy this strategy?"
                )
            return "No active signals at the moment. I'll alert you when new ones appear."

        elif any(word in message_lower for word in ["risk", "volatility", "drawdown"]):
            return (
                f"Your current portfolio has {len(open_positions)} open positions. "
                f"I recommend reviewing your total exposure and ensuring no single asset "
                f"exceeds 20% of your portfolio. Want me to run a detailed risk analysis?"
            )

        return (
            "I can help you analyze your portfolio, review signals, assess risk, "
            "or discuss market conditions. What would you like to explore?"
        )

    async def get_token_usage(self, user_id: str) -> Dict[str, Any]:
        """Get token usage stats for a user."""
        return self.token_budget.get_user_usage(self.db, user_id)

    async def search_chat_history(
        self,
        user_id: str,
        query: str,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Search chat history for relevant messages."""
        try:
            response = self.db.supabase.table("chat_messages") \
                .select("*") \
                .eq("user_id", user_id) \
                .ilike("message", f"%{query}%") \
                .order("created_at", desc=True) \
                .limit(limit) \
                .execute()

            return response.data or []
        except Exception as e:
            logger.error(f"Chat search failed: {e}")
            return []
