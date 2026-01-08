"""
Energy Trading GUI Module

This module provides a web-based GUI for the Energy Trading Marketplace,
including dashboards for energy producers, traders, and administrators.
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta

from utils.logging_config import get_logger

logger = get_logger(__name__)


class EnergyTradingGUI:
    """
    Web GUI for Energy Trading Marketplace.

    Provides interactive dashboards and interfaces for:
    - Energy park management
    - Trading marketplace
    - Provider management
    - Analytics and reporting
    """

    def __init__(self, marketplace: Any, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Energy Trading GUI.

        Args:
            marketplace: EnergyTradingMarketplace instance
            config: GUI configuration
        """
        self.marketplace = marketplace
        self.config = config or self._get_default_config()
        self.logger = get_logger(__name__)

        # GUI state
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.dashboard_cache: Dict[str, Any] = {}

        # Routes and handlers
        self.routes = self._setup_routes()

        self.logger.info("Energy Trading GUI initialized")

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default GUI configuration."""
        return {
            "theme": "dark",
            "language": "en",
            "refresh_interval": 30,  # seconds
            "max_chart_points": 100,
            "enable_real_time": True,
            "supported_currencies": ["EUR", "USD", "BGN"],
            "chart_colors": {
                "solar": "#FFD700",
                "wind": "#87CEEB",
                "hydro": "#4169E1",
                "biomass": "#228B22",
                "geothermal": "#DC143C"
            }
        }

    def _setup_routes(self) -> Dict[str, callable]:
        """Set up GUI routes and handlers."""
        return {
            "/energy-trading": self.get_main_dashboard,
            "/energy-trading/parks": self.get_parks_dashboard,
            "/energy-trading/market": self.get_market_dashboard,
            "/energy-trading/trades": self.get_trades_dashboard,
            "/energy-trading/analytics": self.get_analytics_dashboard,
            "/energy-trading/api/market-overview": self.api_get_market_overview,
            "/energy-trading/api/park-status": self.api_get_park_status,
            "/energy-trading/api/create-offer": self.api_create_offer,
            "/energy-trading/api/place-bid": self.api_place_bid,
            "/energy-trading/api/execute-trade": self.api_execute_trade,
        }

    async def get_main_dashboard(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Get main energy trading dashboard."""
        try:
            # Get market overview
            market_overview = await self.marketplace.get_market_overview()

            # Get recent trades
            recent_trades = await self._get_recent_trades(limit=10)

            # Get top energy parks
            top_parks = await self._get_top_parks(limit=5)

            dashboard_data = {
                "title": "Energy Trading Marketplace",
                "market_overview": market_overview,
                "recent_trades": recent_trades,
                "top_parks": top_parks,
                "quick_actions": [
                    {"label": "Create Energy Offer", "action": "create_offer", "icon": "plus"},
                    {"label": "View Market", "action": "view_market", "icon": "market"},
                    {"label": "Manage Parks", "action": "manage_parks", "icon": "settings"}
                ],
                "alerts": await self._get_system_alerts(),
                "timestamp": asyncio.get_event_loop().time()
            }

            return self._render_template("main_dashboard.html", dashboard_data)

        except Exception as e:
            self.logger.error(f"Failed to get main dashboard: {e}")
            return self._render_error("Dashboard error", str(e))

    async def get_parks_dashboard(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Get energy parks management dashboard."""
        try:
            park_id = request.get("query_params", {}).get("park_id")

            if park_id:
                # Single park view
                park_status = await self.marketplace.get_energy_park_status(park_id)
                if not park_status:
                    return self._render_error("Park not found", f"Energy park {park_id} not found")

                # Get park production history
                production_history = await self._get_park_production_history(park_id)

                dashboard_data = {
                    "title": f"Energy Park: {park_status['name']}",
                    "park_status": park_status,
                    "production_history": production_history,
                    "performance_metrics": await self._calculate_park_metrics(park_id),
                    "actions": [
                        {"label": "Create Offer", "action": "create_offer", "park_id": park_id},
                        {"label": "View Sources", "action": "view_sources", "park_id": park_id},
                        {"label": "Maintenance", "action": "schedule_maintenance", "park_id": park_id}
                    ]
                }

                return self._render_template("park_detail.html", dashboard_data)
            else:
                # All parks overview
                all_parks = []
                for park_id in self.marketplace.energy_parks.keys():
                    park_status = await self.marketplace.get_energy_park_status(park_id)
                    if park_status:
                        all_parks.append(park_status)

                dashboard_data = {
                    "title": "Energy Parks Overview",
                    "parks": all_parks,
                    "summary": await self._calculate_parks_summary(all_parks),
                    "actions": [
                        {"label": "Add New Park", "action": "add_park", "icon": "plus"},
                        {"label": "Bulk Operations", "action": "bulk_ops", "icon": "batch"}
                    ]
                }

                return self._render_template("parks_overview.html", dashboard_data)

        except Exception as e:
            self.logger.error(f"Failed to get parks dashboard: {e}")
            return self._render_error("Parks dashboard error", str(e))

    async def get_market_dashboard(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Get energy trading market dashboard."""
        try:
            market_overview = await self.marketplace.get_market_overview()

            # Get active offers
            active_offers = [
                offer for offer in self.marketplace.energy_offers.values()
                if offer["status"] == "active"
            ]

            # Get price history for charts
            price_history = await self._get_price_history(hours=24)

            # Get market statistics
            market_stats = await self._calculate_market_stats()

            dashboard_data = {
                "title": "Energy Trading Market",
                "market_overview": market_overview,
                "active_offers": active_offers[:20],  # Limit for display
                "price_history": price_history,
                "market_stats": market_stats,
                "filters": {
                    "energy_sources": ["solar", "wind", "hydro", "biomass", "geothermal"],
                    "price_range": {"min": 0, "max": 1.0},
                    "amount_range": {"min": 1, "max": 10000}
                },
                "actions": [
                    {"label": "Place Bid", "action": "place_bid", "icon": "bid"},
                    {"label": "Create Offer", "action": "create_offer", "icon": "offer"},
                    {"label": "Market Analysis", "action": "market_analysis", "icon": "chart"}
                ]
            }

            return self._render_template("market_dashboard.html", dashboard_data)

        except Exception as e:
            self.logger.error(f"Failed to get market dashboard: {e}")
            return self._render_error("Market dashboard error", str(e))

    async def get_trades_dashboard(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Get trades and transactions dashboard."""
        try:
            # Get active trades
            active_trades = list(self.marketplace.active_trades.values())

            # Get completed trades (last 50)
            completed_trades = self.marketplace.completed_trades[-50:]

            # Get trade statistics
            trade_stats = await self._calculate_trade_stats()

            dashboard_data = {
                "title": "Energy Trades & Transactions",
                "active_trades": active_trades,
                "completed_trades": completed_trades,
                "trade_stats": trade_stats,
                "settlement_status": await self._get_settlement_status(),
                "actions": [
                    {"label": "Execute Trade", "action": "execute_trade", "icon": "execute"},
                    {"label": "View Settlements", "action": "view_settlements", "icon": "settlement"},
                    {"label": "Trade History", "action": "trade_history", "icon": "history"}
                ]
            }

            return self._render_template("trades_dashboard.html", dashboard_data)

        except Exception as e:
            self.logger.error(f"Failed to get trades dashboard: {e}")
            return self._render_error("Trades dashboard error", str(e))

    async def get_analytics_dashboard(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Get analytics and reporting dashboard."""
        try:
            # Get production analytics
            production_analytics = await self._get_production_analytics()

            # Get trading analytics
            trading_analytics = await self._get_trading_analytics()

            # Get efficiency metrics
            efficiency_metrics = await self._get_efficiency_metrics()

            # Get forecast data
            forecast_data = await self._get_forecast_data()

            dashboard_data = {
                "title": "Energy Trading Analytics",
                "production_analytics": production_analytics,
                "trading_analytics": trading_analytics,
                "efficiency_metrics": efficiency_metrics,
                "forecast_data": forecast_data,
                "reports": [
                    {"name": "Production Report", "type": "production", "format": "pdf"},
                    {"name": "Trading Report", "type": "trading", "format": "excel"},
                    {"name": "Efficiency Report", "type": "efficiency", "format": "pdf"}
                ],
                "charts": {
                    "production_trend": await self._generate_production_chart(),
                    "price_trend": await self._generate_price_chart(),
                    "efficiency_trend": await self._generate_efficiency_chart()
                }
            }

            return self._render_template("analytics_dashboard.html", dashboard_data)

        except Exception as e:
            self.logger.error(f"Failed to get analytics dashboard: {e}")
            return self._render_error("Analytics dashboard error", str(e))

    # API endpoints
    async def api_get_market_overview(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """API endpoint for market overview data."""
        try:
            data = await self.marketplace.get_market_overview()
            return {"status": "success", "data": data}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def api_get_park_status(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """API endpoint for park status."""
        try:
            park_id = request.get("query_params", {}).get("park_id")
            if not park_id:
                return {"status": "error", "message": "park_id required"}

            data = await self.marketplace.get_energy_park_status(park_id)
            if not data:
                return {"status": "error", "message": "Park not found"}

            return {"status": "success", "data": data}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def api_create_offer(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """API endpoint for creating energy offers."""
        try:
            offer_data = request.get("body", {})

            # Validate required fields
            required_fields = ["seller_id", "energy_amount", "price_per_kwh", "valid_until"]
            for field in required_fields:
                if field not in offer_data:
                    return {"status": "error", "message": f"Missing field: {field}"}

            result = await self.marketplace.create_energy_offer(
                offer_data["seller_id"],
                offer_data
            )

            return {"status": "success", "data": result}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def api_place_bid(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """API endpoint for placing bids."""
        try:
            bid_data = request.get("body", {})

            required_fields = ["offer_id", "buyer_id", "energy_amount", "bid_price"]
            for field in required_fields:
                if field not in bid_data:
                    return {"status": "error", "message": f"Missing field: {field}"}

            result = await self.marketplace.place_bid_on_offer(
                bid_data["offer_id"],
                bid_data["buyer_id"],
                bid_data
            )

            return {"status": "success", "data": result}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def api_execute_trade(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """API endpoint for executing trades."""
        try:
            trade_data = request.get("body", {})

            required_fields = ["offer_id", "bid_id"]
            for field in required_fields:
                if field not in trade_data:
                    return {"status": "error", "message": f"Missing field: {field}"}

            result = await self.marketplace.execute_trade(
                trade_data["offer_id"],
                trade_data["bid_id"]
            )

            return {"status": "success", "data": result}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    # Helper methods
    async def _get_recent_trades(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent completed trades."""
        completed_trades = self.marketplace.completed_trades[-limit:]
        active_trades = list(self.marketplace.active_trades.values())[:limit]

        all_trades = completed_trades + active_trades
        # Sort by execution time (most recent first)
        all_trades.sort(key=lambda x: x.get("executed_at", 0), reverse=True)

        return all_trades[:limit]

    async def _get_top_parks(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get top performing energy parks."""
        parks = []
        for park_id in self.marketplace.energy_parks.keys():
            park_status = await self.marketplace.get_energy_park_status(park_id)
            if park_status:
                parks.append(park_status)

        # Sort by current production
        parks.sort(key=lambda x: x.get("current_production", 0), reverse=True)
        return parks[:limit]

    async def _get_system_alerts(self) -> List[Dict[str, Any]]:
        """Get system alerts and notifications."""
        alerts = []

        # Check for expired offers
        current_time = asyncio.get_event_loop().time()
        expired_count = sum(
            1 for offer in self.marketplace.energy_offers.values()
            if offer["status"] == "active" and offer["valid_until"] < current_time
        )

        if expired_count > 0:
            alerts.append({
                "type": "warning",
                "message": f"{expired_count} energy offers have expired",
                "action": "view_market"
            })

        # Check for high market activity
        market_overview = await self.marketplace.get_market_overview()
        if market_overview.get("active_trades", 0) > 10:
            alerts.append({
                "type": "info",
                "message": "High market activity detected",
                "action": "view_market"
            })

        return alerts

    async def _get_park_production_history(self, park_id: str) -> List[Dict[str, Any]]:
        """Get production history for a park."""
        history = []
        for source_id, records in self.marketplace.production_history.items():
            source = self.marketplace.energy_sources.get(source_id, {})
            if source.get("park_id") == park_id:
                history.extend(records[-24:])  # Last 24 records

        # Sort by timestamp
        history.sort(key=lambda x: x["timestamp"])
        return history[-100:]  # Last 100 records

    async def _calculate_park_metrics(self, park_id: str) -> Dict[str, Any]:
        """Calculate performance metrics for a park."""
        history = await self._get_park_production_history(park_id)

        if not history:
            return {"efficiency": 0, "uptime": 0, "avg_production": 0}

        total_production = sum(h.get("current_power", 0) for h in history)
        avg_production = total_production / len(history) if history else 0

        # Calculate efficiency (simplified)
        park = self.marketplace.energy_parks.get(park_id, {})
        capacity = park.get("total_capacity", 1)
        efficiency = (avg_production / capacity) * 100 if capacity > 0 else 0

        # Calculate uptime (simplified)
        normal_readings = sum(1 for h in history if h.get("status") == "normal")
        uptime = (normal_readings / len(history)) * 100 if history else 0

        return {
            "efficiency": round(efficiency, 2),
            "uptime": round(uptime, 2),
            "avg_production": round(avg_production, 2),
            "total_records": len(history)
        }

    async def _calculate_parks_summary(self, parks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate summary statistics for all parks."""
        if not parks:
            return {"total_capacity": 0, "total_production": 0, "avg_efficiency": 0}

        total_capacity = sum(p.get("total_capacity", 0) for p in parks)
        total_production = sum(p.get("current_production", 0) for p in parks)
        avg_efficiency = sum(p.get("efficiency", 0) for p in parks) / len(parks) if parks else 0

        return {
            "total_parks": len(parks),
            "total_capacity": round(total_capacity, 2),
            "total_production": round(total_production, 2),
            "avg_efficiency": round(avg_efficiency, 2)
        }

    async def _get_price_history(self, hours: int = 24) -> Dict[str, List]:
        """Get price history for charting."""
        cutoff_time = asyncio.get_event_loop().time() - (hours * 3600)

        price_data = {}
        for source_type, prices in self.marketplace.price_history.items():
            # Filter recent prices
            recent_prices = [
                (timestamp, price) for timestamp, price in prices
                if timestamp > cutoff_time
            ]
            price_data[source_type] = recent_prices[-self.config["max_chart_points"]:]

        return price_data

    async def _calculate_market_stats(self) -> Dict[str, Any]:
        """Calculate market statistics."""
        active_offers = [o for o in self.marketplace.energy_offers.values() if o["status"] == "active"]
        active_trades = list(self.marketplace.active_trades.values())

        total_offered = sum(o["energy_amount"] for o in active_offers)
        total_traded = sum(t["energy_amount"] for t in active_trades)

        # Price statistics
        prices = [o["price_per_kwh"] for o in active_offers if o["price_per_kwh"] > 0]
        avg_price = sum(prices) / len(prices) if prices else 0
        min_price = min(prices) if prices else 0
        max_price = max(prices) if prices else 0

        return {
            "active_offers": len(active_offers),
            "active_trades": len(active_trades),
            "total_energy_offered_kwh": round(total_offered, 2),
            "total_energy_traded_kwh": round(total_traded, 2),
            "avg_price_per_kwh": round(avg_price, 4),
            "price_range": {"min": round(min_price, 4), "max": round(max_price, 4)},
            "market_efficiency": round((total_traded / total_offered * 100), 2) if total_offered > 0 else 0
        }

    async def _calculate_trade_stats(self) -> Dict[str, Any]:
        """Calculate trading statistics."""
        active_trades = list(self.marketplace.active_trades.values())
        completed_trades = self.marketplace.completed_trades[-100:]  # Last 100

        total_active_value = sum(t["total_value"] for t in active_trades)
        total_completed_value = sum(t["total_value"] for t in completed_trades)

        # Volume by source
        volume_by_source = {}
        for trade in completed_trades:
            source = trade.get("energy_source", "unknown")
            volume_by_source[source] = volume_by_source.get(source, 0) + trade["energy_amount"]

        return {
            "active_trades_count": len(active_trades),
            "completed_trades_count": len(completed_trades),
            "active_trades_value": round(total_active_value, 2),
            "completed_trades_value": round(total_completed_value, 2),
            "volume_by_source": volume_by_source,
            "avg_trade_size": round(sum(t["energy_amount"] for t in completed_trades) / len(completed_trades), 2) if completed_trades else 0
        }

    async def _get_settlement_status(self) -> Dict[str, Any]:
        """Get settlement status overview."""
        # Placeholder for settlement status
        return {
            "pending_settlements": 0,
            "completed_today": 0,
            "total_outstanding": 0
        }

    async def _get_production_analytics(self) -> Dict[str, Any]:
        """Get production analytics data."""
        # Aggregate production data by source type
        production_by_type = {}
        total_production = 0

        for source in self.marketplace.energy_sources.values():
            source_type = source["type"].value
            production = source.get("total_production", 0)

            production_by_type[source_type] = production_by_type.get(source_type, 0) + production
            total_production += production

        return {
            "production_by_type": production_by_type,
            "total_production": round(total_production, 2),
            "active_sources": len([s for s in self.marketplace.energy_sources.values() if s["status"] == "active"]),
            "efficiency_trend": []  # Would contain historical efficiency data
        }

    async def _get_trading_analytics(self) -> Dict[str, Any]:
        """Get trading analytics data."""
        completed_trades = self.marketplace.completed_trades

        if not completed_trades:
            return {"total_trades": 0, "total_value": 0, "avg_price": 0}

        total_value = sum(t["total_value"] for t in completed_trades)
        total_volume = sum(t["energy_amount"] for t in completed_trades)
        avg_price = total_value / total_volume if total_volume > 0 else 0

        # Revenue by source
        revenue_by_source = {}
        for trade in completed_trades:
            source = trade.get("energy_source", "unknown")
            revenue_by_source[source] = revenue_by_source.get(source, 0) + trade["total_value"]

        return {
            "total_trades": len(completed_trades),
            "total_value": round(total_value, 2),
            "total_volume": round(total_volume, 2),
            "avg_price_per_kwh": round(avg_price, 4),
            "revenue_by_source": revenue_by_source
        }

    async def _get_efficiency_metrics(self) -> Dict[str, Any]:
        """Get efficiency metrics."""
        # Calculate system-wide efficiency
        total_capacity = sum(p.get("total_capacity", 0) for p in self.marketplace.energy_parks.values())
        total_production = sum(p.get("current_production", 0) for p in self.marketplace.energy_parks.values())

        system_efficiency = (total_production / total_capacity * 100) if total_capacity > 0 else 0

        return {
            "system_efficiency": round(system_efficiency, 2),
            "total_capacity": round(total_capacity, 2),
            "total_production": round(total_production, 2),
            "utilization_rate": round((total_production / total_capacity * 100), 2) if total_capacity > 0 else 0
        }

    async def _get_forecast_data(self) -> Dict[str, Any]:
        """Get production forecast data."""
        # Placeholder for forecast data
        return {
            "next_24h_production": 0,
            "next_7d_production": 0,
            "forecast_accuracy": 0,
            "forecast_data": []
        }

    async def _generate_production_chart(self) -> Dict[str, Any]:
        """Generate production chart data."""
        # Aggregate recent production data
        chart_data = {"labels": [], "datasets": []}

        # Get last 24 hours of data
        end_time = asyncio.get_event_loop().time()
        start_time = end_time - (24 * 3600)

        # Group by hour
        hourly_data = {}
        for source_id, records in self.marketplace.production_history.items():
            for record in records:
                if start_time <= record["timestamp"] <= end_time:
                    hour = int(record["timestamp"] // 3600)
                    if hour not in hourly_data:
                        hourly_data[hour] = 0
                    hourly_data[hour] += record.get("current_power", 0)

        # Sort and format
        sorted_hours = sorted(hourly_data.keys())
        chart_data["labels"] = [f"{h % 24}:00" for h in sorted_hours]
        chart_data["datasets"] = [{
            "label": "Production (kW)",
            "data": [hourly_data[h] for h in sorted_hours],
            "borderColor": "#4CAF50",
            "backgroundColor": "rgba(76, 175, 80, 0.1)"
        }]

        return chart_data

    async def _generate_price_chart(self) -> Dict[str, Any]:
        """Generate price chart data."""
        chart_data = {"labels": [], "datasets": []}

        # Use price history
        price_data = await self._get_price_history(hours=24)

        if price_data:
            # Use timestamps from first source
            first_source = next(iter(price_data.values()))
            timestamps = [t for t, _ in first_source]

            chart_data["labels"] = [datetime.fromtimestamp(t).strftime("%H:%M") for t in timestamps]

            for source_type, data in price_data.items():
                prices = [p for _, p in data]
                color = self.config["chart_colors"].get(source_type, "#999999")

                chart_data["datasets"].append({
                    "label": f"{source_type.title()} Price (€/kWh)",
                    "data": prices,
                    "borderColor": color,
                    "backgroundColor": "transparent"
                })

        return chart_data

    async def _generate_efficiency_chart(self) -> Dict[str, Any]:
        """Generate efficiency chart data."""
        # Placeholder efficiency chart
        chart_data = {
            "labels": ["Week 1", "Week 2", "Week 3", "Week 4"],
            "datasets": [{
                "label": "System Efficiency (%)",
                "data": [85, 87, 89, 91],
                "borderColor": "#2196F3",
                "backgroundColor": "rgba(33, 150, 243, 0.1)"
            }]
        }

        return chart_data

    def _render_template(self, template_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Render GUI template with data."""
        # In a real implementation, this would use a template engine
        # For now, return structured data that can be consumed by a frontend
        return {
            "template": template_name,
            "data": data,
            "timestamp": asyncio.get_event_loop().time()
        }

    def _render_error(self, title: str, message: str) -> Dict[str, Any]:
        """Render error page."""
        return {
            "template": "error.html",
            "data": {
                "title": title,
                "message": message,
                "timestamp": asyncio.get_event_loop().time()
            }
        }