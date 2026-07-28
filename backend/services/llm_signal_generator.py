"""
LLM-powered AI signal generation using OpenAI, Anthropic, or Google Genkit.
Generates high-quality trading signals with explainability.
"""

import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime
from config import LLMConfig, DevelopmentConfig

logger = logging.getLogger(__name__)


class LLMSignalGenerator:
    """Generate trading signals using LLM AI."""

    def __init__(self):
        self.provider = LLMConfig.PROVIDER
        self.enabled = LLMConfig.ENABLED
        self.client = None
        self._initialize_client()

    def _initialize_client(self):
        """Initialize LLM provider client."""
        if not self.enabled:
            logger.warning("LLM signal generation disabled")
            return

        try:
            if self.provider == "openai":
                import openai
                openai.api_key = LLMConfig.OPENAI_API_KEY
                self.client = openai
                logger.info("✅ OpenAI LLM client initialized")

            elif self.provider == "anthropic":
                import anthropic
                self.client = anthropic.Anthropic(api_key=LLMConfig.ANTHROPIC_API_KEY)
                logger.info("✅ Anthropic Claude LLM client initialized")

            elif self.provider == "google":
                import google.generativeai as genai
                genai.configure(api_key=LLMConfig.GOOGLE_GENKIT_API_KEY)
                self.client = genai
                logger.info("✅ Google Genkit LLM client initialized")

            else:
                logger.error(f"Unknown LLM provider: {self.provider}")
                self.client = None

        except Exception as e:
            logger.error(f"❌ LLM client initialization failed: {e}")
            self.client = None

    async def generate_signal(
        self,
        ticker: str,
        market_data: Dict[str, Any],
        technical_indicators: Dict[str, Any],
        sentiment_data: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Generate AI trading signal using LLM.

        Args:
            ticker: Asset ticker (e.g., BTCUSDT)
            market_data: Current price, volume, etc.
            technical_indicators: RSI, MACD, Bollinger Bands, etc.
            sentiment_data: Market sentiment scores

        Returns:
            Signal dict with type, entry, exit, confidence, drivers
        """
        if not self.enabled or not self.client:
            return None

        if DevelopmentConfig.MOCK_LLM:
            return self._generate_mock_signal(ticker, market_data)

        try:
            # Build context prompt
            prompt = self._build_prompt(
                ticker, market_data, technical_indicators, sentiment_data
            )

            # Call LLM
            if self.provider == "openai":
                response = await self._call_openai(prompt)
            elif self.provider == "anthropic":
                response = await self._call_anthropic(prompt)
            elif self.provider == "google":
                response = await self._call_google(prompt)
            else:
                return None

            # Parse response
            signal = self._parse_response(response, ticker)
            logger.info(f"📊 Generated LLM signal for {ticker}: {signal}")
            return signal

        except Exception as e:
            logger.error(f"❌ LLM signal generation failed for {ticker}: {e}")
            return None

    async def _call_openai(self, prompt: str) -> str:
        """Call OpenAI API."""
        response = self.client.ChatCompletion.create(
            model=LLMConfig.MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=LLMConfig.TEMPERATURE,
            max_tokens=LLMConfig.MAX_TOKENS,
        )
        return response.choices[0].message.content

    async def _call_anthropic(self, prompt: str) -> str:
        """Call Anthropic Claude API."""
        message = self.client.messages.create(
            model=LLMConfig.MODEL,
            max_tokens=LLMConfig.MAX_TOKENS,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text

    async def _call_google(self, prompt: str) -> str:
        """Call Google Genkit API."""
        model = self.client.GenerativeModel(LLMConfig.MODEL)
        response = model.generate_content(prompt)
        return response.text

    def _build_prompt(
        self,
        ticker: str,
        market_data: Dict[str, Any],
        technical_indicators: Dict[str, Any],
        sentiment_data: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Build LLM prompt with chain-of-thought reasoning."""
        sentiment_block = ""
        if sentiment_data:
            sentiment_block = f"""
SENTIMENT DATA:
- Social Sentiment: {sentiment_data.get('social_sentiment', 'N/A')}
- Fear/Greed Index: {sentiment_data.get('fear_greed_index', 'N/A')}
- News Sentiment: {sentiment_data.get('news_sentiment', 'N/A')}
"""

        return f"""You are an elite algorithmic trading signal generator at AlphaForge. Analyze the following market data using chain-of-thought reasoning before generating a signal.

ASSET: {ticker}

MARKET DATA:
- Current Price: ${market_data.get("price", 0):.2f}
- 24h Change: {market_data.get("change_24h", 0):.2f}%
- 24h Volume: {market_data.get("volume", 0):,.0f}
- 24h High: ${market_data.get("high_24h", 0):.2f}
- 24h Low: ${market_data.get("low_24h", 0):.2f}

TECHNICAL INDICATORS:
- RSI (14): {technical_indicators.get("rsi", 50):.2f}
- MACD Line: {technical_indicators.get("macd", 0):.4f}
- MACD Signal: {technical_indicators.get("macd_signal", 0):.4f}
- MACD Histogram: {technical_indicators.get("macd_histogram", 0):.4f}
- Bollinger Upper: ${technical_indicators.get("bb_upper", 0):.2f}
- Bollinger Middle: ${technical_indicators.get("bb_middle", 0):.2f}
- Bollinger Lower: ${technical_indicators.get("bb_lower", 0):.2f}
- EMA (20): ${technical_indicators.get("ema_20", 0):.2f}
- EMA (50): ${technical_indicators.get("ema_50", 0):.2f}
- EMA (200): ${technical_indicators.get("ema_200", 0):.2f}
- Volume MA (20): {technical_indicators.get("vol_ma_20", 0):,.0f}
- ATR (14): {technical_indicators.get("atr", 0):.2f}
{sentiment_block}
MARKET REGIME CONTEXT:
- Is the market trending or ranging?
- Are we near key support/resistance levels?
- What is the volatility regime?

INSTRUCTIONS:
Think step-by-step:
1. Analyze the trend direction and strength
2. Evaluate momentum indicators (RSI, MACD)
3. Assess volatility (Bollinger Bands, ATR)
4. Consider volume confirmation
5. Factor in sentiment if available
6. Determine market regime (trending/ranging/volatile)
7. Calculate risk-reward based on ATR

Then generate a JSON signal with:
1. signal_type: "BUY", "SELL", or "HOLD"
2. confidence: 0.5-0.95 (based on multi-factor alignment)
3. entry_price: Suggested entry (current price or limit)
4. stop_loss: Based on ATR (1.5x ATR from entry)
5. take_profit: Based on ATR (3x ATR from entry for 2:1 R:R minimum)
6. risk_reward_ratio: Calculated R:R
7. drivers: List of 3-5 specific technical reasons
8. timeframe: "1h", "4h", or "1d"
9. risk_level: "low", "medium", or "high"
10. market_regime: "trending", "ranging", or "volatile"

Return ONLY valid JSON, no markdown or explanations outside the JSON.
"""

    def _parse_response(self, response: str, ticker: str) -> Optional[Dict[str, Any]]:
        """Parse LLM response and extract signal."""
        try:
            # Extract JSON from response (may contain markdown)
            json_start = response.find("{")
            json_end = response.rfind("}") + 1
            if json_start == -1 or json_end == 0:
                return None

            json_str = response[json_start:json_end]
            signal_data = json.loads(json_str)

            # Validate and enrich
            return {
                "ticker": ticker,
                "signal_type": signal_data.get("signal_type", "HOLD"),
                "confidence": float(signal_data.get("confidence", 0.5)),
                "entry_price": float(signal_data.get("entry_price", 0)),
                "stop_loss": float(signal_data.get("stop_loss", 0)),
                "take_profit": float(signal_data.get("take_profit", 0)),
                "risk_reward_ratio": float(signal_data.get("risk_reward_ratio", 1.0)),
                "drivers": signal_data.get("drivers", []),
                "timeframe": signal_data.get("timeframe", "1h"),
                "risk_level": signal_data.get("risk_level", "medium"),
                "source": f"llm_{self.provider}",
                "generated_at": datetime.utcnow().isoformat(),
            }

        except (json.JSONDecodeError, ValueError, KeyError) as e:
            logger.error(f"Failed to parse LLM response for {ticker}: {e}")
            return None

    def _generate_mock_signal(
        self, ticker: str, market_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate mock signal using technical analysis heuristics."""
        price = float(market_data.get("price", 0))
        change = float(market_data.get("change_24h", 0))
        volume = float(market_data.get("volume", 0))

        # Multi-factor scoring
        momentum_score = max(-1, min(1, change / 10))  # Normalize to [-1, 1]
        volume_signal = 1.2 if volume > 1_000_000 else 0.8  # High volume confirmation

        # Simulate RSI from price change
        simulated_rsi = 50 + (change * 3)
        simulated_rsi = max(10, min(90, simulated_rsi))

        # Determine signal based on multiple factors
        if simulated_rsi < 30 and momentum_score < -0.3:
            signal_type = "BUY"
            confidence = min(0.92, 0.65 + abs(momentum_score) * 0.2 * volume_signal)
            drivers = [
                f"RSI oversold at {simulated_rsi:.0f}",
                f"Negative momentum ({change:+.1f}%) with potential reversal",
                "Volume accumulation at support",
            ]
        elif simulated_rsi > 70 and momentum_score > 0.3:
            signal_type = "SELL"
            confidence = min(0.92, 0.65 + abs(momentum_score) * 0.2 * volume_signal)
            drivers = [
                f"RSI overbought at {simulated_rsi:.0f}",
                f"Positive momentum ({change:+.1f}%) at resistance",
                "Distribution volume detected",
            ]
        elif abs(momentum_score) < 0.1:
            signal_type = "HOLD"
            confidence = 0.45
            drivers = [
                "Low volatility consolidation",
                "No clear directional bias",
            ]
        else:
            signal_type = "BUY" if momentum_score > 0 else "SELL"
            confidence = min(0.75, 0.55 + abs(momentum_score) * 0.15)
            drivers = [
                f"Moderate {'bullish' if signal_type == 'BUY' else 'bearish'} momentum",
                f"Price change: {change:+.1f}%",
            ]

        # Calculate stop loss and take profit based on ATR-like estimate
        atr_estimate = price * 0.02  # ~2% daily range estimate
        if signal_type == "BUY":
            stop_loss = price - (atr_estimate * 1.5)
            take_profit = price + (atr_estimate * 3.0)
        elif signal_type == "SELL":
            stop_loss = price + (atr_estimate * 1.5)
            take_profit = price - (atr_estimate * 3.0)
        else:
            stop_loss = price * 0.97
            take_profit = price * 1.03

        risk_reward = abs(take_profit - price) / max(abs(price - stop_loss), 0.01)

        return {
            "ticker": ticker,
            "signal_type": signal_type,
            "confidence": round(confidence, 3),
            "entry_price": price,
            "stop_loss": round(stop_loss, 2),
            "take_profit": round(take_profit, 2),
            "risk_reward_ratio": round(risk_reward, 2),
            "drivers": drivers,
            "timeframe": "1h",
            "risk_level": "low" if confidence > 0.8 else "medium" if confidence > 0.6 else "high",
            "source": "llm_mock",
            "generated_at": datetime.utcnow().isoformat(),
        }

    async def close(self):
        """Cleanup resources."""
        self.client = None
        logger.info("🔌 LLM signal generator closed")
