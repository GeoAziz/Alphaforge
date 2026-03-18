"""CoinGecko data source integration."""

import logging
import httpx
import os
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

from .base_source import BaseDataSource


class CoinGeckoDataSource(BaseDataSource):
    """Fetches market data from CoinGecko API."""
    
    def __init__(self):
        super().__init__("CoinGecko")
        self.base_url = "https://api.coingecko.com/api/v3"
        self.client = httpx.AsyncClient(timeout=10.0)
        # CoinGecko free tier: 10-50 calls/minute
        self.rate_limit_remaining = 50
    
    async def fetch_ticker(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Fetch single ticker from CoinGecko."""
        try:
            # Map common symbols to CoinGecko IDs
            coin_id = self._symbol_to_coin_id(symbol)
            if not coin_id:
                return None
            
            url = f"{self.base_url}/simple/price"
            params = {
                "ids": coin_id,
                "vs_currencies": "usd",
                "include_market_cap": "true",
                "include_24hr_vol": "true",
                "include_24hr_change": "true",
                "include_last_updated_at": "true"
            }
            
            response = await self.client.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                
                if coin_id in data:
                    coin_data = data[coin_id]
                    self.mark_available()
                    
                    return {
                        "symbol": symbol,
                        "price": coin_data.get("usd", 0),
                        "change_24h": None,  # CoinGecko doesn't provide absolute change
                        "change_24h_pct": coin_data.get("usd_24h_change", 0),
                        "volume_24h": coin_data.get("usd_24h_vol", 0),
                        "market_cap": coin_data.get("usd_market_cap", 0),
                        "bid_price": coin_data.get("usd", 0) * 0.999,
                        "ask_price": coin_data.get("usd", 0) * 1.001,
                        "timestamp": datetime.utcnow(),
                        "source": "coingecko"
                    }
            
            logger.warning(f"⚠️ CoinGecko ticker fetch failed for {symbol}: {response.status_code}")
            return None
        
        except Exception as e:
            self.mark_error(str(e))
            logger.error(f"❌ CoinGecko ticker error for {symbol}: {e}")
            return None
    
    async def fetch_tickers(self, symbols: List[str]) -> List[Dict[str, Any]]:
        """Fetch multiple tickers efficiently from CoinGecko (batch)."""
        try:
            # Map all symbols to CoinGecko IDs
            coin_ids = [self._symbol_to_coin_id(s) for s in symbols]
            coin_ids = [c for c in coin_ids if c]  # Remove None values
            
            if not coin_ids:
                return []
            
            url = f"{self.base_url}/simple/price"
            params = {
                "ids": ",".join(coin_ids),
                "vs_currencies": "usd",
                "include_market_cap": "true",
                "include_24hr_vol": "true",
                "include_24hr_change": "true"
            }
            
            response = await self.client.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                tickers = []
                
                for i, symbol in enumerate(symbols):
                    coin_id = coin_ids[i] if i < len(coin_ids) else None
                    if coin_id and coin_id in data:
                        coin_data = data[coin_id]
                        tickers.append({
                            "symbol": symbol,
                            "price": coin_data.get("usd", 0),
                            "change_24h": None,
                            "change_24h_pct": coin_data.get("usd_24h_change", 0),
                            "volume_24h": coin_data.get("usd_24h_vol", 0),
                            "market_cap": coin_data.get("usd_market_cap", 0),
                            "bid_price": coin_data.get("usd", 0) * 0.999,
                            "ask_price": coin_data.get("usd", 0) * 1.001,
                            "timestamp": datetime.utcnow(),
                            "source": "coingecko"
                        })
                
                self.mark_available()
                return tickers
            
            return []
        
        except Exception as e:
            self.mark_error(str(e))
            logger.error(f"❌ CoinGecko batch fetch error: {e}")
            return []
    
    async def fetch_ohlcv(self, symbol: str, interval: str = "1d", limit: int = 7) -> Optional[List[Dict[str, Any]]]:
        """
        Fetch historical OHLCV data from CoinGecko.
        Note: CoinGecko free tier only provides daily data.
        """
        try:
            coin_id = self._symbol_to_coin_id(symbol)
            if not coin_id:
                return None
            
            # CoinGecko API: /coins/{id}/ohlc?vs_currency=usd&days={days}
            url = f"{self.base_url}/coins/{coin_id}/ohlc"
            params = {
                "vs_currency": "usd",
                "days": limit
            }
            
            response = await self.client.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                candles = []
                
                for ohlc in data:
                    candles.append({
                        "timestamp": datetime.fromtimestamp(ohlc[0] / 1000),
                        "open": ohlc[1],
                        "high": ohlc[2],
                        "low": ohlc[3],
                        "close": ohlc[4],
                        "volume": None  # Not provided by CoinGecko OHLC
                    })
                
                self.mark_available()
                return candles
            
            return None
        
        except Exception as e:
            logger.error(f"❌ CoinGecko OHLCV error: {e}")
            return None
    
    async def fetch_sentiment(self) -> Optional[Dict[str, Any]]:
        """
        Fetch global crypto market sentiment from CoinGecko.
        """
        try:
            url = f"{self.base_url}/global"
            response = await self.client.get(url)
            
            if response.status_code == 200:
                data = response.json()
                
                # Extract market data
                market_data = data.get("data", {})
                btc_dominance = market_data.get("btc_market_cap_percentage", {}).get("btc", 50)
                eth_dominance = market_data.get("btc_market_cap_percentage", {}).get("eth", 20)
                
                # Calculate sentiment (simplified)
                # Higher BTC dominance = more conservative/risk-off
                sentiment_score = 50 + (btc_dominance - 50) * -0.5
                
                self.mark_available()
                return {
                    "fear_greed_index": sentiment_score,
                    "btc_dominance": btc_dominance,
                    "eth_dominance": eth_dominance,
                    "timestamp": datetime.utcnow(),
                    "source": "coingecko"
                }
            
            return None
        
        except Exception as e:
            logger.error(f"❌ CoinGecko sentiment error: {e}")
            return None
    
    async def is_rate_limited(self) -> bool:
        """CoinGecko free tier: 10-50 calls/minute."""
        return False  # Typically not rate limited on free tier
    
    def _symbol_to_coin_id(self, symbol: str) -> Optional[str]:
        """Map trading symbol to CoinGecko coin ID."""
        # Common mappings
        mapping = {
            "BTC": "bitcoin",
            "ETH": "ethereum",
            "SOL": "solana",
            "BNB": "binancecoin",
            "XRP": "ripple",
            "ADA": "cardano",
            "DOGE": "dogecoin",
            "AVAX": "avalanche-2",
            "DOT": "polkadot",
            "MATIC": "matic-network",
            "LINK": "chainlink",
            "ATOM": "cosmos",
            "NEAR": "near",
            "ARBITRUM": "arbitrum",
            "OP": "optimism"
        }
        
        symbol_clean = symbol.replace("USDT", "").upper()
        return mapping.get(symbol_clean)
    
    async def close(self):
        """Clean up HTTP client."""
        await self.client.aclose()
