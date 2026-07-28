"""
Sentiment Analysis Service - NLP pipeline for social media and news sentiment.
Architecture Doc §26.1: FinBERT/VADER, on-chain metrics, rolling window aggregation.
"""

import logging
import json
import math
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from collections import defaultdict
import os

logger = logging.getLogger(__name__)


class SentimentSource:
    TWITTER = "twitter"
    REDDIT = "reddit"
    TELEGRAM = "telegram"
    NEWS = "news"
    ON_CHAIN = "on_chain"


class SentimentLabel:
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"


class SentimentAnalysisService:
    """
    Processes social media and news sentiment for crypto assets.
    Architecture Doc §26.1: NLP pipeline with FinBERT (primary) and VADER (fallback).
    """

    def __init__(self, db):
        self.db = db
        self._price_history: Dict[str, List[float]] = defaultdict(list)
        self._aggregated_sentiment: Dict[str, Dict[str, float]] = {}

    async def analyze_text(self, text: str, source: str = "unknown") -> Dict[str, Any]:
        """Analyze sentiment of a single text."""
        try:
            from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
            analyzer = SentimentIntensityAnalyzer()
            scores = analyzer.polarity_scores(text)
            compound = scores["compound"]

            if compound >= 0.05:
                label = SentimentLabel.BULLISH
            elif compound <= -0.05:
                label = SentimentLabel.BEARISH
            else:
                label = SentimentLabel.NEUTRAL

            return {
                "success": True,
                "label": label,
                "score": compound,
                "confidence": abs(compound),
                "source": source,
                "analyzed_at": datetime.utcnow().isoformat(),
            }
        except ImportError:
            return self._mock_analyze(text, source)

    def _mock_analyze(self, text: str, source: str) -> Dict[str, Any]:
        """Fallback mock analysis when VADER not installed."""
        text_lower = text.lower()
        bullish_words = {"moon", "bull", "pump", "buy", "long", "bullish", "breakout", "surge", "rally"}
        bearish_words = {"dump", "crash", "bear", "sell", "short", "bearish", "drop", "plunge", "fear"}

        bullish_count = sum(1 for w in bullish_words if w in text_lower)
        bearish_count = sum(1 for w in bearish_words if w in text_lower)

        total = bullish_count + bearish_count
        if total == 0:
            return {"success": True, "label": SentimentLabel.NEUTRAL, "score": 0, "confidence": 0, "source": source, "analyzed_at": datetime.utcnow().isoformat()}

        score = (bullish_count - bearish_count) / total
        label = SentimentLabel.BULLISH if score > 0.2 else SentimentLabel.BEARISH if score < -0.2 else SentimentLabel.NEUTRAL

        return {"success": True, "label": label, "score": score, "confidence": abs(score), "source": source, "analyzed_at": datetime.utcnow().isoformat()}

    async def ingest_social_data(
        self, ticker: str, source: str, items: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Ingest and analyze social media data for a ticker."""
        analyzed = []
        for item in items:
            text = item.get("text", "")
            result = await self.analyze_text(text, source)
            analyzed.append({**item, "sentiment": result})

        avg_score = 0
        if analyzed:
            scores = [a["sentiment"]["score"] for a in analyzed if a["sentiment"].get("score") is not None]
            avg_score = sum(scores) / len(scores) if scores else 0

        try:
            self.db.supabase.table("sentiment_data").insert({
                "ticker": ticker,
                "social_sentiment": avg_score,
                "data_source": source,
                "collected_at": datetime.utcnow().isoformat(),
            }).execute()
        except Exception as e:
            logger.error(f"Failed to store sentiment: {e}")

        return {
            "success": True,
            "ticker": ticker,
            "source": source,
            "items_analyzed": len(analyzed),
            "average_score": round(avg_score, 4),
            "label": SentimentLabel.BULLISH if avg_score > 0.05 else SentimentLabel.BEARISH if avg_score < -0.05 else SentimentLabel.NEUTRAL,
            "analyzed_at": datetime.utcnow().isoformat(),
        }

    async def get_aggregated_sentiment(
        self, ticker: str, windows: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Get aggregated sentiment across rolling windows (1h, 4h, 24h)."""
        if windows is None:
            windows = ["1h", "4h", "24h"]

        window_map = {"1h": 1, "4h": 4, "24h": 24}
        result = {"ticker": ticker, "windows": {}}

        for window in windows:
            hours = window_map.get(window, 1)
            cutoff = datetime.utcnow() - timedelta(hours=hours)

            try:
                response = (
                    self.db.supabase.table("sentiment_data")
                    .select("*")
                    .eq("ticker", ticker)
                    .gte("collected_at", cutoff.isoformat())
                    .order("collected_at", desc=True)
                    .execute()
                )
                data = response.data or []
                if data:
                    scores = [d.get("social_sentiment", 0) for d in data if d.get("social_sentiment") is not None]
                    avg = sum(scores) / len(scores) if scores else 0
                else:
                    avg = 0

                result["windows"][window] = {
                    "average_score": round(avg, 4),
                    "label": SentimentLabel.BULLISH if avg > 0.05 else SentimentLabel.BEARISH if avg < -0.05 else SentimentLabel.NEUTRAL,
                    "data_points": len(data),
                }
            except Exception as e:
                logger.error(f"Failed to get aggregated sentiment: {e}")
                result["windows"][window] = {"average_score": 0, "label": SentimentLabel.NEUTRAL, "data_points": 0}

        return result

    async def get_onchain_metrics(self, ticker: str) -> Dict[str, Any]:
        """
        Get on-chain metrics per architecture doc §26.1:
        exchange inflows/outflows, whale movements, stablecoin supply.
        """
        try:
            response = (
                self.db.supabase.table("onchain_metrics")
                .select("*")
                .eq("asset", ticker)
                .order("timestamp", desc=True)
                .limit(1)
                .execute()
            )
            if response.data:
                return {"success": True, "metrics": response.data[0]}

            flows_response = (
                self.db.supabase.table("onchain_exchange_flows")
                .select("*")
                .eq("asset", ticker)
                .order("timestamp", desc=True)
                .limit(1)
                .execute()
            )

            metrics = {
                "asset": ticker,
                "exchange_inflow": 0,
                "exchange_outflow": 0,
                "net_flow": 0,
                "whale_movements": [],
            }
            if flows_response.data:
                flow = flows_response.data[0]
                metrics["exchange_inflow"] = float(flow.get("exchange_inflow", 0))
                metrics["exchange_outflow"] = float(flow.get("exchange_outflow", 0))
                metrics["net_flow"] = float(flow.get("net_flow", 0))

            return {"success": True, "metrics": metrics}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def generate_sentiment_signal(
        self, ticker: str
    ) -> Dict[str, Any]:
        """Generate a sentiment-based signal for a ticker."""
        aggregated = await self.get_aggregated_sentiment(ticker, ["1h", "4h", "24h"])
        onchain = await self.get_onchain_metrics(ticker)

        short_term = aggregated.get("windows", {}).get("1h", {}).get("average_score", 0)
        medium_term = aggregated.get("windows", {}).get("4h", {}).get("average_score", 0)
        long_term = aggregated.get("windows", {}).get("24h", {}).get("average_score", 0)

        weighted = short_term * 0.5 + medium_term * 0.35 + long_term * 0.15

        flow_signal = 0
        if onchain.get("success"):
            net_flow = onchain["metrics"].get("net_flow", 0)
            flow_signal = -0.2 if net_flow > 0 else 0.1

        combined = weighted + flow_signal
        confidence = min(abs(combined), 1.0)

        if combined > 0.1:
            signal_type = "BUY"
        elif combined < -0.1:
            signal_type = "SELL"
        else:
            signal_type = "HOLD"

        return {
            "success": True,
            "ticker": ticker,
            "signal_type": signal_type,
            "confidence": round(confidence, 4),
            "sentiment_score": round(combined, 4),
            "components": {
                "short_term": round(short_term, 4),
                "medium_term": round(medium_term, 4),
                "long_term": round(long_term, 4),
                "onchain_flow": round(flow_signal, 4),
            },
            "generated_at": datetime.utcnow().isoformat(),
        }
