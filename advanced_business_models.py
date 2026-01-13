"""
Advanced Business Models Module

This module simulates advanced business models for an IoT platform, including
dynamic subscription tiers, API monetization, partner ecosystems, and time-based
financial reporting.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta, timezone
import json
from collections import defaultdict
import random

from utils.logging_config import get_logger

# --- Helper Classes & Engines ---

class DynamicPricingEngine:
    """Simulates dynamic price adjustments based on market factors."""
    def __init__(self, logger):
        self.logger = logger
        self.price_multipliers = {'starter': 1.0, 'professional': 1.0, 'enterprise': 1.0}

    def update_prices(self, demand_factor: float, system_load: float):
        """Adjusts prices based on demand and system load."""
        self.logger.info(f"Updating prices based on demand ({demand_factor:.2f}) and load ({system_load:.2f}).")
        for tier in self.price_multipliers:
            base_multiplier = 1.0
            # Increase price with high demand
            if demand_factor > 1.5:
                base_multiplier += (demand_factor - 1.5) * 0.1
            # Increase price with high system load
            if system_load > 0.8:
                base_multiplier += (system_load - 0.8) * 0.2
            # Decrease price with low demand
            if demand_factor < 0.8:
                base_multiplier -= (0.8 - demand_factor) * 0.05

            self.price_multipliers[tier] = round(max(0.8, base_multiplier), 2) # Don't drop below 80%
            self.logger.info(f"New price multiplier for '{tier}': {self.price_multipliers[tier]}")

    def get_adjusted_price(self, tier: str, base_price: float) -> float:
        return base_price * self.price_multipliers.get(tier, 1.0)

# --- Core Business Model Managers ---

class SubscriptionTierManager:
    """Manages subscription tiers, including usage-based and dynamic pricing."""
    def __init__(self, pricing_engine: DynamicPricingEngine):
        self.pricing_engine = pricing_engine
        self.tiers = {
            'starter': {'name': 'Starter', 'base_price': 99, 'features': ['basic'], 'limits': {'api_calls': 1000}},
            'professional': {'name': 'Professional', 'base_price': 299, 'features': ['advanced'], 'limits': {'api_calls': 10000}},
            'pay_as_you_go': {'name': 'Pay-as-you-go', 'base_price': 0, 'features': ['basic'], 'limits': {}},
        }
        self.usage_rates = {'api_calls': 0.02}
        self.customers: Dict[str, Dict[str, Any]] = {}

    def add_customer(self, customer_id: str, tier: str, join_date: datetime):
        if tier not in self.tiers:
            raise ValueError(f"Invalid tier: {tier}")
        self.customers[customer_id] = {
            "tier": tier,
            "usage": defaultdict(int),
            "join_date": join_date,
        }

    def log_usage(self, customer_id: str, usage_data: Dict[str, int]):
        if customer_id not in self.customers: return
        for metric, value in usage_data.items():
            self.customers[customer_id]["usage"][metric] += value

    def calculate_monthly_billing(self) -> List[Dict]:
        """Calculates billing for all customers for a month."""
        all_bills = []
        for cid, customer in self.customers.items():
            tier_config = self.tiers[customer['tier']]
            usage = customer['usage']

            # Apply dynamic pricing to base price
            base_cost = self.pricing_engine.get_adjusted_price(customer['tier'], tier_config['base_price'])

            usage_cost = 0
            overage_cost = 0

            # Calculate costs based on the model
            if customer['tier'] == 'pay_as_you_go':
                # Pure usage-based billing
                for metric, value in usage.items():
                    usage_cost += value * self.usage_rates.get(metric, 0)
            else:
                # Tiered with overages
                for metric, limit in tier_config['limits'].items():
                    actual_usage = usage.get(metric, 0)
                    if actual_usage > limit:
                        overage = actual_usage - limit
                        overage_cost += overage * self.usage_rates.get(metric, 0)

            all_bills.append({
                'customer_id': cid,
                'tier': customer['tier'],
                'base_cost': base_cost,
                'usage_cost': usage_cost,
                'overage_cost': overage_cost,
                'total_cost': base_cost + usage_cost + overage_cost
            })
            # Reset usage for next month
            customer['usage'] = defaultdict(int)
        return all_bills

class APIMonetizationManager:
    """Manages API monetization (simplified as usage is now in SubscriptionManager)."""
    def __init__(self):
        self.api_users = {} # Still useful for tracking non-customer API users (e.g., trials)

    def calculate_costs(self):
        # In this refactored model, API costs are part of the subscription.
        # This method could be used for trial users or other non-subscribed API consumers.
        return {}

class PartnerEcosystemManager:
    """Manages partner ecosystems with revenue sharing."""
    def __init__(self):
        self.partners = {}

    def onboard_partner(self, partner_id: str, rev_share_percentage: float):
        self.partners[partner_id] = {
            'rev_share': rev_share_percentage,
            'monthly_revenue': 0,
            'payout_history': []
        }

    def log_partner_transaction(self, partner_id: str, revenue: float):
        if partner_id in self.partners:
            self.partners[partner_id]['monthly_revenue'] += revenue

    def process_monthly_payouts(self) -> List[Dict]:
        """Calculates and records payouts for all partners."""
        payouts = []
        for pid, partner in self.partners.items():
            revenue = partner['monthly_revenue']
            payout_amount = revenue * partner['rev_share']

            payouts.append({'partner_id': pid, 'revenue_generated': revenue, 'payout': payout_amount})

            partner['payout_history'].append({'date': datetime.now(timezone.utc), 'amount': payout_amount})
            # Reset for next month
            partner['monthly_revenue'] = 0
        return payouts

# --- Simulation Orchestrator ---

class BusinessModelSimulator:
    """Orchestrates the simulation of business models over time."""
    def __init__(self):
        self.logger = get_logger(f"{__name__}.{self.__class__.__name__}")
        self.pricing_engine = DynamicPricingEngine(self.logger)
        self.subscription_manager = SubscriptionTierManager(self.pricing_engine)
        self.api_manager = APIMonetizationManager()
        self.partner_manager = PartnerEcosystemManager()

    def run_simulation(self, start_date: datetime, days: int):
        self.logger.info(f"--- Starting {days}-day business simulation from {start_date.date()} ---")

        # Setup initial state
        self.partner_manager.onboard_partner("partner_a", 0.2) # 20% rev share

        # Main simulation loop
        for day in range(days):
            current_date = start_date + timedelta(days=day)
            self.logger.debug(f"\n--- Day {day+1} ({current_date.date()}) ---")

            # 1. Potentially update pricing (e.g., weekly)
            if day % 7 == 0:
                self.pricing_engine.update_prices(demand_factor=random.uniform(0.7, 1.8), system_load=random.uniform(0.4, 0.9))

            # 2. Simulate new customers
            if random.random() < 0.3: # 30% chance of a new customer
                new_cid = f"cust_{len(self.subscription_manager.customers) + 1}"
                new_tier = random.choice(['starter', 'professional', 'pay_as_you_go'])
                self.subscription_manager.add_customer(new_cid, new_tier, current_date)
                self.logger.debug(f"New customer '{new_cid}' joined on tier '{new_tier}'.")

            # 3. Simulate usage for existing customers
            for cid in list(self.subscription_manager.customers.keys()):
                usage = {'api_calls': random.randint(50, 500)}
                self.subscription_manager.log_usage(cid, usage)

            # 4. Simulate partner-driven revenue
            if random.random() < 0.5:
                self.partner_manager.log_partner_transaction("partner_a", revenue=random.uniform(10, 100))

        # --- End of simulation: Generate final reports ---
        self.logger.info("\n--- Simulation Ended: Generating Final Reports ---")
        subscription_revenue = self.subscription_manager.calculate_monthly_billing()
        partner_payouts = self.partner_manager.process_monthly_payouts()

        total_sub_revenue = sum(b['total_cost'] for b in subscription_revenue)
        total_partner_payout = sum(p['payout'] for p in partner_payouts)

        final_report = {
            "simulation_period_days": days,
            "total_customers": len(self.subscription_manager.customers),
            "total_subscription_revenue": round(total_sub_revenue, 2),
            "total_partner_payouts": round(total_partner_payout, 2),
            "net_revenue": round(total_sub_revenue - total_partner_payout, 2),
            "billing_details": subscription_revenue,
            "partner_payout_details": partner_payouts,
        }

        print(json.dumps(final_report, indent=2))
        return final_report

if __name__ == "__main__":
    simulator = BusinessModelSimulator()
    simulator.run_simulation(start_date=datetime.now(timezone.utc), days=30)