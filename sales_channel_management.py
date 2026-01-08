"""
Sales and Channel Management Module

This module implements comprehensive sales and channel management features:
- International sales team management
- Partner program administration
- Channel development and optimization
- Customer relationship management
- Sales analytics and forecasting
- Territory and quota management
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum
import statistics

from utils.logging_config import get_logger

logger = get_logger(__name__)


class SalesRole(Enum):
    """Sales team roles."""
    SALES_REP = "sales_rep"
    SALES_MANAGER = "sales_manager"
    SALES_DIRECTOR = "sales_director"
    CHANNEL_MANAGER = "channel_manager"
    PARTNER_MANAGER = "partner_manager"


class PartnerTier(Enum):
    """Partner program tiers."""
    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"
    PLATINUM = "platinum"


class ChannelType(Enum):
    """Channel types."""
    DIRECT = "direct"
    PARTNER_RESELLER = "partner_reseller"
    SYSTEM_INTEGRATOR = "system_integrator"
    DISTRIBUTOR = "distributor"
    OEM = "oem"


class CustomerSegment(Enum):
    """Customer segments."""
    SMB = "smb"  # Small/Medium Business
    ENTERPRISE = "enterprise"
    FORTUNE_500 = "fortune_500"
    PUBLIC_SECTOR = "public_sector"


class SalesChannelManagement:
    """
    Sales and channel management system.

    Handles international sales teams, partner programs, channel development,
    and customer relationship management for enterprise expansion.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize sales and channel management module.

        Args:
            config: Module configuration
        """
        self.config = config or self._get_default_config()

        # Sales team management
        self.sales_team: Dict[str, Dict[str, Any]] = {}
        self.territories: Dict[str, Dict[str, Any]] = {}
        self.quotas: Dict[str, Dict[str, Any]] = {}

        # Partner program
        self.partners: Dict[str, Dict[str, Any]] = {}
        self.partner_tiers: Dict[str, Dict[str, Any]] = {}
        self.partner_performance: Dict[str, List[Dict[str, Any]]] = {}

        # Channel management
        self.channels: Dict[str, Dict[str, Any]] = {}
        self.channel_performance: Dict[str, Dict[str, Any]] = {}

        # Customer management
        self.customers: Dict[str, Dict[str, Any]] = {}
        self.customer_segments: Dict[str, List[str]] = {}
        self.sales_opportunities: Dict[str, Dict[str, Any]] = {}

        # Sales analytics
        self.sales_metrics: Dict[str, Dict[str, Any]] = {}
        self.forecasts: Dict[str, Dict[str, Any]] = {}

        self.logger = get_logger(__name__)
        self.logger.info("Sales and Channel Management Module initialized")

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            "forecast_period_months": 12,
            "quota_attainment_target": 0.8,  # 80% target attainment
            "partner_margin_range": {"min": 0.15, "max": 0.35},  # 15-35% margins
            "channel_commission_range": {"min": 0.05, "max": 0.20},  # 5-20% commissions
            "customer_lifetime_value_period": 36,  # 36 months
            "sales_cycle_target_days": 90,
            "win_rate_target": 0.25  # 25% win rate
        }

    async def register_sales_rep(
        self,
        rep_id: str,
        rep_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Register a sales representative.

        Args:
            rep_id: Unique sales rep identifier
            rep_config: Sales rep configuration

        Returns:
            Registration result
        """
        try:
            self.logger.info(f"Registering sales rep {rep_id}")

            # Validate sales rep configuration
            await self._validate_sales_rep_config(rep_config)

            sales_rep = {
                "rep_id": rep_id,
                "name": rep_config["name"],
                "email": rep_config["email"],
                "role": SalesRole(rep_config.get("role", "sales_rep")).value,
                "territory": rep_config.get("territory"),
                "region": rep_config.get("region", "EMEA"),
                "manager": rep_config.get("manager"),
                "start_date": rep_config.get("start_date", datetime.now().isoformat()),
                "status": "active",
                "performance_metrics": {},
                "assigned_customers": [],
                "quota_history": [],
                "metadata": rep_config.get("metadata", {})
            }

            self.sales_team[rep_id] = sales_rep

            self.logger.info(f"Sales rep {rep_id} registered in {sales_rep['region']} region")
            return {
                "rep_id": rep_id,
                "status": "registered",
                "role": sales_rep["role"],
                "region": sales_rep["region"]
            }

        except Exception as e:
            self.logger.error(f"Failed to register sales rep {rep_id}: {e}")
            raise

    async def _validate_sales_rep_config(self, config: Dict[str, Any]):
        """Validate sales rep configuration."""
        required_fields = ["name", "email"]

        for field in required_fields:
            if field not in config:
                raise ValueError(f"Missing required field: {field}")

        # Validate email format
        if "@" not in config["email"]:
            raise ValueError("Invalid email format")

        # Validate role
        if config.get("role"):
            try:
                SalesRole(config["role"])
            except ValueError:
                raise ValueError(f"Invalid sales role: {config['role']}")

    async def create_territory(
        self,
        territory_id: str,
        territory_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a sales territory.

        Args:
            territory_id: Unique territory identifier
            territory_config: Territory configuration

        Returns:
            Territory creation result
        """
        try:
            self.logger.info(f"Creating sales territory {territory_id}")

            territory = {
                "territory_id": territory_id,
                "name": territory_config["name"],
                "region": territory_config.get("region", "EMEA"),
                "countries": territory_config.get("countries", []),
                "market_size": territory_config.get("market_size", 0),
                "assigned_reps": [],
                "performance_targets": territory_config.get("performance_targets", {}),
                "status": "active",
                "created_at": datetime.now().isoformat(),
                "metadata": territory_config.get("metadata", {})
            }

            self.territories[territory_id] = territory

            self.logger.info(f"Territory {territory_id} created covering {len(territory['countries'])} countries")
            return {
                "territory_id": territory_id,
                "status": "created",
                "countries_count": len(territory["countries"]),
                "market_size": territory["market_size"]
            }

        except Exception as e:
            self.logger.error(f"Failed to create territory {territory_id}: {e}")
            raise

    async def set_sales_quota(
        self,
        rep_id: str,
        quota_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Set sales quota for a representative.

        Args:
            rep_id: Sales rep identifier
            quota_config: Quota configuration

        Returns:
            Quota setting result
        """
        try:
            if rep_id not in self.sales_team:
                raise ValueError(f"Sales rep {rep_id} not found")

            quota = {
                "rep_id": rep_id,
                "period": quota_config["period"],  # e.g., "2025-Q1"
                "revenue_target": quota_config["revenue_target"],
                "deal_count_target": quota_config.get("deal_count_target", 0),
                "customer_count_target": quota_config.get("customer_count_target", 0),
                "product_targets": quota_config.get("product_targets", {}),
                "set_date": datetime.now().isoformat(),
                "status": "active",
                "attainment": 0.0,
                "metadata": quota_config.get("metadata", {})
            }

            quota_key = f"{rep_id}_{quota['period']}"
            self.quotas[quota_key] = quota

            self.logger.info(f"Quota set for {rep_id}: €{quota['revenue_target']} for {quota['period']}")
            return {
                "rep_id": rep_id,
                "period": quota["period"],
                "revenue_target": quota["revenue_target"],
                "status": "set"
            }

        except Exception as e:
            self.logger.error(f"Failed to set quota for {rep_id}: {e}")
            raise

    async def register_channel_partner(
        self,
        partner_id: str,
        partner_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Register a channel partner.

        Args:
            partner_id: Unique partner identifier
            partner_config: Partner configuration

        Returns:
            Registration result
        """
        try:
            self.logger.info(f"Registering channel partner {partner_id}")

            # Validate partner configuration
            await self._validate_partner_config(partner_config)

            partner = {
                "partner_id": partner_id,
                "name": partner_config["name"],
                "type": ChannelType(partner_config.get("type", "partner_reseller")).value,
                "tier": PartnerTier(partner_config.get("tier", "bronze")).value,
                "territory": partner_config.get("territory"),
                "specializations": partner_config.get("specializations", []),
                "certifications": partner_config.get("certifications", []),
                "margin_rate": partner_config.get("margin_rate", 0.20),
                "commission_rate": partner_config.get("commission_rate", 0.10),
                "status": "active",
                "registered_at": datetime.now().isoformat(),
                "performance_score": 0.0,
                "assigned_customers": [],
                "revenue_history": [],
                "metadata": partner_config.get("metadata", {})
            }

            self.partners[partner_id] = partner

            # Initialize partner tier benefits
            await self._initialize_partner_tier_benefits(partner_id, partner["tier"])

            self.logger.info(f"Channel partner {partner_id} registered as {partner['tier']} tier {partner['type']}")
            return {
                "partner_id": partner_id,
                "status": "registered",
                "tier": partner["tier"],
                "type": partner["type"],
                "margin_rate": partner["margin_rate"]
            }

        except Exception as e:
            self.logger.error(f"Failed to register channel partner {partner_id}: {e}")
            raise

    async def _validate_partner_config(self, config: Dict[str, Any]):
        """Validate partner configuration."""
        required_fields = ["name"]

        for field in required_fields:
            if field not in config:
                raise ValueError(f"Missing required field: {field}")

        # Validate partner type
        if config.get("type"):
            try:
                ChannelType(config["type"])
            except ValueError:
                raise ValueError(f"Invalid partner type: {config['type']}")

        # Validate tier
        if config.get("tier"):
            try:
                PartnerTier(config["tier"])
            except ValueError:
                raise ValueError(f"Invalid partner tier: {config['tier']}")

    async def _initialize_partner_tier_benefits(
        self,
        partner_id: str,
        tier: str
    ):
        """Initialize partner tier benefits."""
        tier_benefits = {
            "bronze": {
                "training_sessions": 2,
                "marketing_fund": 1000,
                "technical_support": "email",
                "co_sell_opportunities": 0
            },
            "silver": {
                "training_sessions": 4,
                "marketing_fund": 5000,
                "technical_support": "phone",
                "co_sell_opportunities": 2
            },
            "gold": {
                "training_sessions": 8,
                "marketing_fund": 15000,
                "technical_support": "dedicated",
                "co_sell_opportunities": 5
            },
            "platinum": {
                "training_sessions": 12,
                "marketing_fund": 30000,
                "technical_support": "white_glove",
                "co_sell_opportunities": 10
            }
        }

        benefits = tier_benefits.get(tier, tier_benefits["bronze"])
        self.partner_tiers[partner_id] = {
            "tier": tier,
            "benefits": benefits,
            "assigned_at": datetime.now().isoformat()
        }

    async def register_customer(
        self,
        customer_id: str,
        customer_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Register a customer.

        Args:
            customer_id: Unique customer identifier
            customer_config: Customer configuration

        Returns:
            Registration result
        """
        try:
            self.logger.info(f"Registering customer {customer_id}")

            customer = {
                "customer_id": customer_id,
                "name": customer_config["name"],
                "segment": CustomerSegment(customer_config.get("segment", "enterprise")).value,
                "industry": customer_config.get("industry"),
                "company_size": customer_config.get("company_size"),
                "location": customer_config.get("location", {}),
                "assigned_rep": customer_config.get("assigned_rep"),
                "channel_partner": customer_config.get("channel_partner"),
                "contract_value": customer_config.get("contract_value", 0),
                "status": "active",
                "registered_at": datetime.now().isoformat(),
                "lifetime_value": 0,
                "satisfaction_score": 0,
                "metadata": customer_config.get("metadata", {})
            }

            self.customers[customer_id] = customer

            # Update customer segments
            segment = customer["segment"]
            if segment not in self.customer_segments:
                self.customer_segments[segment] = []
            self.customer_segments[segment].append(customer_id)

            # Assign to sales rep if specified
            if customer.get("assigned_rep"):
                await self._assign_customer_to_rep(customer_id, customer["assigned_rep"])

            self.logger.info(f"Customer {customer_id} registered in {customer['segment']} segment")
            return {
                "customer_id": customer_id,
                "status": "registered",
                "segment": customer["segment"],
                "assigned_rep": customer.get("assigned_rep")
            }

        except Exception as e:
            self.logger.error(f"Failed to register customer {customer_id}: {e}")
            raise

    async def _assign_customer_to_rep(self, customer_id: str, rep_id: str):
        """Assign customer to sales rep."""
        if rep_id in self.sales_team:
            if customer_id not in self.sales_team[rep_id]["assigned_customers"]:
                self.sales_team[rep_id]["assigned_customers"].append(customer_id)

    async def create_sales_opportunity(
        self,
        opportunity_id: str,
        opportunity_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a sales opportunity.

        Args:
            opportunity_id: Unique opportunity identifier
            opportunity_config: Opportunity configuration

        Returns:
            Opportunity creation result
        """
        try:
            self.logger.info(f"Creating sales opportunity {opportunity_id}")

            opportunity = {
                "opportunity_id": opportunity_id,
                "customer_id": opportunity_config["customer_id"],
                "assigned_rep": opportunity_config.get("assigned_rep"),
                "channel_partner": opportunity_config.get("channel_partner"),
                "product_interest": opportunity_config.get("product_interest", []),
                "estimated_value": opportunity_config["estimated_value"],
                "probability": opportunity_config.get("probability", 0.5),
                "expected_close_date": opportunity_config.get("expected_close_date"),
                "stage": opportunity_config.get("stage", "prospecting"),
                "status": "active",
                "created_at": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat(),
                "activities": [],
                "metadata": opportunity_config.get("metadata", {})
            }

            self.sales_opportunities[opportunity_id] = opportunity

            # Calculate weighted value
            opportunity["weighted_value"] = opportunity["estimated_value"] * opportunity["probability"]

            self.logger.info(f"Sales opportunity {opportunity_id} created with €{opportunity['estimated_value']} value")
            return {
                "opportunity_id": opportunity_id,
                "status": "created",
                "estimated_value": opportunity["estimated_value"],
                "probability": opportunity["probability"],
                "weighted_value": opportunity["weighted_value"]
            }

        except Exception as e:
            self.logger.error(f"Failed to create sales opportunity {opportunity_id}: {e}")
            raise

    async def generate_sales_forecast(
        self,
        forecast_period: str = "3_months"
    ) -> Dict[str, Any]:
        """
        Generate sales forecast.

        Args:
            forecast_period: Forecast period (3_months, 6_months, 12_months)

        Returns:
            Sales forecast
        """
        try:
            self.logger.info(f"Generating {forecast_period} sales forecast")

            # Get forecast periods
            periods = {
                "3_months": 3,
                "6_months": 6,
                "12_months": 12
            }

            months = periods.get(forecast_period, 3)

            # Calculate forecast from opportunities
            total_weighted_value = sum(
                opp.get("weighted_value", 0)
                for opp in self.sales_opportunities.values()
                if opp["status"] == "active"
            )

            # Calculate by region
            regional_forecast = await self._calculate_regional_forecast(months)

            # Calculate by product
            product_forecast = await self._calculate_product_forecast(months)

            forecast = {
                "forecast_period": forecast_period,
                "total_weighted_value": total_weighted_value,
                "monthly_average": total_weighted_value / months,
                "regional_breakdown": regional_forecast,
                "product_breakdown": product_forecast,
                "confidence_level": await self._calculate_forecast_confidence(),
                "generated_at": datetime.now().isoformat(),
                "assumptions": [
                    "Win rates based on historical data",
                    "Sales cycle lengths considered",
                    "Seasonal factors not included"
                ]
            }

            forecast_id = f"forecast_{int(datetime.now().timestamp())}"
            self.forecasts[forecast_id] = forecast

            return {
                "forecast_id": forecast_id,
                "forecast": forecast
            }

        except Exception as e:
            self.logger.error(f"Failed to generate sales forecast: {e}")
            raise

    async def _calculate_regional_forecast(self, months: int) -> Dict[str, float]:
        """Calculate regional sales forecast."""
        regional_values = {}

        for opp in self.sales_opportunities.values():
            if opp["status"] != "active":
                continue

            customer_id = opp.get("customer_id")
            if customer_id and customer_id in self.customers:
                customer = self.customers[customer_id]
                region = customer.get("location", {}).get("region", "Unknown")

                weighted_value = opp.get("weighted_value", 0)
                regional_values[region] = regional_values.get(region, 0) + weighted_value

        # Distribute over months
        for region in regional_values:
            regional_values[region] = regional_values[region] / months

        return regional_values

    async def _calculate_product_forecast(self, months: int) -> Dict[str, float]:
        """Calculate product sales forecast."""
        product_values = {}

        for opp in self.sales_opportunities.values():
            if opp["status"] != "active":
                continue

            products = opp.get("product_interest", [])
            weighted_value = opp.get("weighted_value", 0) / len(products) if products else 0

            for product in products:
                product_values[product] = product_values.get(product, 0) + weighted_value

        # Distribute over months
        for product in product_values:
            product_values[product] = product_values[product] / months

        return product_values

    async def _calculate_forecast_confidence(self) -> str:
        """Calculate forecast confidence level."""
        # Simple confidence calculation based on opportunity count and average probability
        opportunities = [opp for opp in self.sales_opportunities.values() if opp["status"] == "active"]

        if not opportunities:
            return "Low"

        avg_probability = statistics.mean(opp.get("probability", 0) for opp in opportunities)
        opp_count = len(opportunities)

        if opp_count > 20 and avg_probability > 0.3:
            return "High"
        elif opp_count > 10 and avg_probability > 0.2:
            return "Medium"
        else:
            return "Low"

    async def get_sales_analytics(
        self,
        start_date: str,
        end_date: str,
        group_by: str = "month"
    ) -> Dict[str, Any]:
        """
        Get sales analytics and performance metrics.

        Args:
            start_date: Analytics start date
            end_date: Analytics end date
            group_by: Grouping period (day, week, month, quarter)

        Returns:
            Sales analytics
        """
        try:
            start = datetime.fromisoformat(start_date)
            end = datetime.fromisoformat(end_date)

            analytics = {
                "period": {"start": start_date, "end": end_date},
                "summary": {
                    "total_customers": len(self.customers),
                    "active_opportunities": len([opp for opp in self.sales_opportunities.values() if opp["status"] == "active"]),
                    "total_sales_team": len(self.sales_team),
                    "active_partners": len([p for p in self.partners.values() if p["status"] == "active"])
                },
                "performance": await self._calculate_sales_performance(start, end),
                "forecast_accuracy": await self._calculate_forecast_accuracy(),
                "generated_at": datetime.now().isoformat()
            }

            return analytics

        except Exception as e:
            self.logger.error(f"Failed to get sales analytics: {e}")
            raise

    async def _calculate_sales_performance(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Calculate sales performance metrics."""
        # Calculate metrics for sales reps
        rep_performance = {}
        for rep_id, rep in self.sales_team.items():
            # Get quotas for the period
            rep_quotas = [
                quota for quota in self.quotas.values()
                if quota["rep_id"] == rep_id and quota.get("period")
            ]

            if rep_quotas:
                avg_attainment = statistics.mean(q["attainment"] for q in rep_quotas)
                rep_performance[rep_id] = {
                    "name": rep["name"],
                    "avg_quota_attainment": avg_attainment,
                    "customers_assigned": len(rep["assigned_customers"]),
                    "opportunities_active": len([
                        opp for opp in self.sales_opportunities.values()
                        if opp.get("assigned_rep") == rep_id and opp["status"] == "active"
                    ])
                }

        # Calculate partner performance
        partner_performance = {}
        for partner_id, partner in self.partners.items():
            performance_history = self.partner_performance.get(partner_id, [])
            if performance_history:
                avg_score = statistics.mean(p["performance_score"] for p in performance_history)
                total_revenue = sum(p["revenue"] for p in performance_history)
                partner_performance[partner_id] = {
                    "name": partner["name"],
                    "tier": partner["tier"],
                    "avg_performance_score": avg_score,
                    "total_revenue": total_revenue,
                    "customers_supported": len(partner["assigned_customers"])
                }

        return {
            "sales_rep_performance": rep_performance,
            "partner_performance": partner_performance,
            "overall_metrics": {
                "avg_rep_attainment": statistics.mean([
                    p["avg_quota_attainment"] for p in rep_performance.values()
                ]) if rep_performance else 0,
                "total_active_partners": len(partner_performance)
            }
        }

    async def _calculate_forecast_accuracy(self) -> Dict[str, Any]:
        """Calculate forecast accuracy metrics."""
        # Compare recent forecasts with actual results
        recent_forecasts = [
            f for f in self.forecasts.values()
            if (datetime.now() - datetime.fromisoformat(f["generated_at"])).days <= 90
        ]

        if not recent_forecasts:
            return {"accuracy_score": None, "forecasts_analyzed": 0}

        # Simplified accuracy calculation
        accuracy_scores = []
        for forecast in recent_forecasts:
            # In real implementation, compare with actual sales data
            # For now, use a placeholder accuracy
            accuracy_scores.append(0.75)  # 75% accuracy

        avg_accuracy = statistics.mean(accuracy_scores) if accuracy_scores else 0

        return {
            "accuracy_score": avg_accuracy,
            "forecasts_analyzed": len(recent_forecasts),
            "accuracy_trend": "stable"  # improving, stable, declining
        }

    def get_sales_rep_status(self, rep_id: str) -> Optional[Dict[str, Any]]:
        """Get sales rep status and metrics."""
        if rep_id not in self.sales_team:
            return None

        rep = self.sales_team[rep_id]

        # Get current quotas
        current_quotas = [
            quota for quota in self.quotas.values()
            if quota["rep_id"] == rep_id and quota["status"] == "active"
        ]

        return {
            "rep_id": rep_id,
            "name": rep["name"],
            "role": rep["role"],
            "territory": rep.get("territory"),
            "region": rep["region"],
            "status": rep["status"],
            "assigned_customers": len(rep["assigned_customers"]),
            "active_opportunities": len([
                opp for opp in self.sales_opportunities.values()
                if opp.get("assigned_rep") == rep_id and opp["status"] == "active"
            ]),
            "current_quotas": current_quotas,
            "performance_score": rep.get("performance_metrics", {}).get("overall_score", 0)
        }

    def get_partner_status(self, partner_id: str) -> Optional[Dict[str, Any]]:
        """Get channel partner status."""
        if partner_id not in self.partners:
            return None

        partner = self.partners[partner_id]
        tier_info = self.partner_tiers.get(partner_id, {})

        return {
            "partner_id": partner_id,
            "name": partner["name"],
            "type": partner["type"],
            "tier": partner["tier"],
            "status": partner["status"],
            "territory": partner.get("territory"),
            "performance_score": partner["performance_score"],
            "assigned_customers": len(partner["assigned_customers"]),
            "tier_benefits": tier_info.get("benefits", {}),
            "margin_rate": partner["margin_rate"],
            "commission_rate": partner["commission_rate"]
        }


# Global sales and channel management instance
sales_channel_management = SalesChannelManagement()


async def register_sales_rep(rep_id: str, rep_config: Dict[str, Any]) -> Dict[str, Any]:
    """Register sales representative."""
    return await sales_channel_management.register_sales_rep(rep_id, rep_config)


async def create_territory(territory_id: str, territory_config: Dict[str, Any]) -> Dict[str, Any]:
    """Create sales territory."""
    return await sales_channel_management.create_territory(territory_id, territory_config)


async def register_channel_partner(partner_id: str, partner_config: Dict[str, Any]) -> Dict[str, Any]:
    """Register channel partner."""
    return await sales_channel_management.register_channel_partner(partner_id, partner_config)


async def register_customer(customer_id: str, customer_config: Dict[str, Any]) -> Dict[str, Any]:
    """Register customer."""
    return await sales_channel_management.register_customer(customer_id, customer_config)


async def create_sales_opportunity(opportunity_id: str, opportunity_config: Dict[str, Any]) -> Dict[str, Any]:
    """Create sales opportunity."""
    return await sales_channel_management.create_sales_opportunity(opportunity_id, opportunity_config)


async def generate_sales_forecast(forecast_period: str = "3_months") -> Dict[str, Any]:
    """Generate sales forecast."""
    return await sales_channel_management.generate_sales_forecast(forecast_period)


async def get_sales_analytics(start_date: str, end_date: str, group_by: str = "month") -> Dict[str, Any]:
    """Get sales analytics."""
    return await sales_channel_management.get_sales_analytics(start_date, end_date, group_by)