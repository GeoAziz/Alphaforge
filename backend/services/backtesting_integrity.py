"""
Backtesting Integrity Standards
Architecture Doc §20: Pre-registration policy, data separation,
minimum backtest requirements, performance reporting, benchmark comparison.
"""

import logging
import hashlib
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class DatasetType(str, Enum):
    TRAINING = "training"
    VALIDATION = "validation"
    HOLDOUT = "holdout"
    PRODUCTION = "production"


@dataclass
class BacktestReport:
    strategy_id: str
    hypothesis: str
    backtest_period: str
    data_source: str
    equity_curve: List[float]
    monthly_returns: List[Dict[str, Any]]
    worst_drawdown: float
    worst_drawdown_recovery_days: int
    sharpe_ratio: float
    sortino_ratio: float
    trade_count: int
    avg_trade_duration_hours: float
    win_rate: float
    profit_factor: float
    benchmark_comparison: Dict[str, Any]
    disclaimer: str


class BacktestingIntegrityService:
    """
    Enforces backtesting integrity per §20.

    §20.1: Pre-registration policy (hypothesis before backtest)
    §20.2: Data separation (train/validation/holdout/production)
    §20.3: Minimum backtest requirements
    §20.4: Performance reporting standards
    §20.5: Benchmark comparison standards
    """

    MIN_TEST_PERIOD_YEARS = 2
    MIN_TRADE_COUNT = 100
    MIN_SHARPE = 1.0
    MAX_DRAWDOWN = 25.0
    MIN_PROFIT_FACTOR = 1.5
    MIN_WIN_RATE = 50.0

    BENCHMARK_REQUIREMENTS = {
        "BTC": {"benchmark": "buy_and_hold_btc", "required_alpha": 0.10},
        "ETH": {"benchmark": "buy_and_hold_eth", "required_alpha": 0.08},
        "ALT": {"benchmark": "buy_and_hold_respective", "required_alpha": 0.05},
        "MULTI": {"benchmark": "equally_weighted", "required_alpha": 0.07},
    }

    DISCLAIMER = "Past performance does not guarantee future results."

    def __init__(self, db):
        self.db = db
        self._preregistrations: Dict[str, Dict[str, Any]] = {}
        self._data_separation: Dict[str, Dict[str, Any]] = {}
        self._reports: List[BacktestReport] = []

    # ========================================================================
    # §20.1 Pre-Registration Policy
    # ========================================================================

    async def preregister_hypothesis(
        self,
        strategy_id: str,
        researcher_id: str,
        hypothesis: str,
        asset_universe: List[str],
        timeframe: str,
        entry_logic: str,
        exit_logic: str,
        expected_driver: str,
    ) -> Dict[str, Any]:
        """
        Pre-register hypothesis BEFORE running any backtest.
        Per §20.1: Prevents cherry-picking backtests.
        """
        try:
            timestamp = datetime.utcnow().isoformat()
            prereg = {
                "strategy_id": strategy_id,
                "researcher_id": researcher_id,
                "hypothesis": hypothesis,
                "asset_universe": asset_universe,
                "timeframe": timeframe,
                "entry_logic": entry_logic,
                "exit_logic": exit_logic,
                "expected_driver": expected_driver,
                "preregistered_at": timestamp,
                "hash": hashlib.sha256(
                    f"{strategy_id}:{hypothesis}:{timestamp}".encode()
                ).hexdigest()[:16],
            }

            self._preregistrations[strategy_id] = prereg

            if self.db and self.db.supabase:
                self.db.supabase.table("backtest_preregistrations").insert(prereg).execute()

            logger.info(f"✅ Hypothesis pre-registered: {strategy_id}")
            return {"success": True, "preregistration": prereg}

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def verify_preregistration(self, strategy_id: str) -> Dict[str, Any]:
        """Verify that a hypothesis was pre-registered before backtest."""
        prereg = self._preregistrations.get(strategy_id)
        if not prereg:
            return {
                "success": True,
                "preregistered": False,
                "warning": "No pre-registration found. Backtest results may not be reliable.",
            }
        return {"success": True, "preregistered": True, "preregistration": prereg}

    # ========================================================================
    # §20.2 Data Separation Policy
    # ========================================================================

    async def separate_data(
        self,
        strategy_id: str,
        full_dataset: List[Dict[str, Any]],
        train_pct: float = 0.60,
        validation_pct: float = 0.20,
    ) -> Dict[str, Any]:
        """
        Separate data into train/validation/holdout sets.
        Per §20.2: Holdout set touched exactly once per research cycle.
        """
        total = len(full_dataset)
        train_end = int(total * train_pct)
        val_end = int(total * (train_pct + validation_pct))

        sets = {
            DatasetType.TRAINING.value: full_dataset[:train_end],
            DatasetType.VALIDATION.value: full_dataset[train_end:val_end],
            DatasetType.HOLDOUT.value: full_dataset[val_end:],
        }

        hashes = {}
        for name, data in sets.items():
            hashes[name] = hashlib.sha256(
                json.dumps(data, sort_keys=True, default=str).encode()
            ).hexdigest()[:16]

        self._data_separation[strategy_id] = {
            "sizes": {name: len(data) for name, data in sets.items()},
            "hashes": hashes,
            "separated_at": datetime.utcnow().isoformat(),
        }

        return {
            "success": True,
            "strategy_id": strategy_id,
            "sizes": {name: len(data) for name, data in sets.items()},
            "hashes": hashes,
        }

    # ========================================================================
    # §20.3 Minimum Backtest Requirements
    # ========================================================================

    async def validate_minimum_requirements(
        self,
        backtest_results: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Validate backtest meets minimum requirements per §20.3.
        """
        sharpe = backtest_results.get("sharpe_ratio", 0)
        max_dd = backtest_results.get("max_drawdown", 100)
        pf = backtest_results.get("profit_factor", 0)
        trade_count = backtest_results.get("total_trades", 0)
        win_rate = backtest_results.get("win_rate", 0)

        requirements = {
            "sharpe_ratio": {
                "value": sharpe,
                "required": self.MIN_SHARPE,
                "pass": sharpe >= self.MIN_SHARPE,
            },
            "max_drawdown": {
                "value": max_dd,
                "required": f"≤{self.MAX_DRAWDOWN}%",
                "pass": max_dd <= self.MAX_DRAWDOWN,
            },
            "profit_factor": {
                "value": pf,
                "required": self.MIN_PROFIT_FACTOR,
                "pass": pf >= self.MIN_PROFIT_FACTOR,
            },
            "trade_count": {
                "value": trade_count,
                "required": self.MIN_TRADE_COUNT,
                "pass": trade_count >= self.MIN_TRADE_COUNT,
            },
            "win_rate": {
                "value": win_rate,
                "required": f"≥{self.MIN_WIN_RATE}%",
                "pass": win_rate >= self.MIN_WIN_RATE,
            },
        }

        all_pass = all(r["pass"] for r in requirements.values())

        return {
            "success": True,
            "meets_requirements": all_pass,
            "requirements": requirements,
        }

    # ========================================================================
    # §20.4 Performance Reporting Standards
    # ========================================================================

    async def generate_performance_report(
        self,
        strategy_id: str,
        backtest_results: Dict[str, Any],
        benchmark_results: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Generate a full performance report per §20.4.
        Includes equity curve, monthly returns, drawdown, and benchmark comparison.
        """
        try:
            equity_curve = backtest_results.get("equity_curve", [])
            monthly_returns = backtest_results.get("monthly_returns", [])

            worst_dd = backtest_results.get("max_drawdown", 0)
            worst_dd_recovery = backtest_results.get("recovery_days", 0)

            benchmark_comparison = {}
            if benchmark_results:
                strategy_return = backtest_results.get("total_return", 0)
                benchmark_return = benchmark_results.get("total_return", 0)
                alpha = strategy_return - benchmark_return

                benchmark_comparison = {
                    "benchmark_return": benchmark_return,
                    "strategy_return": strategy_return,
                    "alpha": round(alpha, 4),
                    "correlation": backtest_results.get("benchmark_correlation", 0),
                    "beta": backtest_results.get("beta", 1.0),
                }

            report = BacktestReport(
                strategy_id=strategy_id,
                hypothesis=self._preregistrations.get(strategy_id, {}).get("hypothesis", "N/A"),
                backtest_period=f"{backtest_results.get('start_date', 'N/A')} to {backtest_results.get('end_date', 'N/A')}",
                data_source=backtest_results.get("data_source", "N/A"),
                equity_curve=equity_curve,
                monthly_returns=monthly_returns,
                worst_drawdown=worst_dd,
                worst_drawdown_recovery_days=worst_dd_recovery,
                sharpe_ratio=backtest_results.get("sharpe_ratio", 0),
                sortino_ratio=backtest_results.get("sortino_ratio", 0),
                trade_count=backtest_results.get("total_trades", 0),
                avg_trade_duration_hours=backtest_results.get("avg_trade_duration", 0),
                win_rate=backtest_results.get("win_rate", 0),
                profit_factor=backtest_results.get("profit_factor", 0),
                benchmark_comparison=benchmark_comparison,
                disclaimer=self.DISCLAIMER,
            )

            self._reports.append(report)

            if self.db and self.db.supabase:
                self.db.supabase.table("backtest_reports").insert(asdict(report)).execute()

            return {"success": True, "report": asdict(report)}

        except Exception as e:
            return {"success": False, "error": str(e)}

    # ========================================================================
    # §20.5 Benchmark Comparison Standards
    # ========================================================================

    async def check_benchmark_outperformance(
        self,
        strategy_id: str,
        asset_class: str,
        strategy_return: float,
        benchmark_return: float,
        consecutive_months_underperforming: int = 0,
    ) -> Dict[str, Any]:
        """
        Check if strategy outperforms benchmark per §20.5.
        Auto-retire if underperformance continues.
        """
        benchmark_config = self.BENCHMARK_REQUIREMENTS.get(
            asset_class,
            self.BENCHMARK_REQUIREMENTS["MULTI"],
        )

        alpha = strategy_return - benchmark_return
        meets_alpha = alpha >= benchmark_config["required_alpha"]

        underperforming = consecutive_months_underperforming >= 2

        result = {
            "success": True,
            "strategy_id": strategy_id,
            "asset_class": asset_class,
            "strategy_return": strategy_return,
            "benchmark_return": benchmark_return,
            "alpha": round(alpha, 4),
            "required_alpha": benchmark_config["required_alpha"],
            "meets_alpha_requirement": meets_alpha,
            "consecutive_months_underperforming": consecutive_months_underperforming,
            "underperforming_flag": underperforming,
            "recommendation": "",
        }

        if underperforming:
            result["recommendation"] = (
                "Strategy underperforming for 2+ consecutive months. "
                "Mark as underperforming on marketplace, reduce visibility, "
                "notify subscribers, give creator 4 weeks to respond."
            )
        elif not meets_alpha:
            result["recommendation"] = "Strategy not meeting alpha requirement. Monitor closely."
        else:
            result["recommendation"] = "Strategy outperforming benchmark. Continue normal operation."

        return result

    def get_all_reports(self) -> List[Dict[str, Any]]:
        return [asdict(r) for r in self._reports]
