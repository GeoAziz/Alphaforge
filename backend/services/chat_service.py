"""
Chat & LLM Service - Handles AI-powered chat and insights.
Integrates with LLM backend for streaming responses.
"""

import logging
from datetime import datetime
from typing import List, Dict, Any, AsyncGenerator, Optional
import json

logger = logging.getLogger(__name__)


class ChatService:
    """Manages user chat interactions and LLM responses."""
    
    def __init__(self, db):
        self.db = db
        self.context_limit = 20  # Max previous messages for context
    
    async def save_message(
        self,
        user_id: str,
        message: str,
        role: str = "user"
    ) -> Dict[str, Any]:
        """Save a chat message to database."""
        try:
            msg_data = {
                "user_id": user_id,
                "message": message,
                "role": role,
                "created_at": datetime.utcnow().isoformat()
            }
            
            response = self.db.supabase.table("chat_messages").insert(msg_data).execute()
            
            if response.data:
                logger.info(f"✅ Chat message saved for {user_id}")
                return {"success": True, "message_id": response.data[0]["id"]}
            
        except Exception as e:
            logger.error(f"❌ Failed to save chat message: {e}")
        
        return {"success": False, "error": str(e)}
    
    async def get_chat_history(
        self,
        user_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Retrieve chat history for a user."""
        try:
            response = self.db.supabase.table("chat_messages")\
                .select("*")\
                .eq("user_id", user_id)\
                .order("created_at", desc=False)\
                .limit(limit)\
                .execute()
            
            messages = response.data or []
            logger.info(f"✅ Fetched {len(messages)} chat messages for {user_id}")
            
            return messages
        
        except Exception as e:
            logger.error(f"❌ Failed to fetch chat history: {e}")
            return []
    
    async def get_context_for_response(
        self,
        user_id: str,
        portfolio_service,
        signal_processor
    ) -> Dict[str, Any]:
        """Build context information for AI response."""
        try:
            context = {}
            
            # Get user portfolio summary
            portfolio = await portfolio_service.get_portfolio_summary(user_id)
            context["portfolio"] = portfolio
            
            # Get active signals
            signals_response = self.db.supabase.table("signals")\
                .select("*")\
                .order("created_at", desc=True)\
                .limit(5)\
                .execute()
            
            context["active_signals"] = signals_response.data or []
            
            # Get open positions
            positions_response = self.db.supabase.table("positions")\
                .select("*")\
                .eq("user_id", user_id)\
                .execute()
            
            context["open_positions"] = positions_response.data or []
            
            return context
        
        except Exception as e:
            logger.error(f"❌ Failed to build context: {e}")
            return {}
    
    async def generate_response(
        self,
        user_id: str,
        message: str,
        context: Dict[str, Any]
    ) -> AsyncGenerator[str, None]:
        """
        Generate AI response (placeholder for LLM integration).
        In production, this would call Anthropic Claude or similar.
        """
        
        # For MVP, generate intelligent responses based on message keywords
        message_lower = message.lower()
        
        # Save user message
        await self.save_message(user_id, message, "user")
        
        # Generate response based on context
        response_text = await self._generate_ai_response(message, context)
        
        # Save AI response
        await self.save_message(user_id, response_text, "assistant")
        
        # Yield response for streaming
        yield response_text
    
    async def _generate_ai_response(
        self,
        message: str,
        context: Dict[str, Any]
    ) -> str:
        """Generate contextual AI response."""
        
        message_lower = message.lower()
        portfolio = context.get("portfolio", {})
        open_positions = context.get("open_positions", [])
        signals = context.get("active_signals", [])
        
        # Response templates based on detected intent
        
        if any(word in message_lower for word in ["portfolio", "balance", "equity"]):
            total_equity = portfolio.get("total_equity", 100000)
            pnl = portfolio.get("total_pnl", 0)
            pnl_pct = portfolio.get("pnl_percent", 0)
            
            return (
                f"Your portfolio currently has ${total_equity:,.2f} in total equity. "
                f"Your total P&L is ${pnl:,.2f} ({pnl_pct:.2f}%). "
                f"You have {len(open_positions)} open positions. "
                f"Your risk exposure appears {'high' if abs(pnl_pct) > 20 else 'moderate' if abs(pnl_pct) > 10 else 'low'}."
            )
        
        elif any(word in message_lower for word in ["signal", "trade", "recommendation"]):
            if signals:
                top_signal = signals[0]
                ticker = top_signal.get("ticker", "BTC")
                signal_type = top_signal.get("signal_type", "HOLD")
                confidence = top_signal.get("confidence", 0.5)
                
                return (
                    f"I've identified a high-confidence {signal_type} signal for {ticker} "
                    f"with {confidence:.0%} confidence. The technical indicators suggest "
                    f"recent momentum, but ensure your position sizing aligns with risk limits. "
                    f"Consider waiting for confirmation on a lower timeframe."
                )
            else:
                return (
                    "Currently, I'm not detecting any new high-confidence signals. "
                    "Market conditions appear neutral. I'll continue monitoring "
                    "key support/resistance levels."
                )
        
        elif any(word in message_lower for word in ["risk", "volatility", "drawdown"]):
            max_drawdown = portfolio.get("max_drawdown", 0)
            return (
                f"Your current risk profile shows a maximum drawdown of {abs(max_drawdown):.2%}. "
                f"I recommend maintaining current position sizes and considering "
                f"hedging strategies if volatility increases further."
            )
        
        elif any(word in message_lower for word in ["performance", "win rate", "sharpe"]):
            sharpe = portfolio.get("sharpe_ratio", 0)
            win_pct = portfolio.get("win_rate", 0)
            
            return (
                f"Your performance metrics show a Sharpe ratio of {sharpe:.2f} "
                f"and a win rate of {win_pct:.1%}. This indicates "
                f"{'strong risk-adjusted returns' if sharpe > 1 else 'moderate performance' if sharpe > 0.5 else 'need for strategy improvement'}. "
                f"Continue analyzing factors driving profitable vs. losing trades."
            )
        
        elif any(word in message_lower for word in ["market", "sentiment", "trend"]):
            return (
                "Market sentiment is currently neutral with mild bullish bias. "
                "Bitcoin dominance is stable, and altcoins are showing mixed signals. "
                "I'd focus on high-conviction setups with clear risk/reward ratios."
            )
        
        else:
            return (
                "I can help you with analysis on your portfolio performance, "
                "market signals and trading recommendations, risk assessment, or strategy insights. "
                "What would you like to explore?"
            )
