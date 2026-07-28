"""
Onchain Smart Money Tracker - Public dashboard showing whale movements,
liquidation heatmaps, MVRV/SOPR metrics, and exchange flows.
"""

import logging
import math
import random
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

ASSET_CONFIGS = {
    "BTC": {"name": "Bitcoin", "whale_threshold": 100, "avg_price": 67500},
    "ETH": {"name": "Ethereum", "whale_threshold": 1000, "avg_price": 3500},
    "SOL": {"name": "Solana", "whale_threshold": 10000, "avg_price": 170},
    "BNB": {"name": "BNB", "whale_threshold": 500, "avg_price": 600},
    "XRP": {"name": "XRP", "whale_threshold": 100000, "avg_price": 0.62},
}


def _generate_mock_whales(limit: int = 20) -> List[Dict[str, Any]]:
    """Generate mock whale movement data for demo/development."""
    now = datetime.utcnow()
    movements = []

    for i in range(min(limit, 30)):
        asset = random.choice(list(ASSET_CONFIGS.keys()))
        config = ASSET_CONFIGS[asset]
        amount = random.uniform(config["whale_threshold"], config["whale_threshold"] * 10)
        value_usd = amount * config["avg_price"]

        movements.append({
            "id": f"whale-{i+1}",
            "asset": asset,
            "amount": round(amount, 4),
            "value_usd": round(value_usd, 2),
            "from_address": f"0x{random.randint(10**38, 10**39-1):040x}",
            "to_address": f"0x{random.randint(10**38, 10**39-1):040x}",
            "movement_type": random.choice(["exchange_deposit", "exchange_withdrawal", "cold_storage", "otc"]),
            "timestamp": (now - timedelta(minutes=random.randint(5, 720))).isoformat(),
        })

    movements.sort(key=lambda x: x["timestamp"], reverse=True)
    return movements


def _generate_mock_metrics(asset: str) -> Dict[str, Any]:
    """Generate mock on-chain metrics for a given asset."""
    base_price = ASSET_CONFIGS.get(asset, {}).get("avg_price", 50000)

    mvrv = round(random.uniform(0.8, 2.5), 2)
    sopr = round(random.uniform(0.95, 1.08), 4)
    nvt = round(random.uniform(15, 80), 1)
    active_addresses = random.randint(200000, 900000)
    exchange_balance_change = round(random.uniform(-5, 5), 2)
    miner_revenue = random.randint(1000000, 5000000)

    mvrv_label = "Undervalued"
    if mvrv > 1.5:
        mvrv_label = "Overvalued"
    elif mvrv > 1.2:
        mvrv_label = "Fair Value"

    sopr_label = "Profit-taking"
    if sopr < 1.0:
        sopr_label = "Accumulation"

    return {
        "asset": asset,
        "price": base_price,
        "mvrv": mvrv,
        "mvrv_label": mvrv_label,
        "sopr": sopr,
        "sopr_label": sopr_label,
        "nvt_ratio": nvt,
        "active_addresses_24h": active_addresses,
        "exchange_balance_change_pct_24h": exchange_balance_change,
        "miner_revenue_usd": miner_revenue,
        "realized_cap": round(base_price * random.uniform(15_000_000, 20_000_000), 0),
        "market_cap": round(base_price * random.uniform(18_000_000, 21_000_000), 0),
        "timestamp": datetime.utcnow().isoformat(),
    }


def _generate_mock_exchange_flows() -> List[Dict[str, Any]]:
    """Generate mock exchange inflow/outflow data."""
    now = datetime.utcnow()
    flows = []

    for asset in ["BTC", "ETH", "SOL", "BNB"]:
        config = ASSET_CONFIGS[asset]
        for hour_offset in range(24):
            ts = now - timedelta(hours=hour_offset)
            inflow = round(random.uniform(10, config["whale_threshold"] * 5), 4)
            outflow = round(random.uniform(10, config["whale_threshold"] * 5), 4)

            flows.append({
                "asset": asset,
                "timestamp": ts.isoformat(),
                "exchange_inflow": inflow,
                "exchange_outflow": outflow,
                "net_flow": round(outflow - inflow, 4),
                "inflow_value_usd": round(inflow * config["avg_price"], 2),
                "outflow_value_usd": round(outflow * config["avg_price"], 2),
            })

    flows.sort(key=lambda x: x["timestamp"], reverse=True)
    return flows


class OnchainTrackerService:
    """Public on-chain data dashboard service."""

    def __init__(self, db=None, use_mock: bool = True):
        self.db = db
        self.use_mock = use_mock

    async def get_whale_movements(
        self,
        asset: Optional[str] = None,
        limit: int = 20,
    ) -> Dict[str, Any]:
        """Get recent whale movements."""
        try:
            if self.use_mock:
                movements = _generate_mock_whales(limit)
                if asset:
                    movements = [m for m in movements if m["asset"] == asset.upper()]
                return {
                    "success": True,
                    "movements": movements,
                    "count": len(movements),
                    "source": "mock",
                }

            query = self.db.supabase.table("onchain_whale_movements").select("*")
            if asset:
                query = query.eq("asset", asset.upper())
            response = query.order("timestamp", desc=True).limit(limit).execute()
            movements = response.data or []

            return {
                "success": True,
                "movements": movements,
                "count": len(movements),
                "source": "database",
            }
        except Exception as e:
            logger.error(f"Failed to get whale movements: {e}")
            return {"success": False, "error": str(e), "movements": [], "count": 0}

    async def get_asset_metrics(
        self,
        asset: str,
    ) -> Dict[str, Any]:
        """Get on-chain metrics for a specific asset (SOPR, MVRV, NVT, etc.)."""
        try:
            asset = asset.upper()
            if asset not in ASSET_CONFIGS:
                return {"success": False, "error": f"Unsupported asset: {asset}"}

            if self.use_mock:
                metrics = _generate_mock_metrics(asset)
                return {"success": True, "metrics": metrics, "source": "mock"}

            response = (
                self.db.supabase.table("onchain_metrics")
                .select("*")
                .eq("asset", asset)
                .order("timestamp", desc=True)
                .limit(1)
                .execute()
            )

            if response.data:
                return {"success": True, "metrics": response.data[0], "source": "database"}
            return {"success": False, "error": "No metrics found", "metrics": {}}
        except Exception as e:
            logger.error(f"Failed to get asset metrics: {e}")
            return {"success": False, "error": str(e)}

    async def get_exchange_flows(
        self,
        asset: Optional[str] = None,
        hours: int = 24,
    ) -> Dict[str, Any]:
        """Get exchange inflows and outflows."""
        try:
            if self.use_mock:
                flows = _generate_mock_exchange_flows()
                if asset:
                    flows = [f for f in flows if f["asset"] == asset.upper()]

                summary = {}
                for flow in flows:
                    a = flow["asset"]
                    if a not in summary:
                        summary[a] = {"total_inflow": 0, "total_outflow": 0, "net_flow": 0}
                    summary[a]["total_inflow"] += flow["exchange_inflow"]
                    summary[a]["total_outflow"] += flow["exchange_outflow"]
                    summary[a]["net_flow"] += flow["net_flow"]

                for a in summary:
                    summary[a] = {k: round(v, 4) for k, v in summary[a].items()}

                return {
                    "success": True,
                    "flows": flows[:48],
                    "summary": summary,
                    "count": len(flows[:48]),
                    "source": "mock",
                }

            cutoff = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
            query = self.db.supabase.table("onchain_exchange_flows").select("*").gte("timestamp", cutoff)
            if asset:
                query = query.eq("asset", asset.upper())
            response = query.order("timestamp", desc=True).execute()
            flows = response.data or []

            return {
                "success": True,
                "flows": flows,
                "count": len(flows),
                "source": "database",
            }
        except Exception as e:
            logger.error(f"Failed to get exchange flows: {e}")
            return {"success": False, "error": str(e), "flows": [], "count": 0}
