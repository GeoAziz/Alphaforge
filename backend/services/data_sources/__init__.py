"""Data sources module for fetching market data from multiple providers."""

from .base_source import BaseDataSource
from .binance_source import BinanceDataSource
from .coingecko_source import CoinGeckoDataSource
from .polygon_source import PolygonDataSource
from .source_orchestrator import DataSourceOrchestrator
from .exchange_adapters import BybitDataSource, OKXDataSource, BitgetDataSource
from .bybit_source import BybitExchange
from .okx_source import OKXExchange
from .bitget_source import BitgetExchange

__all__ = [
    "BaseDataSource",
    "BinanceDataSource",
    "CoinGeckoDataSource",
    "PolygonDataSource",
    "DataSourceOrchestrator",
    "BybitDataSource",
    "OKXDataSource",
    "BitgetDataSource",
    "BybitExchange",
    "OKXExchange",
    "BitgetExchange",
]
