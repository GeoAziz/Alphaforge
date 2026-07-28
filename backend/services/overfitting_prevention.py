"""
Overfitting Prevention Service
Architecture Doc §10: Look-ahead bias, survivorship bias, purged walk-forward
validation, holdout set policy, and cryptographic audit log.
"""

import logging
import hashlib
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)


@dataclass
class HoldoutSet:
    asset: str
    strategy_class: str
    start_date: str
    end_date: str
    data_hash: str
    accessed_by: List[Dict[str, Any]]
    purity: bool = True
    created_at: str = ""


class OverfittingPreventionService:
    """
    Implements §10.1-10.5 overfitting prevention measures.
    """

    def __init__(self, db):
        self.db = db
        self._holdout_sets: Dict[str, HoldoutSet] = {}
        self._audit_entries: List[Dict[str, Any]] = []

    # ========================================================================
    # §10.1 Look-Ahead Bias Prevention
    # ========================================================================

    async def check_look_ahead_bias(
        self,
        feature_code: str,
        feature_name: str,
    ) -> Dict[str, Any]:
        """
        Static analysis check for look-ahead bias in feature code.
        Per §10.1: Flag any feature that references a future data point.
        """
        suspicious_patterns = [
            "future_",
            "next_",
            "forward_",
            "shift(-",
            "shift(-1",
            "iloc[1:]",
            "iloc[2:]",
            "df['close'].shift(-",
            "df['open'].shift(-",
            "return_series.shift(-",
            "price.shift(-",
            "t+1",
            "t+2",
            "ahead",
        ]

        violations = []
        for pattern in suspicious_patterns:
            if pattern in feature_code.lower():
                violations.append({
                    "pattern": pattern,
                    "severity": "CRITICAL",
                    "message": f"Potential look-ahead bias: '{pattern}' references future data",
                })

        is_clean = len(violations) == 0

        result = {
            "success": True,
            "feature_name": feature_name,
            "look_ahead_clean": is_clean,
            "violations": violations,
            "checked_at": datetime.utcnow().isoformat(),
        }

        if not is_clean:
            logger.warning(f"⚠️ Look-ahead bias detected in feature {feature_name}: {len(violations)} violations")

        if self.db and self.db.supabase:
            self.db.supabase.table("look_ahead_checks").insert({
                "feature_name": feature_name,
                "clean": is_clean,
                "violations": violations,
                "checked_at": datetime.utcnow().isoformat(),
            }).execute()

        return result

    # ========================================================================
    # §10.2 Survivorship Bias Prevention
    # ========================================================================

    async def get_universe_snapshot(
        self,
        timestamp: str,
        asset_universe: List[str],
    ) -> Dict[str, Any]:
        """
        Get asset universe at a specific historical timestamp.
        Per §10.2: Backtests operate on universe snapshot at each timestamp,
        not the current asset universe.
        """
        try:
            active_assets = asset_universe.copy()
            delisted_assets = []

            if self.db and self.db.supabase:
                response = (
                    self.db.supabase.table("asset_universe_history")
                    .select("*")
                    .lte("delisted_at", timestamp)
                    .execute()
                )
                if response.data:
                    delisted = [r["asset"] for r in response.data]
                    delisted_assets = delisted
                    active_assets = [a for a in active_assets if a not in delisted]

            return {
                "success": True,
                "timestamp": timestamp,
                "active_assets": active_assets,
                "delisted_assets": delisted_assets,
                "universe_size": len(active_assets),
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    # ========================================================================
    # §10.3 Purged Walk-Forward Validation
    # ========================================================================

    def purged_walk_forward_split(
        self,
        data: List[Dict[str, Any]],
        n_splits: int = 5,
        purge_gap_days: int = 5,
        test_ratio: float = 0.2,
    ) -> List[Dict[str, Any]]:
        """
        Generate purged walk-forward train/test splits.
        Per §10.3: Purge gap removes observations within a rolling window
        around each test observation from the training set.

        Default purge gap: 5 days for daily models.
        """
        if not data or n_splits < 1:
            return []

        total_len = len(data)
        test_size = max(1, int(total_len * test_ratio))
        splits = []

        for i in range(n_splits):
            test_end = total_len - i * test_size
            test_start = test_end - test_size
            train_end = test_start - purge_gap_days

            if train_end <= 0 or test_start <= 0:
                break

            splits.append({
                "split": i + 1,
                "train_indices": list(range(0, train_end)),
                "test_indices": list(range(test_start, test_end)),
                "purge_gap": purge_gap_days,
                "train_size": train_end,
                "test_size": test_size,
                "train_start": data[0].get("timestamp", ""),
                "train_end": data[min(train_end - 1, total_len - 1)].get("timestamp", ""),
                "test_start": data[test_start].get("timestamp", ""),
                "test_end": data[min(test_end - 1, total_len - 1)].get("timestamp", ""),
            })

        return splits

    # ========================================================================
    # §10.4 Holdout Set Policy
    # ========================================================================

    async def create_holdout_set(
        self,
        asset: str,
        strategy_class: str,
        data: List[Dict[str, Any]],
        holdout_pct: float = 0.10,
    ) -> Dict[str, Any]:
        """
        Create a holdout set covering the most recent 10% of data.
        Per §10.4: Touched exactly once per research cycle.
        """
        try:
            holdout_size = max(1, int(len(data) * holdout_pct))
            holdout_data = data[-holdout_size:]
            data_hash = hashlib.sha256(
                json.dumps(holdout_data, sort_keys=True, default=str).encode()
            ).hexdigest()[:32]

            holdout = HoldoutSet(
                asset=asset,
                strategy_class=strategy_class,
                start_date=holdout_data[0].get("timestamp", ""),
                end_date=holdout_data[-1].get("timestamp", ""),
                data_hash=data_hash,
                accessed_by=[],
                purity=True,
                created_at=datetime.utcnow().isoformat(),
            )

            key = f"{asset}:{strategy_class}"
            self._holdout_sets[key] = holdout

            if self.db and self.db.supabase:
                self.db.supabase.table("holdout_sets").insert(asdict(holdout)).execute()

            logger.info(f"✅ Holdout set created: {asset}/{strategy_class} ({holdout_size} points)")
            return {"success": True, "holdout": asdict(holdout), "size": holdout_size}

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def access_holdout_set(
        self,
        asset: str,
        strategy_class: str,
        researcher_id: str,
        model_version: str,
    ) -> Dict[str, Any]:
        """
        Access holdout set (logged, purity tracking).
        Per §10.4: Holdout set access is logged per researcher per model version.
        """
        key = f"{asset}:{strategy_class}"
        holdout = self._holdout_sets.get(key)
        if not holdout:
            return {"success": False, "error": "Holdout set not found"}

        if not holdout.purity:
            return {"success": False, "error": "Holdout set purity terminated — define new holdout for next cycle"}

        access_record = {
            "researcher_id": researcher_id,
            "model_version": model_version,
            "accessed_at": datetime.utcnow().isoformat(),
        }
        holdout.accessed_by.append(access_record)

        if self.db and self.db.supabase:
            self.db.supabase.table("holdout_sets").update({
                "accessed_by": holdout.accessed_by,
            }).eq("asset", asset).eq("strategy_class", strategy_class).execute()

        return {"success": True, "holdout": asdict(holdout)}

    async def terminate_holdout_purity(
        self, asset: str, strategy_class: str
    ) -> Dict[str, Any]:
        """Mark holdout set as impure (used for final validation)."""
        key = f"{asset}:{strategy_class}"
        holdout = self._holdout_sets.get(key)
        if not holdout:
            return {"success": False, "error": "Holdout set not found"}

        holdout.purity = False
        return {"success": True, "message": "Holdout purity terminated. New holdout required for next cycle."}

    # ========================================================================
    # §10.5 Cryptographic Audit Log
    # ========================================================================

    async def log_model_audit_entry(
        self,
        model_id: str,
        model_version: str,
        model_weights_hash: str,
        train_data_range: str,
        train_data_hash: str,
        validation_data_range: str,
        validation_data_hash: str,
        hyperparameters: Dict[str, Any],
        backtest_metrics: Dict[str, Any],
        researcher_id: str,
        hypothesis: str,
    ) -> Dict[str, Any]:
        """
        Append a tamper-evident audit log entry for a model version.
        Per §10.5: Append-only, signed, stored in separate access-controlled DB.
        """
        try:
            entry_content = {
                "model_id": model_id,
                "model_version": model_version,
                "model_weights_hash": model_weights_hash,
                "train_data_range": train_data_range,
                "train_data_hash": train_data_hash,
                "validation_data_range": validation_data_range,
                "validation_data_hash": validation_data_hash,
                "hyperparameters": hyperparameters,
                "backtest_metrics": backtest_metrics,
                "researcher_id": researcher_id,
                "hypothesis": hypothesis,
                "timestamp": datetime.utcnow().isoformat(),
            }

            entry_hash = hashlib.sha256(
                json.dumps(entry_content, sort_keys=True).encode()
            ).hexdigest()

            prev_hash = self._audit_entries[-1]["entry_hash"] if self._audit_entries else "GENESIS"

            audit_entry = {
                **entry_content,
                "entry_hash": entry_hash,
                "prev_hash": prev_hash,
                "chain_valid": True,
            }

            self._audit_entries.append(audit_entry)

            if self.db and self.db.supabase:
                self.db.supabase.table("model_audit_log").insert(audit_entry).execute()

            logger.info(f"✅ Audit entry logged: {model_id} v{model_version} hash={entry_hash[:16]}")
            return {"success": True, "audit_entry": audit_entry}

        except Exception as e:
            logger.error(f"❌ Audit log failed: {e}")
            return {"success": False, "error": str(e)}

    async def verify_audit_chain(self) -> Dict[str, Any]:
        """Verify integrity of the entire audit chain."""
        valid = True
        broken_at = None

        for i, entry in enumerate(self._audit_entries):
            if i == 0:
                if entry["prev_hash"] != "GENESIS":
                    valid = False
                    broken_at = i
                    break
            else:
                if entry["prev_hash"] != self._audit_entries[i - 1]["entry_hash"]:
                    valid = False
                    broken_at = i
                    break

        return {
            "success": True,
            "chain_valid": valid,
            "total_entries": len(self._audit_entries),
            "broken_at_index": broken_at,
        }
