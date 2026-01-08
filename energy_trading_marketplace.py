"""
Energy Trading Marketplace Module

This module implements a marketplace for trading renewable energy from various sources
including solar panels, wind turbines, and hydro turbines. It supports multi-location
energy production and trading with different electricity providers.
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional, Tuple, Union
from datetime import datetime, timedelta
from enum import Enum

from utils.logging_config import get_logger

logger = get_logger(__name__)


class EnergySource(Enum):
    """Types of renewable energy sources."""
    SOLAR = "solar"
    WIND = "wind"
    HYDRO = "hydro"
    BIOMASS = "biomass"
    GEOTHERMAL = "geothermal"


class TradingStatus(Enum):
    """Trading transaction statuses."""
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


class EnergyTradingError(Exception):
    """Base exception for energy trading errors."""
    pass


class InsufficientEnergyError(EnergyTradingError):
    """Raised when insufficient energy is available for trading."""
    pass


class InvalidPriceError(EnergyTradingError):
    """Raised when energy price is invalid."""
    pass


class EnergyTradingMarketplace:
    """
    Energy Trading Marketplace for renewable energy sources.

    Provides comprehensive energy trading capabilities including:
    - Multi-source energy production tracking
    - Dynamic pricing and market mechanisms
    - Multi-location energy park management
    - Provider trading and settlement
    - Real-time energy balancing
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Energy Trading Marketplace.

        Args:
            config: Configuration dictionary
        """
        self.config = config or self._get_default_config()
        self.logger = get_logger(__name__)

        # Energy production tracking
        self.energy_sources: Dict[str, Dict[str, Any]] = {}
        self.energy_parks: Dict[str, Dict[str, Any]] = {}
        self.production_history: Dict[str, List[Dict[str, Any]]] = {}

        # Trading marketplace
        self.energy_offers: Dict[str, Dict[str, Any]] = {}
        self.active_trades: Dict[str, Dict[str, Any]] = {}
        self.completed_trades: List[Dict[str, Any]] = []

        # Provider management
        self.energy_providers: Dict[str, Dict[str, Any]] = {}
        self.provider_contracts: Dict[str, Dict[str, Any]] = {}

        # P2P Consumer management
        self.energy_consumers: Dict[str, Dict[str, Any]] = {}
        self.consumer_wallets: Dict[str, Dict[str, Any]] = {}
        self.consumer_devices: Dict[str, Dict[str, Any]] = {}  # Smart meters, EVs, etc.

        # Market data
        self.market_prices: Dict[str, List[Dict[str, Any]]] = {}
        self.price_history: Dict[str, List[float]] = {}

        # Settlement and billing
        self.settlements: Dict[str, Dict[str, Any]] = {}
        self.billing_cycles: Dict[str, Dict[str, Any]] = {}

        # International markets support
        self.supported_currencies: Dict[str, Dict[str, Any]] = {}
        self.market_regulations: Dict[str, Dict[str, Any]] = {}
        self.cross_border_routes: Dict[str, List[Dict[str, Any]]] = {}
        self.exchange_rates: Dict[str, float] = {}

        # Background tasks
        self.monitoring_task: Optional[asyncio.Task] = None
        self.settlement_task: Optional[asyncio.Task] = None

        # Initialize international market support
        self._initialize_international_markets()

        self.logger.info("Energy Trading Marketplace initialized")

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            "default_currency": "EUR",
            "price_update_interval": 300,  # 5 minutes
            "settlement_interval": 3600,   # 1 hour
            "minimum_trade_amount": 1.0,   # kWh
            "maximum_trade_amount": 10000.0,  # kWh
            "price_volatility_limit": 0.5,  # 50% max change
            "contract_duration_days": 365,  # 1 year
            "billing_cycle_days": 30,       # Monthly billing
            "grid_connection_fee": 0.01,    # EUR/kWh
            "transmission_loss_factor": 0.05,  # 5% loss
            "renewable_energy_bonus": 0.02,   # EUR/kWh bonus
            "monitoring_enabled": True,
            "supported_markets": ["EU", "US", "UK", "DE", "FR", "ES"],
            "default_exchange_rate_api": "https://api.exchangerate-api.com/v4/latest/EUR"
        }

    def _initialize_international_markets(self):
        """Initialize international market configurations."""
        # Supported currencies
        self.supported_currencies = {
            "EUR": {"name": "Euro", "symbol": "€", "markets": ["EU", "DE", "FR", "ES", "IT", "NL"]},
            "USD": {"name": "US Dollar", "symbol": "$", "markets": ["US"]},
            "GBP": {"name": "British Pound", "symbol": "£", "markets": ["UK"]},
            "CHF": {"name": "Swiss Franc", "symbol": "CHF", "markets": ["CH"]},
            "SEK": {"name": "Swedish Krona", "symbol": "kr", "markets": ["SE"]},
            "NOK": {"name": "Norwegian Krone", "symbol": "kr", "markets": ["NO"]},
            "DKK": {"name": "Danish Krone", "symbol": "kr", "markets": ["DK"]},
            "PLN": {"name": "Polish Złoty", "symbol": "zł", "markets": ["PL"]},
            "CZK": {"name": "Czech Koruna", "symbol": "Kč", "markets": ["CZ"]}
        }

        # Market regulations
        self.market_regulations = {
            "EU": {
                "renewable_targets": 0.32,  # 32% renewable by 2030
                "carbon_price": 75.0,  # EUR/ton CO2
                "grid_codes": ["ENTSO-E"],
                "certificates": ["EUA", "GOO"],
                "taxes": {"vat_rate": 0.21, "energy_tax": 0.01}
            },
            "DE": {
                "renewable_targets": 0.65,  # 65% renewable
                "carbon_price": 55.0,
                "grid_codes": ["ENTSO-E", "VDE"],
                "certificates": ["EUA", "HKN"],
                "taxes": {"vat_rate": 0.19, "energy_tax": 0.02}
            },
            "FR": {
                "renewable_targets": 0.40,
                "carbon_price": 44.6,
                "grid_codes": ["ENTSO-E", "RTE"],
                "certificates": ["EUA"],
                "taxes": {"vat_rate": 0.20, "energy_tax": 0.01}
            },
            "ES": {
                "renewable_targets": 0.74,
                "carbon_price": 0.0,  # Temporary exemption
                "grid_codes": ["ENTSO-E", "REE"],
                "certificates": ["EUA"],
                "taxes": {"vat_rate": 0.21, "energy_tax": 0.005}
            },
            "UK": {
                "renewable_targets": 0.40,
                "carbon_price": 22.0,
                "grid_codes": ["National Grid"],
                "certificates": ["ROC"],
                "taxes": {"vat_rate": 0.20, "energy_tax": 0.01}
            }
        }

        # Cross-border trading routes
        self.cross_border_routes = {
            "EU": [
                {"from": "DE", "to": "FR", "capacity": 50000, "latency_ms": 50},
                {"from": "DE", "to": "NL", "capacity": 30000, "latency_ms": 30},
                {"from": "FR", "to": "ES", "capacity": 25000, "latency_ms": 100},
                {"from": "ES", "to": "PT", "capacity": 15000, "latency_ms": 80}
            ]
        }

        # Initialize exchange rates (simplified)
        self.exchange_rates = {
            "EUR_USD": 1.08,
            "EUR_GBP": 0.85,
            "EUR_CHF": 0.95,
            "EUR_SEK": 11.5,
            "EUR_NOK": 11.8,
            "EUR_DKK": 7.45,
            "EUR_PLN": 4.3,
            "EUR_CZK": 24.5
        }

    async def register_energy_park(
        self,
        park_id: str,
        park_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Register a new energy park (solar, wind, hydro, etc.).

        Args:
            park_id: Unique park identifier
            park_config: Park configuration

        Returns:
            Registration result
        """
        try:
            self.logger.info(f"Registering energy park {park_id}")

            # Validate configuration
            await self._validate_park_config(park_config)

            # Create park record
            park = {
                "park_id": park_id,
                "name": park_config.get("name", park_id),
                "location": park_config["location"],
                "energy_sources": park_config["energy_sources"],
                "total_capacity": park_config["total_capacity"],  # kW
                "grid_connection": park_config.get("grid_connection", "connected"),
                "status": "active",
                "registered_at": time.time(),
                "last_updated": time.time(),
                "certificates": park_config.get("certificates", []),  # Green certificates
                "metadata": park_config.get("metadata", {})
            }

            # Initialize production tracking
            self.energy_parks[park_id] = park
            self.production_history[park_id] = []

            # Register individual energy sources
            for source_config in park_config["energy_sources"]:
                source_id = f"{park_id}_{source_config['type']}_{source_config['id']}"
                await self.register_energy_source(source_id, source_config, park_id)

            self.logger.info(f"Energy park {park_id} registered with {len(park_config['energy_sources'])} sources")
            return {
                "park_id": park_id,
                "status": "registered",
                "sources_registered": len(park_config["energy_sources"]),
                "total_capacity": park["total_capacity"]
            }

        except Exception as e:
            self.logger.error(f"Failed to register energy park {park_id}: {e}")
            raise EnergyTradingError(f"Park registration failed: {e}") from e

    async def _validate_park_config(self, config: Dict[str, Any]) -> None:
        """Validate energy park configuration."""
        required_fields = ["location", "energy_sources", "total_capacity"]

        for field in required_fields:
            if field not in config:
                raise ValueError(f"Missing required field: {field}")

        if not config["energy_sources"]:
            raise ValueError("At least one energy source must be specified")

        total_capacity = 0
        for source in config["energy_sources"]:
            if "capacity" not in source:
                raise ValueError("Each energy source must have capacity specified")
            total_capacity += source["capacity"]

        if abs(config["total_capacity"] - total_capacity) > 0.1:  # 0.1 kW tolerance
            raise ValueError("Total capacity doesn't match sum of source capacities")

    async def register_energy_source(
        self,
        source_id: str,
        source_config: Dict[str, Any],
        park_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Register an individual energy source.

        Args:
            source_id: Unique source identifier
            source_config: Source configuration
            park_id: Associated park ID

        Returns:
            Registration result
        """
        try:
            # Validate source type
            source_type = source_config.get("type", "").upper()
            if source_type not in [e.value for e in EnergySource]:
                raise ValueError(f"Invalid energy source type: {source_type}")

            source = {
                "source_id": source_id,
                "type": EnergySource(source_type.lower()),
                "capacity": source_config["capacity"],  # kW
                "efficiency": source_config.get("efficiency", 1.0),
                "location": source_config.get("location", {}),
                "park_id": park_id,
                "status": "active",
                "installed_at": source_config.get("installed_at", time.time()),
                "last_maintenance": source_config.get("last_maintenance"),
                "expected_lifetime": source_config.get("expected_lifetime", 25),  # years
                "current_production": 0.0,  # kW
                "total_production": 0.0,    # kWh lifetime
                "metadata": source_config.get("metadata", {})
            }

            self.energy_sources[source_id] = source
            self.production_history[source_id] = []

            self.logger.info(f"Energy source {source_id} registered: {source_type} {source_config['capacity']}kW")
            return {
                "source_id": source_id,
                "status": "registered",
                "type": source_type,
                "capacity": source_config["capacity"]
            }

        except Exception as e:
            self.logger.error(f"Failed to register energy source {source_id}: {e}")
            raise EnergyTradingError(f"Source registration failed: {e}") from e

    async def register_energy_provider(
        self,
        provider_id: str,
        provider_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Register an electricity provider/buyer.

        Args:
            provider_id: Unique provider identifier
            provider_config: Provider configuration

        Returns:
            Registration result
        """
        try:
            self.logger.info(f"Registering energy provider {provider_id}")

            provider = {
                "provider_id": provider_id,
                "name": provider_config.get("name", provider_id),
                "type": provider_config.get("type", "utility"),  # utility, industrial, commercial
                "buying_capacity": provider_config.get("buying_capacity", 1000),  # kW
                "preferred_sources": provider_config.get("preferred_sources", []),  # renewable preferences
                "contract_terms": provider_config.get("contract_terms", {}),
                "pricing_model": provider_config.get("pricing_model", "fixed"),  # fixed, dynamic, auction
                "status": "active",
                "registered_at": time.time(),
                "total_purchased": 0.0,  # kWh
                "active_contracts": [],
                "payment_terms": provider_config.get("payment_terms", {}),
                "metadata": provider_config.get("metadata", {})
            }

            self.energy_providers[provider_id] = provider

            self.logger.info(f"Energy provider {provider_id} registered")
            return {
                "provider_id": provider_id,
                "status": "registered",
                "buying_capacity": provider["buying_capacity"]
            }

        except Exception as e:
            self.logger.error(f"Failed to register energy provider {provider_id}: {e}")
            raise EnergyTradingError(f"Provider registration failed: {e}") from e

    async def register_energy_consumer(
        self,
        consumer_id: str,
        consumer_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Register an energy consumer for P2P trading.

        Args:
            consumer_id: Unique consumer identifier
            consumer_config: Consumer configuration

        Returns:
            Registration result
        """
        try:
            self.logger.info(f"Registering energy consumer {consumer_id}")

            consumer = {
                "consumer_id": consumer_id,
                "name": consumer_config.get("name", consumer_id),
                "email": consumer_config.get("email"),
                "phone": consumer_config.get("phone"),
                "address": consumer_config.get("address", {}),
                "type": consumer_config.get("type", "residential"),  # residential, commercial, industrial
                "consumption_capacity": consumer_config.get("consumption_capacity", 10),  # kW
                "preferred_sources": consumer_config.get("preferred_sources", ["solar", "wind"]),  # renewable preferences
                "devices": consumer_config.get("devices", []),  # smart meters, EVs, etc.
                "status": "active",
                "registered_at": time.time(),
                "total_consumed": 0.0,  # kWh
                "total_spent": 0.0,     # EUR
                "reputation_score": 1.0,
                "payment_methods": consumer_config.get("payment_methods", []),
                "metadata": consumer_config.get("metadata", {})
            }

            self.energy_consumers[consumer_id] = consumer

            # Create consumer wallet
            wallet = {
                "consumer_id": consumer_id,
                "balance": 0.0,
                "currency": self.config["default_currency"],
                "transactions": [],
                "created_at": time.time()
            }
            self.consumer_wallets[consumer_id] = wallet

            # Register consumer devices
            for device_config in consumer_config.get("devices", []):
                device_id = f"{consumer_id}_{device_config['type']}_{device_config['id']}"
                await self.register_consumer_device(device_id, device_config, consumer_id)

            self.logger.info(f"Energy consumer {consumer_id} registered with {len(consumer_config.get('devices', []))} devices")
            return {
                "consumer_id": consumer_id,
                "status": "registered",
                "wallet_balance": wallet["balance"],
                "devices_registered": len(consumer_config.get("devices", []))
            }

        except Exception as e:
            self.logger.error(f"Failed to register energy consumer {consumer_id}: {e}")
            raise EnergyTradingError(f"Consumer registration failed: {e}") from e

    async def register_consumer_device(
        self,
        device_id: str,
        device_config: Dict[str, Any],
        consumer_id: str
    ) -> Dict[str, Any]:
        """
        Register a consumer device (smart meter, EV, etc.).

        Args:
            device_id: Unique device identifier
            device_config: Device configuration
            consumer_id: Associated consumer ID

        Returns:
            Registration result
        """
        try:
            device = {
                "device_id": device_id,
                "consumer_id": consumer_id,
                "type": device_config["type"],  # smart_meter, electric_vehicle, battery, etc.
                "model": device_config.get("model", "unknown"),
                "capacity": device_config.get("capacity", 0),  # kW or kWh
                "current_consumption": 0.0,  # kW
                "total_consumption": 0.0,    # kWh
                "status": "active",
                "location": device_config.get("location", {}),
                "installation_date": device_config.get("installation_date", time.time()),
                "last_reading": None,
                "metadata": device_config.get("metadata", {})
            }

            self.consumer_devices[device_id] = device

            self.logger.info(f"Consumer device {device_id} registered: {device_config['type']}")
            return {
                "device_id": device_id,
                "status": "registered",
                "type": device["type"],
                "capacity": device["capacity"]
            }

        except Exception as e:
            self.logger.error(f"Failed to register consumer device {device_id}: {e}")
            raise EnergyTradingError(f"Device registration failed: {e}") from e

    async def update_production_data(
        self,
        source_id: str,
        production_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update production data for an energy source.

        Args:
            source_id: Source identifier
            production_data: Production metrics

        Returns:
            Update result
        """
        try:
            if source_id not in self.energy_sources:
                raise ValueError(f"Energy source {source_id} not found")

            source = self.energy_sources[source_id]
            timestamp = production_data.get("timestamp", time.time())

            # Update current production
            current_production = production_data.get("current_power", 0.0)  # kW
            source["current_production"] = current_production

            # Calculate energy produced in this interval
            time_diff = timestamp - source.get("last_update", timestamp)
            if time_diff > 0:
                energy_produced = current_production * (time_diff / 3600)  # kWh
                source["total_production"] += energy_produced

            source["last_update"] = timestamp

            # Record in history
            history_record = {
                "timestamp": timestamp,
                "current_power": current_production,
                "energy_produced": energy_produced if 'energy_produced' in locals() else 0,
                "efficiency": production_data.get("efficiency", source["efficiency"]),
                "weather_conditions": production_data.get("weather", {}),
                "status": production_data.get("status", "normal")
            }

            self.production_history[source_id].append(history_record)

            # Keep only recent history (last 30 days)
            cutoff_time = timestamp - (30 * 24 * 3600)
            self.production_history[source_id] = [
                record for record in self.production_history[source_id]
                if record["timestamp"] > cutoff_time
            ]

            # Update park totals if applicable
            if source.get("park_id"):
                await self._update_park_production(source["park_id"])

            self.logger.debug(f"Updated production for {source_id}: {current_production}kW")
            return {
                "source_id": source_id,
                "current_production": current_production,
                "total_production": source["total_production"],
                "status": "updated"
            }

        except Exception as e:
            self.logger.error(f"Failed to update production data for {source_id}: {e}")
            raise EnergyTradingError(f"Production update failed: {e}") from e

    async def _update_park_production(self, park_id: str) -> None:
        """Update total production for an energy park."""
        if park_id not in self.energy_parks:
            return

        park = self.energy_parks[park_id]
        total_production = 0.0
        total_current = 0.0

        # Sum production from all sources in the park
        for source_id, source in self.energy_sources.items():
            if source.get("park_id") == park_id:
                total_production += source["total_production"]
                total_current += source["current_production"]

        park["total_production"] = total_production
        park["current_production"] = total_current
        park["last_updated"] = time.time()

    async def create_energy_offer(
        self,
        seller_id: str,
        offer_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create an energy trading offer.

        Args:
            seller_id: Seller identifier (park or source)
            offer_config: Offer configuration

        Returns:
            Offer creation result
        """
        try:
            offer_id = f"offer_{seller_id}_{int(time.time())}"

            # Validate offer
            await self._validate_energy_offer(seller_id, offer_config)

            offer = {
                "offer_id": offer_id,
                "seller_id": seller_id,
                "energy_amount": offer_config["energy_amount"],  # kWh
                "price_per_kwh": offer_config["price_per_kwh"],  # EUR/kWh
                "currency": offer_config.get("currency", self.config["default_currency"]),
                "energy_source": offer_config.get("energy_source", "mixed"),
                "location": offer_config.get("location", {}),
                "valid_from": offer_config.get("valid_from", time.time()),
                "valid_until": offer_config["valid_until"],
                "min_purchase": offer_config.get("min_purchase", self.config["minimum_trade_amount"]),
                "delivery_terms": offer_config.get("delivery_terms", {}),
                "certificates": offer_config.get("certificates", []),  # Green certificates
                "status": "active",
                "created_at": time.time(),
                "bids": [],
                "metadata": offer_config.get("metadata", {})
            }

            self.energy_offers[offer_id] = offer

            self.logger.info(f"Created energy offer {offer_id}: {offer_config['energy_amount']}kWh at {offer_config['price_per_kwh']} EUR/kWh")
            return {
                "offer_id": offer_id,
                "status": "created",
                "energy_amount": offer["energy_amount"],
                "price_per_kwh": offer["price_per_kwh"]
            }

        except Exception as e:
            self.logger.error(f"Failed to create energy offer for {seller_id}: {e}")
            raise EnergyTradingError(f"Offer creation failed: {e}") from e

    async def _validate_energy_offer(
        self,
        seller_id: str,
        offer_config: Dict[str, Any]
    ) -> None:
        """Validate energy offer parameters."""
        required_fields = ["energy_amount", "price_per_kwh", "valid_until"]

        for field in required_fields:
            if field not in offer_config:
                raise ValueError(f"Missing required field: {field}")

        # Validate amounts
        amount = offer_config["energy_amount"]
        if amount < self.config["minimum_trade_amount"] or amount > self.config["maximum_trade_amount"]:
            raise ValueError(f"Energy amount must be between {self.config['minimum_trade_amount']} and {self.config['maximum_trade_amount']} kWh")

        # Validate price
        price = offer_config["price_per_kwh"]
        if price <= 0:
            raise InvalidPriceError("Price must be positive")

        # Check if seller has sufficient energy
        available_energy = await self._get_available_energy(seller_id)
        if available_energy < amount:
            raise InsufficientEnergyError(f"Insufficient energy available: {available_energy} < {amount} kWh")

        # Validate time range
        valid_until = offer_config["valid_until"]
        if valid_until <= time.time():
            raise ValueError("Offer expiration time must be in the future")

    async def _get_available_energy(self, seller_id: str) -> float:
        """Get available energy for trading from seller."""
        # Check if it's a park or individual source
        if seller_id in self.energy_parks:
            return self.energy_parks[seller_id].get("current_production", 0) * 24  # Daily estimate
        elif seller_id in self.energy_sources:
            return self.energy_sources[seller_id].get("current_production", 0) * 24  # Daily estimate
        else:
            return 0.0

    async def place_bid_on_offer(
        self,
        offer_id: str,
        buyer_id: str,
        bid_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Place a bid on an energy offer.

        Args:
            offer_id: Offer identifier
            buyer_id: Buyer identifier
            bid_config: Bid configuration

        Returns:
            Bid placement result
        """
        try:
            if offer_id not in self.energy_offers:
                raise ValueError(f"Offer {offer_id} not found")

            offer = self.energy_offers[offer_id]

            # Validate bid
            await self._validate_bid(offer, buyer_id, bid_config)

            bid = {
                "bid_id": f"bid_{offer_id}_{buyer_id}_{int(time.time())}",
                "buyer_id": buyer_id,
                "energy_amount": bid_config["energy_amount"],
                "bid_price": bid_config["bid_price"],  # EUR/kWh
                "delivery_schedule": bid_config.get("delivery_schedule", {}),
                "payment_terms": bid_config.get("payment_terms", {}),
                "placed_at": time.time(),
                "status": "pending",
                "metadata": bid_config.get("metadata", {})
            }

            offer["bids"].append(bid)

            self.logger.info(f"Placed bid on offer {offer_id}: {bid_config['energy_amount']}kWh at {bid_config['bid_price']} EUR/kWh")
            return {
                "bid_id": bid["bid_id"],
                "status": "placed",
                "offer_id": offer_id,
                "energy_amount": bid["energy_amount"],
                "bid_price": bid["bid_price"]
            }

        except Exception as e:
            self.logger.error(f"Failed to place bid on offer {offer_id}: {e}")
            raise EnergyTradingError(f"Bid placement failed: {e}") from e

    async def _validate_bid(
        self,
        offer: Dict[str, Any],
        buyer_id: str,
        bid_config: Dict[str, Any]
    ) -> None:
        """Validate bid parameters."""
        required_fields = ["energy_amount", "bid_price"]

        for field in required_fields:
            if field not in bid_config:
                raise ValueError(f"Missing required field: {field}")

        amount = bid_config["energy_amount"]
        if amount < offer["min_purchase"] or amount > offer["energy_amount"]:
            raise ValueError(f"Bid amount must be between {offer['min_purchase']} and {offer['energy_amount']} kWh")

        # Check if buyer is registered
        if buyer_id not in self.energy_providers:
            raise ValueError(f"Buyer {buyer_id} not registered")

    async def execute_trade(
        self,
        offer_id: str,
        bid_id: str
    ) -> Dict[str, Any]:
        """
        Execute a trade between offer and bid.

        Args:
            offer_id: Offer identifier
            bid_id: Bid identifier

        Returns:
            Trade execution result
        """
        try:
            if offer_id not in self.energy_offers:
                raise ValueError(f"Offer {offer_id} not found")

            offer = self.energy_offers[offer_id]

            # Find the bid
            bid = None
            for b in offer["bids"]:
                if b["bid_id"] == bid_id:
                    bid = b
                    break

            if not bid:
                raise ValueError(f"Bid {bid_id} not found in offer {offer_id}")

            trade_id = f"trade_{offer_id}_{bid_id}_{int(time.time())}"

            # Create trade record
            trade = {
                "trade_id": trade_id,
                "offer_id": offer_id,
                "bid_id": bid_id,
                "seller_id": offer["seller_id"],
                "buyer_id": bid["buyer_id"],
                "energy_amount": bid["energy_amount"],
                "price_per_kwh": bid["bid_price"],
                "total_value": bid["energy_amount"] * bid["bid_price"],
                "currency": offer["currency"],
                "energy_source": offer["energy_source"],
                "delivery_schedule": bid["delivery_schedule"],
                "status": TradingStatus.ACTIVE.value,
                "executed_at": time.time(),
                "settlement_status": "pending",
                "delivery_status": "pending",
                "metadata": {
                    "offer_metadata": offer.get("metadata", {}),
                    "bid_metadata": bid.get("metadata", {})
                }
            }

            self.active_trades[trade_id] = trade

            # Update offer status
            offer["status"] = "partially_filled" if bid["energy_amount"] < offer["energy_amount"] else "filled"

            # Update provider totals
            if bid["buyer_id"] in self.energy_providers:
                self.energy_providers[bid["buyer_id"]]["total_purchased"] += bid["energy_amount"]

            self.logger.info(f"Executed trade {trade_id}: {bid['energy_amount']}kWh for {trade['total_value']} {trade['currency']}")
            return {
                "trade_id": trade_id,
                "status": "executed",
                "energy_amount": trade["energy_amount"],
                "total_value": trade["total_value"],
                "currency": trade["currency"]
            }

        except Exception as e:
            self.logger.error(f"Failed to execute trade {offer_id}/{bid_id}: {e}")
            raise EnergyTradingError(f"Trade execution failed: {e}") from e

    async def create_micro_offer(
        self,
        seller_id: str,
        offer_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a micro energy offer for P2P trading (small amounts).

        Args:
            seller_id: Seller identifier (consumer with excess energy)
            offer_config: Micro offer configuration

        Returns:
            Offer creation result
        """
        try:
            # Validate micro offer (smaller amounts, shorter validity)
            if offer_config.get("energy_amount", 0) > 50:  # Max 50kWh for micro offers
                raise ValueError("Micro offers cannot exceed 50kWh")

            offer_config["valid_until"] = min(
                offer_config.get("valid_until", time.time() + 3600),  # Max 1 hour validity
                time.time() + 3600
            )

            offer_config["min_purchase"] = max(
                offer_config.get("min_purchase", 0.1),  # Min 0.1kWh
                0.1
            )

            # Create standard offer
            result = await self.create_energy_offer(seller_id, offer_config)

            # Mark as micro offer
            offer_id = result["offer_id"]
            self.energy_offers[offer_id]["is_micro"] = True
            self.energy_offers[offer_id]["micro_category"] = "p2p"

            self.logger.info(f"Created micro energy offer {offer_id}: {offer_config['energy_amount']}kWh")
            return result

        except Exception as e:
            self.logger.error(f"Failed to create micro offer for {seller_id}: {e}")
            raise EnergyTradingError(f"Micro offer creation failed: {e}") from e

    async def create_micro_bid(
        self,
        offer_id: str,
        buyer_id: str,
        bid_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a micro bid for P2P trading.

        Args:
            offer_id: Offer identifier
            buyer_id: Buyer identifier (consumer)
            bid_config: Micro bid configuration

        Returns:
            Bid creation result
        """
        try:
            # Validate micro bid
            if bid_config.get("energy_amount", 0) > 50:  # Max 50kWh for micro bids
                raise ValueError("Micro bids cannot exceed 50kWh")

            # Create standard bid
            result = await self.place_bid_on_offer(offer_id, buyer_id, bid_config)

            # Mark as micro bid
            bid_id = result["bid_id"]
            offer = self.energy_offers[offer_id]
            for bid in offer["bids"]:
                if bid["bid_id"] == bid_id:
                    bid["is_micro"] = True
                    bid["micro_category"] = "p2p"
                    break

            self.logger.info(f"Created micro bid {bid_id} on offer {offer_id}")
            return result

        except Exception as e:
            self.logger.error(f"Failed to create micro bid for {buyer_id}: {e}")
            raise EnergyTradingError(f"Micro bid creation failed: {e}") from e

    async def execute_micro_trade(
        self,
        offer_id: str,
        bid_id: str
    ) -> Dict[str, Any]:
        """
        Execute a micro P2P trade with instant settlement.

        Args:
            offer_id: Offer identifier
            bid_id: Bid identifier

        Returns:
            Trade execution result
        """
        try:
            # Execute standard trade
            result = await self.execute_trade(offer_id, bid_id)

            # Mark as micro trade
            trade_id = result["trade_id"]
            self.active_trades[trade_id]["is_micro"] = True
            self.active_trades[trade_id]["micro_category"] = "p2p"

            # Process instant settlement for micro trades
            await self._process_micro_settlement(trade_id)

            self.logger.info(f"Executed micro trade {trade_id}")
            return result

        except Exception as e:
            self.logger.error(f"Failed to execute micro trade {offer_id}/{bid_id}: {e}")
            raise EnergyTradingError(f"Micro trade execution failed: {e}") from e

    async def _process_micro_settlement(self, trade_id: str) -> None:
        """
        Process instant settlement for micro trades.

        Args:
            trade_id: Trade identifier
        """
        try:
            trade = self.active_trades[trade_id]

            # Transfer energy tokens (simplified)
            seller_id = trade["seller_id"]
            buyer_id = trade["buyer_id"]
            energy_amount = trade["energy_amount"]
            total_value = trade["total_value"]

            # Update consumer wallets
            if buyer_id in self.consumer_wallets:
                self.consumer_wallets[buyer_id]["balance"] -= total_value
                self.consumer_wallets[buyer_id]["transactions"].append({
                    "type": "purchase",
                    "trade_id": trade_id,
                    "amount": -total_value,
                    "energy_amount": energy_amount,
                    "timestamp": time.time()
                })

            if seller_id in self.consumer_wallets:
                self.consumer_wallets[seller_id]["balance"] += total_value
                self.consumer_wallets[seller_id]["transactions"].append({
                    "type": "sale",
                    "trade_id": trade_id,
                    "amount": total_value,
                    "energy_amount": energy_amount,
                    "timestamp": time.time()
                })

            # Update consumer totals
            if buyer_id in self.energy_consumers:
                self.energy_consumers[buyer_id]["total_consumed"] += energy_amount
                self.energy_consumers[buyer_id]["total_spent"] += total_value

            if seller_id in self.energy_consumers:
                self.energy_consumers[seller_id]["total_consumed"] -= energy_amount  # Net producer

            # Mark trade as settled
            trade["settlement_status"] = "completed"
            trade["settled_at"] = time.time()

            self.logger.info(f"Processed micro settlement for trade {trade_id}")

        except Exception as e:
            self.logger.error(f"Failed to process micro settlement for {trade_id}: {e}")

    # Smart Contract Implementation for Energy Trading

    async def create_energy_contract(
        self,
        contract_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a smart contract for energy trading.

        Args:
            contract_config: Contract configuration

        Returns:
            Contract creation result
        """
        try:
            contract_id = f"contract_{int(time.time())}"

            contract = {
                "contract_id": contract_id,
                "type": contract_config.get("type", "energy_trade"),
                "parties": contract_config["parties"],  # seller, buyer
                "terms": contract_config["terms"],      # energy amount, price, delivery terms
                "conditions": contract_config.get("conditions", {}),  # smart conditions
                "status": "pending",
                "created_at": time.time(),
                "executed_at": None,
                "settled_at": None,
                "blockchain_tx": None,  # For actual blockchain integration
                "metadata": contract_config.get("metadata", {})
            }

            # Validate contract
            await self._validate_energy_contract(contract)

            self.provider_contracts[contract_id] = contract

            self.logger.info(f"Created energy contract {contract_id}")
            return {
                "contract_id": contract_id,
                "status": "created",
                "parties": contract["parties"],
                "terms": contract["terms"]
            }

        except Exception as e:
            self.logger.error(f"Failed to create energy contract: {e}")
            raise EnergyTradingError(f"Contract creation failed: {e}") from e

    async def _validate_energy_contract(self, contract: Dict[str, Any]) -> None:
        """Validate energy contract terms."""
        required_fields = ["parties", "terms"]

        for field in required_fields:
            if field not in contract:
                raise ValueError(f"Missing required field: {field}")

        # Validate parties exist
        for party in contract["parties"]:
            party_id = party["id"]
            if party["role"] == "seller":
                if party_id not in self.energy_parks and party_id not in self.energy_consumers:
                    raise ValueError(f"Seller {party_id} not registered")
            elif party["role"] == "buyer":
                if party_id not in self.energy_providers and party_id not in self.energy_consumers:
                    raise ValueError(f"Buyer {party_id} not registered")

        # Validate terms
        terms = contract["terms"]
        if terms.get("energy_amount", 0) <= 0:
            raise ValueError("Energy amount must be positive")
        if terms.get("price_per_kwh", 0) <= 0:
            raise ValueError("Price must be positive")

    async def execute_contract(self, contract_id: str) -> Dict[str, Any]:
        """
        Execute a smart contract.

        Args:
            contract_id: Contract identifier

        Returns:
            Execution result
        """
        try:
            if contract_id not in self.provider_contracts:
                raise ValueError(f"Contract {contract_id} not found")

            contract = self.provider_contracts[contract_id]

            # Check conditions
            if not await self._check_contract_conditions(contract):
                raise ValueError("Contract conditions not met")

            # Execute contract
            contract["status"] = "executed"
            contract["executed_at"] = time.time()

            # Create trade from contract
            trade_result = await self._create_trade_from_contract(contract)

            self.logger.info(f"Executed energy contract {contract_id}")
            return {
                "contract_id": contract_id,
                "status": "executed",
                "trade_id": trade_result.get("trade_id"),
                "executed_at": contract["executed_at"]
            }

        except Exception as e:
            self.logger.error(f"Failed to execute contract {contract_id}: {e}")
            raise EnergyTradingError(f"Contract execution failed: {e}") from e

    async def _check_contract_conditions(self, contract: Dict[str, Any]) -> bool:
        """Check if contract conditions are met."""
        conditions = contract.get("conditions", {})

        # Check energy availability
        seller_id = None
        for party in contract["parties"]:
            if party["role"] == "seller":
                seller_id = party["id"]
                break

        if seller_id:
            available_energy = await self._get_available_energy(seller_id)
            required_energy = contract["terms"]["energy_amount"]
            if available_energy < required_energy:
                return False

        # Check payment conditions
        # In real implementation, check wallet balances, payment confirmations, etc.

        return True

    async def _create_trade_from_contract(self, contract: Dict[str, Any]) -> Dict[str, Any]:
        """Create a trade from an executed contract."""
        seller_id = None
        buyer_id = None

        for party in contract["parties"]:
            if party["role"] == "seller":
                seller_id = party["id"]
            elif party["role"] == "buyer":
                buyer_id = party["id"]

        offer_config = {
            "energy_amount": contract["terms"]["energy_amount"],
            "price_per_kwh": contract["terms"]["price_per_kwh"],
            "valid_until": time.time() + 3600,  # 1 hour
            "energy_source": contract["terms"].get("energy_source", "contract"),
            "delivery_terms": contract["terms"].get("delivery_terms", {})
        }

        # Create offer
        offer_result = await self.create_energy_offer(seller_id, offer_config)
        offer_id = offer_result["offer_id"]

        # Create bid
        bid_config = {
            "energy_amount": contract["terms"]["energy_amount"],
            "bid_price": contract["terms"]["price_per_kwh"],
            "delivery_schedule": contract["terms"].get("delivery_schedule", {})
        }

        bid_result = await self.place_bid_on_offer(offer_id, buyer_id, bid_config)
        bid_id = bid_result["bid_id"]

        # Execute trade
        trade_result = await self.execute_trade(offer_id, bid_id)

        return trade_result

    # International Markets Support

    async def create_cross_border_offer(
        self,
        seller_id: str,
        buyer_market: str,
        offer_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a cross-border energy trading offer.

        Args:
            seller_id: Seller identifier
            buyer_market: Target market code (e.g., 'DE', 'FR')
            offer_config: Offer configuration

        Returns:
            Offer creation result
        """
        try:
            # Validate cross-border requirements
            await self._validate_cross_border_offer(seller_id, buyer_market, offer_config)

            # Convert pricing to target market currency
            target_currency = self._get_market_currency(buyer_market)
            converted_price = await self._convert_currency(
                offer_config["price_per_kwh"],
                self.config["default_currency"],
                target_currency
            )

            # Apply cross-border fees and regulations
            final_price = await self._apply_cross_border_fees(
                converted_price, buyer_market, offer_config["energy_source"]
            )

            offer_config["original_price"] = offer_config["price_per_kwh"]
            offer_config["target_market"] = buyer_market
            offer_config["target_currency"] = target_currency
            offer_config["converted_price"] = final_price
            offer_config["price_per_kwh"] = final_price
            offer_config["currency"] = target_currency
            offer_config["cross_border"] = True

            # Create the offer
            result = await self.create_energy_offer(seller_id, offer_config)

            self.logger.info(f"Created cross-border offer from {seller_id} to {buyer_market}: {offer_config['energy_amount']}kWh")
            return result

        except Exception as e:
            self.logger.error(f"Failed to create cross-border offer: {e}")
            raise EnergyTradingError(f"Cross-border offer creation failed: {e}") from e

    async def _validate_cross_border_offer(
        self,
        seller_id: str,
        buyer_market: str,
        offer_config: Dict[str, Any]
    ) -> None:
        """Validate cross-border offer requirements."""
        # Check if markets are supported
        if buyer_market not in self.market_regulations:
            raise ValueError(f"Unsupported market: {buyer_market}")

        # Check cross-border route availability
        seller_market = self._get_entity_market(seller_id)
        if not self._has_cross_border_route(seller_market, buyer_market):
            raise ValueError(f"No cross-border route available between {seller_market} and {buyer_market}")

        # Check regulatory compliance
        await self._check_regulatory_compliance(buyer_market, offer_config)

    def _get_entity_market(self, entity_id: str) -> str:
        """Get the market code for an entity."""
        # Check if it's a park
        if entity_id in self.energy_parks:
            location = self.energy_parks[entity_id].get("location", {})
            return location.get("country", "EU")

        # Check if it's a consumer
        if entity_id in self.energy_consumers:
            address = self.energy_consumers[entity_id].get("address", {})
            return address.get("country", "EU")

        return "EU"  # Default

    def _has_cross_border_route(self, from_market: str, to_market: str) -> bool:
        """Check if cross-border route exists."""
        routes = self.cross_border_routes.get("EU", [])
        for route in routes:
            if route["from"] == from_market and route["to"] == to_market:
                return True
        return False

    async def _check_regulatory_compliance(
        self,
        market: str,
        offer_config: Dict[str, Any]
    ) -> None:
        """Check regulatory compliance for the target market."""
        regulations = self.market_regulations.get(market, {})

        # Check renewable targets
        if offer_config.get("energy_source") == "fossil":
            renewable_target = regulations.get("renewable_targets", 0)
            if renewable_target > 0.5:  # High renewable target markets
                raise ValueError(f"Market {market} has high renewable targets - fossil fuels not allowed")

        # Check certificates requirements
        required_certs = regulations.get("certificates", [])
        if required_certs and not offer_config.get("certificates"):
            raise ValueError(f"Market {market} requires certificates: {required_certs}")

    def _get_market_currency(self, market: str) -> str:
        """Get the currency for a market."""
        currency_map = {
            "EU": "EUR",
            "DE": "EUR",
            "FR": "EUR",
            "ES": "EUR",
            "UK": "GBP",
            "US": "USD",
            "CH": "CHF",
            "SE": "SEK",
            "NO": "NOK",
            "DK": "DKK",
            "PL": "PLN",
            "CZ": "CZK"
        }
        return currency_map.get(market, "EUR")

    async def _convert_currency(
        self,
        amount: float,
        from_currency: str,
        to_currency: str
    ) -> float:
        """Convert amount between currencies."""
        if from_currency == to_currency:
            return amount

        rate_key = f"{from_currency}_{to_currency}"
        rate = self.exchange_rates.get(rate_key, 1.0)

        # In real implementation, fetch live rates
        # For now, use static rates

        return amount * rate

    async def _apply_cross_border_fees(
        self,
        price: float,
        target_market: str,
        energy_source: str
    ) -> float:
        """Apply cross-border trading fees and adjustments."""
        # Base transmission fee
        transmission_fee = price * self.config["transmission_loss_factor"]

        # Regulatory fees
        regulations = self.market_regulations.get(target_market, {})
        energy_tax = regulations.get("taxes", {}).get("energy_tax", 0.01)
        tax_fee = price * energy_tax

        # Renewable bonus/penalty
        renewable_bonus = 0
        if energy_source in ["solar", "wind", "hydro"]:
            renewable_bonus = price * self.config["renewable_energy_bonus"]

        final_price = price + transmission_fee + tax_fee - renewable_bonus

        return round(final_price, 4)

    async def get_market_overview_international(self) -> Dict[str, Any]:
        """Get international market overview."""
        try:
            overview = await self.get_market_overview()

            # Add international market data
            international_data = {
                "supported_markets": list(self.market_regulations.keys()),
                "supported_currencies": list(self.supported_currencies.keys()),
                "cross_border_routes": self.cross_border_routes,
                "exchange_rates": self.exchange_rates,
                "market_regulations": self.market_regulations
            }

            overview["international"] = international_data
            return overview

        except Exception as e:
            self.logger.error(f"Failed to get international market overview: {e}")
            return {"error": str(e)}

    async def get_market_specific_data(self, market_code: str) -> Dict[str, Any]:
        """Get market-specific data and statistics."""
        try:
            if market_code not in self.market_regulations:
                raise ValueError(f"Unsupported market: {market_code}")

            # Get market-specific offers and trades
            market_offers = [
                offer for offer in self.energy_offers.values()
                if offer.get("target_market") == market_code or offer.get("location", {}).get("country") == market_code
            ]

            market_trades = [
                trade for trade in self.active_trades.values()
                if trade.get("target_market") == market_code
            ]

            # Calculate market statistics
            total_offered = sum(o["energy_amount"] for o in market_offers)
            total_traded = sum(t["energy_amount"] for t in market_trades)
            avg_price = sum(o["price_per_kwh"] for o in market_offers) / len(market_offers) if market_offers else 0

            return {
                "market_code": market_code,
                "regulations": self.market_regulations[market_code],
                "currency": self._get_market_currency(market_code),
                "statistics": {
                    "active_offers": len(market_offers),
                    "active_trades": len(market_trades),
                    "total_energy_offered": total_offered,
                    "total_energy_traded": total_traded,
                    "average_price": avg_price
                },
                "recent_offers": market_offers[-5:],  # Last 5 offers
                "recent_trades": market_trades[-5:]   # Last 5 trades
            }

        except Exception as e:
            self.logger.error(f"Failed to get market data for {market_code}: {e}")
            raise EnergyTradingError(f"Market data retrieval failed: {e}") from e

    # Localization Support

    def _initialize_localization(self):
        """Initialize localization data."""
        self.localizations = {
            "en": {
                "welcome": "Welcome to Energy Trading Platform",
                "offer_created": "Energy offer created successfully",
                "trade_executed": "Trade executed successfully",
                "insufficient_balance": "Insufficient wallet balance",
                "invalid_offer": "Invalid offer parameters"
            },
            "de": {
                "welcome": "Willkommen auf der Energiehandelsplattform",
                "offer_created": "Energieangebot erfolgreich erstellt",
                "trade_executed": "Handel erfolgreich ausgeführt",
                "insufficient_balance": "Unzureichendes Guthaben",
                "invalid_offer": "Ungültige Angebotsparameter"
            },
            "fr": {
                "welcome": "Bienvenue sur la plateforme de trading d'énergie",
                "offer_created": "Offre d'énergie créée avec succès",
                "trade_executed": "Échange exécuté avec succès",
                "insufficient_balance": "Solde insuffisant",
                "invalid_offer": "Paramètres d'offre invalides"
            },
            "es": {
                "welcome": "Bienvenido a la plataforma de comercio de energía",
                "offer_created": "Oferta de energía creada exitosamente",
                "trade_executed": "Comercio ejecutado exitosamente",
                "insufficient_balance": "Saldo insuficiente",
                "invalid_offer": "Parámetros de oferta inválidos"
            }
        }

        self.default_locale = "en"

    def get_localized_message(self, key: str, locale: str = None) -> str:
        """Get localized message."""
        if not hasattr(self, 'localizations'):
            self._initialize_localization()

        locale = locale or self.default_locale
        messages = self.localizations.get(locale, self.localizations[self.default_locale])
        return messages.get(key, self.localizations[self.default_locale].get(key, key))

    def format_currency_by_locale(self, amount: float, currency: str, locale: str = None) -> str:
        """Format currency according to locale."""
        locale = locale or self.default_locale

        # Currency symbols
        symbols = {
            "EUR": {"en": "€", "de": "€", "fr": "€", "es": "€"},
            "USD": {"en": "$", "de": "$", "fr": "$", "es": "$"},
            "GBP": {"en": "£", "de": "£", "fr": "£", "es": "£"}
        }

        symbol = symbols.get(currency, {}).get(locale, currency)

        if locale == "de":
            return f"{amount:.2f} {symbol}".replace(".", ",")
        elif locale == "fr":
            return f"{amount:.2f} {symbol}".replace(".", ",")
        elif locale == "es":
            return f"{symbol}{amount:.2f}".replace(".", ",")
        else:  # en
            return f"{symbol}{amount:.2f}"

    def get_supported_locales(self) -> List[str]:
        """Get list of supported locales."""
        if not hasattr(self, 'localizations'):
            self._initialize_localization()
        return list(self.localizations.keys())

    # Payment Processing Integration

    async def process_payment(
        self,
        trade_id: str,
        payment_method: str,
        payment_details: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process payment for an energy trade.

        Args:
            trade_id: Trade identifier
            payment_method: Payment method (wallet, card, bank, crypto)
            payment_details: Payment-specific details

        Returns:
            Payment processing result
        """
        try:
            if trade_id not in self.active_trades:
                raise ValueError(f"Trade {trade_id} not found")

            trade = self.active_trades[trade_id]

            # Route to appropriate payment processor
            if payment_method == "wallet":
                result = await self._process_wallet_payment(trade, payment_details)
            elif payment_method == "card":
                result = await self._process_card_payment(trade, payment_details)
            elif payment_method == "bank":
                result = await self._process_bank_payment(trade, payment_details)
            elif payment_method == "crypto":
                result = await self._process_crypto_payment(trade, payment_details)
            else:
                raise ValueError(f"Unsupported payment method: {payment_method}")

            # Update trade status
            if result["status"] == "completed":
                trade["payment_status"] = "completed"
                trade["payment_method"] = payment_method
                trade["payment_details"] = payment_details
                trade["paid_at"] = time.time()

            self.logger.info(f"Processed {payment_method} payment for trade {trade_id}")
            return result

        except Exception as e:
            self.logger.error(f"Failed to process payment for trade {trade_id}: {e}")
            raise EnergyTradingError(f"Payment processing failed: {e}") from e

    async def _process_wallet_payment(
        self,
        trade: Dict[str, Any],
        payment_details: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process wallet-to-wallet payment."""
        buyer_id = trade["buyer_id"]
        seller_id = trade["seller_id"]
        amount = trade["total_value"]

        # Check buyer balance
        if buyer_id not in self.consumer_wallets:
            raise ValueError(f"Buyer {buyer_id} has no wallet")

        buyer_wallet = self.consumer_wallets[buyer_id]
        if buyer_wallet["balance"] < amount:
            raise ValueError(f"Insufficient balance: {buyer_wallet['balance']} < {amount}")

        # Transfer funds
        buyer_wallet["balance"] -= amount
        buyer_wallet["transactions"].append({
            "type": "payment",
            "trade_id": trade["trade_id"],
            "amount": -amount,
            "timestamp": time.time()
        })

        if seller_id in self.consumer_wallets:
            seller_wallet = self.consumer_wallets[seller_id]
            seller_wallet["balance"] += amount
            seller_wallet["transactions"].append({
                "type": "receipt",
                "trade_id": trade["trade_id"],
                "amount": amount,
                "timestamp": time.time()
            })

        return {
            "status": "completed",
            "payment_method": "wallet",
            "amount": amount,
            "currency": trade["currency"],
            "transaction_id": f"wallet_tx_{int(time.time())}"
        }

    async def _process_card_payment(
        self,
        trade: Dict[str, Any],
        payment_details: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process credit/debit card payment."""
        # In real implementation, integrate with payment gateway (Stripe, PayPal, etc.)
        # This is a simplified simulation

        required_fields = ["card_number", "expiry", "cvv", "cardholder_name"]
        for field in required_fields:
            if field not in payment_details:
                raise ValueError(f"Missing required field: {field}")

        # Simulate payment processing
        await asyncio.sleep(0.5)  # Simulate network delay

        # Simulate success/failure (90% success rate)
        if time.time() % 10 < 9:  # 90% success
            return {
                "status": "completed",
                "payment_method": "card",
                "amount": trade["total_value"],
                "currency": trade["currency"],
                "transaction_id": f"card_tx_{int(time.time())}",
                "card_last_four": payment_details["card_number"][-4:]
            }
        else:
            return {
                "status": "failed",
                "payment_method": "card",
                "error": "Card declined",
                "amount": trade["total_value"]
            }

    async def _process_bank_payment(
        self,
        trade: Dict[str, Any],
        payment_details: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process bank transfer payment."""
        # Simulate bank transfer (takes longer)
        await asyncio.sleep(2.0)  # Simulate processing time

        return {
            "status": "completed",
            "payment_method": "bank",
            "amount": trade["total_value"],
            "currency": trade["currency"],
            "transaction_id": f"bank_tx_{int(time.time())}",
            "reference": payment_details.get("reference", f"REF_{int(time.time())}")
        }

    async def _process_crypto_payment(
        self,
        trade: Dict[str, Any],
        payment_details: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process cryptocurrency payment."""
        # In real implementation, integrate with crypto wallet/exchange
        # This is a simplified simulation

        supported_currencies = ["BTC", "ETH", "USDT"]
        crypto_currency = payment_details.get("crypto_currency", "USDT")

        if crypto_currency not in supported_currencies:
            raise ValueError(f"Unsupported cryptocurrency: {crypto_currency}")

        # Simulate crypto transaction
        await asyncio.sleep(1.0)  # Simulate blockchain confirmation

        return {
            "status": "completed",
            "payment_method": "crypto",
            "amount": trade["total_value"],
            "currency": trade["currency"],
            "crypto_currency": crypto_currency,
            "transaction_id": f"crypto_tx_{int(time.time())}",
            "blockchain_tx": f"0x{secrets.token_hex(32)}"
        }

    async def get_wallet_balance(self, consumer_id: str) -> Dict[str, Any]:
        """Get consumer wallet balance."""
        if consumer_id not in self.consumer_wallets:
            raise ValueError(f"Consumer {consumer_id} has no wallet")

        wallet = self.consumer_wallets[consumer_id]
        return {
            "consumer_id": consumer_id,
            "balance": wallet["balance"],
            "currency": wallet["currency"],
            "last_transaction": wallet["transactions"][-1] if wallet["transactions"] else None
        }

    async def add_wallet_funds(
        self,
        consumer_id: str,
        amount: float,
        payment_method: str,
        payment_details: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Add funds to consumer wallet."""
        if consumer_id not in self.consumer_wallets:
            raise ValueError(f"Consumer {consumer_id} has no wallet")

        wallet = self.consumer_wallets[consumer_id]

        # Process payment for adding funds
        payment_result = await self._process_wallet_topup(amount, payment_method, payment_details)

        if payment_result["status"] == "completed":
            wallet["balance"] += amount
            wallet["transactions"].append({
                "type": "deposit",
                "amount": amount,
                "payment_method": payment_method,
                "timestamp": time.time()
            })

        return {
            "consumer_id": consumer_id,
            "amount_added": amount,
            "new_balance": wallet["balance"],
            "payment_result": payment_result
        }

    async def _process_wallet_topup(
        self,
        amount: float,
        payment_method: str,
        payment_details: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process wallet top-up payment."""
        # Simplified - in real implementation, integrate with payment providers
        await asyncio.sleep(0.5)

        return {
            "status": "completed",
            "payment_method": payment_method,
            "amount": amount,
            "transaction_id": f"topup_tx_{int(time.time())}"
        }

    async def get_market_overview(self) -> Dict[str, Any]:
        """Get current market overview."""
        try:
            # Calculate market statistics
            active_offers = [o for o in self.energy_offers.values() if o["status"] == "active"]
            active_trades = list(self.active_trades.values())

            total_offered = sum(o["energy_amount"] for o in active_offers)
            total_traded = sum(t["energy_amount"] for t in active_trades)

            # Price statistics
            prices = [o["price_per_kwh"] for o in active_offers if o["price_per_kwh"] > 0]
            avg_price = sum(prices) / len(prices) if prices else 0

            # Source distribution
            source_distribution = {}
            for offer in active_offers:
                source = offer["energy_source"]
                source_distribution[source] = source_distribution.get(source, 0) + offer["energy_amount"]

            return {
                "timestamp": time.time(),
                "active_offers": len(active_offers),
                "active_trades": len(active_trades),
                "total_energy_offered": total_offered,
                "total_energy_traded": total_traded,
                "average_price": avg_price,
                "currency": self.config["default_currency"],
                "source_distribution": source_distribution,
                "market_status": "active" if active_offers else "inactive"
            }

        except Exception as e:
            self.logger.error(f"Failed to get market overview: {e}")
            return {"error": str(e)}

    async def get_energy_park_status(self, park_id: str) -> Optional[Dict[str, Any]]:
        """Get status of an energy park."""
        if park_id not in self.energy_parks:
            return None

        park = self.energy_parks[park_id]

        # Get source statuses
        sources = []
        for source_id, source in self.energy_sources.items():
            if source.get("park_id") == park_id:
                sources.append({
                    "source_id": source_id,
                    "type": source["type"].value,
                    "capacity": source["capacity"],
                    "current_production": source["current_production"],
                    "total_production": source["total_production"],
                    "status": source["status"]
                })

        return {
            "park_id": park_id,
            "name": park["name"],
            "location": park["location"],
            "total_capacity": park["total_capacity"],
            "current_production": park.get("current_production", 0),
            "total_production": park.get("total_production", 0),
            "status": park["status"],
            "sources": sources,
            "last_updated": park["last_updated"]
        }

    async def get_provider_dashboard(self, provider_id: str) -> Optional[Dict[str, Any]]:
        """Get provider dashboard data."""
        if provider_id not in self.energy_providers:
            return None

        provider = self.energy_providers[provider_id]

        # Get active trades for this provider
        provider_trades = [
            trade for trade in self.active_trades.values()
            if trade["buyer_id"] == provider_id
        ]

        # Calculate metrics
        total_purchased = sum(t["energy_amount"] for t in provider_trades)
        total_spent = sum(t["total_value"] for t in provider_trades)

        return {
            "provider_id": provider_id,
            "name": provider["name"],
            "type": provider["type"],
            "buying_capacity": provider["buying_capacity"],
            "total_purchased": provider["total_purchased"],
            "active_trades": len(provider_trades),
            "current_month_purchased": total_purchased,
            "current_month_spent": total_spent,
            "currency": self.config["default_currency"],
            "status": provider["status"]
        }

    async def start_market_monitoring(self) -> None:
        """Start background market monitoring."""
        if self.monitoring_task and not self.monitoring_task.done():
            return

        self.monitoring_task = asyncio.create_task(self._market_monitoring_worker())
        self.settlement_task = asyncio.create_task(self._settlement_worker())

        self.logger.info("Started energy trading market monitoring")

    async def stop_market_monitoring(self) -> None:
        """Stop background market monitoring."""
        if self.monitoring_task:
            self.monitoring_task.cancel()
        if self.settlement_task:
            self.settlement_task.cancel()

        self.logger.info("Stopped energy trading market monitoring")

    async def _market_monitoring_worker(self) -> None:
        """Background market monitoring worker."""
        while True:
            try:
                await asyncio.sleep(self.config["price_update_interval"])

                # Update market prices
                await self._update_market_prices()

                # Check for expired offers
                await self._cleanup_expired_offers()

                # Update production forecasts
                await self._update_production_forecasts()

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Market monitoring error: {e}")

    async def _settlement_worker(self) -> None:
        """Background settlement worker."""
        while True:
            try:
                await asyncio.sleep(self.config["settlement_interval"])

                # Process settlements
                await self._process_settlements()

                # Update billing cycles
                await self._update_billing_cycles()

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Settlement worker error: {e}")

    async def _update_market_prices(self) -> None:
        """Update market prices based on supply/demand."""
        # Simplified price update logic
        # In practice, this would use more sophisticated algorithms
        current_time = time.time()

        for source_type in [e.value for e in EnergySource]:
            # Calculate average price for source type
            offers = [
                o for o in self.energy_offers.values()
                if o["status"] == "active" and o["energy_source"] == source_type
            ]

            if offers:
                avg_price = sum(o["price_per_kwh"] for o in offers) / len(offers)

                if source_type not in self.price_history:
                    self.price_history[source_type] = []

                self.price_history[source_type].append(avg_price)

                # Keep only recent history
                self.price_history[source_type] = self.price_history[source_type][-100:]

    async def _cleanup_expired_offers(self) -> None:
        """Clean up expired energy offers."""
        current_time = time.time()
        expired_offers = []

        for offer_id, offer in self.energy_offers.items():
            if offer["status"] == "active" and offer["valid_until"] < current_time:
                offer["status"] = "expired"
                expired_offers.append(offer_id)

        if expired_offers:
            self.logger.info(f"Expired {len(expired_offers)} energy offers")

    async def _update_production_forecasts(self) -> None:
        """Update production forecasts for energy sources."""
        # Placeholder for production forecasting logic
        # This would use weather data, historical patterns, etc.
        pass

    async def _process_settlements(self) -> None:
        """Process energy trade settlements."""
        # Placeholder for settlement processing
        # This would handle payments, delivery confirmations, etc.
        pass

    async def _update_billing_cycles(self) -> None:
        """Update billing cycles for providers."""
        # Placeholder for billing cycle updates
        pass