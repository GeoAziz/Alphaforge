"""
Portfolio Service - Maintains open positions and calculates portfolio state.
Tracks positions, unrealized PnL, exposure limits, and risk metrics.
"""

import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from decimal import Decimal

logger = logging.getLogger(__name__)


class PortfolioService:
    """Manages user portfolio state and open positions."""
    
    def __init__(self, db):
        self.db = db
        self.MAX_POSITION_SIZE_PCT = 0.02  # 2% per position
        self.MAX_PORTFOLIO_EXPOSURE_PCT = 0.20  # 20% per asset
        self.MAX_LEVERAGE = 5
    
    async def open_position(
        self,
        user_id: str,
        ticker: str,
        direction: str,
        entry_price: float,
        quantity: float,
        signal_id: Optional[str] = None,
        current_price: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Open a new trading position.
        """
        
        if current_price is None:
            current_price = entry_price
        
        position_data = {
            "user_id": user_id,
            "ticker": ticker,
            "direction": direction,
            "entry_price": entry_price,
            "quantity": quantity,
            "current_price": current_price,
            "signal_id": signal_id,
            "opened_at": datetime.utcnow().isoformat()
        }
        
        try:
            response = self.db.supabase.table("positions").insert(position_data).execute()
            position_id = response.data[0]["id"] if response.data else None
            
            logger.info(f"✅ Position opened: {ticker} {direction} ({quantity} @{entry_price})")
            
            return {
                "success": True,
                "position_id": position_id,
                "position": position_data
            }
        
        except Exception as e:
            logger.error(f"❌ Position creation failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def close_position(
        self,
        user_id: str,
        position_id: str,
        exit_price: float
    ) -> Dict[str, Any]:
        """
        Close an open position and record realized PnL.
        """
        
        try:
            # Fetch position
            response = self.db.supabase.table("positions").select("*").eq("id", position_id).eq("user_id", user_id).execute()
            
            if not response.data:
                return {"success": False, "error": "Position not found"}
            
            position = response.data[0]
            
            entry_price = float(position["entry_price"])
            quantity = float(position["quantity"])
            direction = position["direction"]
            
            # Calculate PnL
            if direction == "LONG":
                pnl = (exit_price - entry_price) * quantity
            else:  # SHORT
                pnl = (entry_price - exit_price) * quantity
            
            # Delete position (closed)
            self.db.supabase.table("positions").delete().eq("id", position_id).execute()
            
            logger.info(f"✅ Position closed: {position['ticker']} (PnL: ${pnl:.2f})")
            
            return {
                "success": True,
                "pnl": pnl,
                "exit_price": exit_price
            }
        
        except Exception as e:
            logger.error(f"❌ Position close failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def update_position_price(
        self,
        position_id: str,
        current_price: float
    ) -> Dict[str, Any]:
        """Update current price for a position (for real-time updates)."""
        
        try:
            self.db.supabase.table("positions").update({
                "current_price": current_price
            }).eq("id", position_id).execute()
            
            return {"success": True}
        
        except Exception as e:
            logger.error(f"❌ Position price update failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_open_positions(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all open positions for a user."""
        
        try:
            response = self.db.supabase.table("positions").select("*").eq("user_id", user_id).execute()
            positions = response.data or []
            
            # Calculate unrealized PnL for each position
            for position in positions:
                position = self._calculate_position_pnl(position)
            
            return positions
        
        except Exception as e:
            logger.error(f"❌ Failed to fetch positions: {e}")
            return []
    
    async def get_portfolio_summary(self, user_id: str) -> Dict[str, Any]:
        """Get comprehensive portfolio summary."""
        
        try:
            # Fetch portfolio record
            portfolio_response = self.db.supabase.table("portfolios").select("*").eq("user_id", user_id).execute()
            
            if portfolio_response.data:
                portfolio = portfolio_response.data[0]
            else:
                # Create default
                portfolio = {
                    "user_id": user_id,
                    "starting_balance": 100000,
                    "current_balance": 100000,
                    "total_pnl": 0
                }
                self.db.supabase.table("portfolios").insert(portfolio).execute()
            
            # Get open positions
            positions = await self.get_open_positions(user_id)
            
            # Calculate metrics from positions
            total_unrealized_pnl = 0
            total_exposure = 0
            
            for position in positions:
                position = self._calculate_position_pnl(position)
                total_unrealized_pnl += position.get("unrealized_pnl", 0)
                total_exposure += position.get("risk_exposure_pct", 0)
            
            current_balance = float(portfolio.get("current_balance", 100000))
            total_equity = current_balance + total_unrealized_pnl
            
            summary = {
                "portfolio_id": portfolio.get("id"),
                "user_id": user_id,
                "starting_balance": float(portfolio.get("starting_balance", 100000)),
                "current_balance": current_balance,
                "total_equity": total_equity,
                "unrealized_pnl": total_unrealized_pnl,
                "realized_pnl": float(portfolio.get("total_pnl", 0)),
                "total_pnl": total_unrealized_pnl + float(portfolio.get("total_pnl", 0)),
                "total_pnl_percent": (total_unrealized_pnl + float(portfolio.get("total_pnl", 0))) / float(portfolio.get("starting_balance", 100000)) * 100,
                "open_positions_count": len(positions),
                "total_exposure_pct": total_exposure,
                "open_positions": positions
            }
            
            logger.info(f"📊 Portfolio summary for {user_id}: Equity ${summary['total_equity']:.2f}, PnL {summary['total_pnl_percent']:+.2f}%")
            
            return summary
        
        except Exception as e:
            logger.error(f"❌ Portfolio summary calculation failed: {e}")
            return {}
    
    def _calculate_position_pnl(self, position: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate unrealized PnL metrics for a position."""
        
        entry_price = float(position.get("entry_price", 0))
        current_price = float(position.get("current_price", entry_price))
        quantity = float(position.get("quantity", 0))
        direction = position.get("direction", "LONG")
        
        # Calculate unrealized PnL
        if direction == "LONG":
            unrealized_pnl = (current_price - entry_price) * quantity
        else:  # SHORT
            unrealized_pnl = (entry_price - current_price) * quantity
        
        unrealized_pnl_percent = (unrealized_pnl / (entry_price * quantity) * 100) if (entry_price * quantity) > 0 else 0
        
        # Risk exposure (as % of position value)
        position_value = entry_price * quantity
        risk_exposure_pct = position_value / 100000 * 100  # Assuming 100k portfolio
        
        position.update({
            "unrealized_pnl": unrealized_pnl,
            "unrealized_pnl_percent": unrealized_pnl_percent,
            "risk_exposure_pct": risk_exposure_pct
        })
        
        return position
    
    async def validate_position_size(
        self,
        user_id: str,
        portfolio_balance: float,
        ticker: str,
        position_value: float
    ) -> Tuple[bool, str]:
        """
        Validate if a new position meets risk constraints.
        Returns: (is_valid, reason)
        """
        
        # Check: Position size limit (2% of portfolio)
        position_size_pct = (position_value / portfolio_balance) * 100
        if position_size_pct > 2:
            return False, f"Position size ({position_size_pct:.2f}%) exceeds 2% limit"
        
        # Check: Existing exposure to same asset
        positions = await self.get_open_positions(user_id)
        existing_exposure = sum(
            float(p.get("entry_price", 0)) * float(p.get("quantity", 0))
            for p in positions
            if p.get("ticker") == ticker
        )
        
        total_exposure = existing_exposure + position_value
        exposure_pct = (total_exposure / portfolio_balance) * 100
        
        if exposure_pct > 20:
            return False, f"Total {ticker} exposure ({exposure_pct:.2f}%) exceeds 20% limit"
        
        return True, "Position size valid"
