"""
Advanced Business Models Module

This module implements advanced business models for the IoT IIoT Intelligence Platform,
including subscription tiers, API monetization, partner ecosystems, and innovative
pricing strategies for industrial applications.

Features:
- Advanced subscription tiers with usage-based pricing
- API monetization and marketplace
- Partner ecosystem management
- Freemium models for small businesses
- Dynamic pricing optimization
- Revenue analytics and forecasting
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
import json
from collections import defaultdict

class SubscriptionTierManager:
    """
    Manages advanced subscription tiers with dynamic pricing.
    """

    def __init__(self):
        self.tiers = {
            'starter': {
                'name': 'Starter',
                'base_price': 99,
                'features': ['basic_monitoring', 'email_alerts', '5_devices'],
                'limits': {'devices': 5, 'api_calls': 1000, 'storage_gb': 10}
            },
            'professional': {
                'name': 'Professional',
                'base_price': 299,
                'features': ['advanced_analytics', 'real_time_alerts', '50_devices', 'api_access'],
                'limits': {'devices': 50, 'api_calls': 10000, 'storage_gb': 100}
            },
            'enterprise': {
                'name': 'Enterprise',
                'base_price': 999,
                'features': ['full_platform', 'white_label', 'unlimited_devices', 'priority_support'],
                'limits': {'devices': -1, 'api_calls': -1, 'storage_gb': -1}  # -1 = unlimited
            }
        }
        self.usage_pricing = {
            'device_overage': 15,
            'api_overage': 0.01,
            'storage_overage': 0.5
        }
        # State management
        self.customers: Dict[str, Dict[str, Any]] = {}

    def add_customer(self, customer_id: str, tier: str):
        """Adds a new customer with a specified subscription tier."""
        if tier not in self.tiers:
            raise ValueError(f"Invalid tier: {tier}")
        self.customers[customer_id] = {
            "tier": tier,
            "current_usage": defaultdict(int),
            "onboarded_date": datetime.utcnow()
        }

    def log_customer_usage(self, customer_id: str, usage_data: Dict[str, int]):
        """Logs resource usage for a customer."""
        if customer_id not in self.customers:
            raise ValueError(f"Customer {customer_id} not found.")
        for metric, value in usage_data.items():
            self.customers[customer_id]["current_usage"][metric] += value

    def calculate_subscription_cost(self, customer_id: str, billing_period: str = 'monthly') -> Dict[str, Any]:
        """
        Calculate subscription cost for a specific customer based on their state.
        """
        if customer_id not in self.customers:
            return {"error": f"Customer not found: {customer_id}"}

        customer_data = self.customers[customer_id]
        tier = customer_data["tier"]
        usage = customer_data["current_usage"]
        tier_config = self.tiers[tier]
        base_cost = tier_config['base_price']
        limits = tier_config['limits']

        overage_cost = 0
        overages = {}
        for metric, limit in limits.items():
            if limit != -1:
                actual_usage = usage.get(metric, 0)
                if actual_usage > limit:
                    overage = actual_usage - limit
                    overage_rate = self.usage_pricing.get(f'{metric}_overage', 0)
                    overage_cost += overage * overage_rate
                    overages[metric] = {'limit': limit, 'actual': actual_usage, 'overage': overage, 'cost': overage * overage_rate}

        total_cost = base_cost + overage_cost

        # Apply billing period multiplier
        if billing_period == 'yearly':
            total_cost *= 12 * 0.9  # 10% discount for yearly

        recommendations = self._generate_tier_recommendations(customer_id, overages)

        return {
            'customer_id': customer_id,
            'tier': tier,
            'base_cost': base_cost,
            'overage_cost': overage_cost,
            'total_cost': round(total_cost, 2),
            'billing_period': billing_period,
            'overages': overages,
            'recommendations': recommendations
        }

    def recommend_optimal_tier(self, customer_id: str, budget: float = None) -> Dict[str, Any]:
        """
        Recommend the optimal subscription tier for a customer based on their usage.
        """
        if customer_id not in self.customers:
            return {"error": f"Customer not found: {customer_id}"}

        usage = self.customers[customer_id]["current_usage"]
        tier_scores = {}

        for tier_name, tier_config in self.tiers.items():
            score = 0
            limits = tier_config['limits']
            for metric, limit in limits.items():
                if limit == -1: score += 10
                else:
                    actual = usage.get(metric, 0)
                    if actual <= limit: score += 5
                    elif actual <= limit * 1.5: score += 2
                    else: score -= 2

            features_needed = self._assess_feature_needs(usage)
            available_features = set(tier_config['features'])
            feature_coverage = len(features_needed & available_features) / max(len(features_needed), 1)
            score += feature_coverage * 5
            tier_scores[tier_name] = score

        best_tier_name = max(tier_scores, key=tier_scores.get)

        # Temporarily set customer tier to get cost analysis
        original_tier = self.customers[customer_id]['tier']
        self.customers[customer_id]['tier'] = best_tier_name
        cost_analysis = self.calculate_subscription_cost(customer_id)
        self.customers[customer_id]['tier'] = original_tier # Revert

        return {
            'recommended_tier': best_tier_name,
            'confidence_score': min(tier_scores[best_tier_name] / 15, 1.0),
            'cost_analysis': cost_analysis
        }

    def _generate_tier_recommendations(self, customer_id: str, overages: Dict[str, Any]) -> List[str]:
        """
        Generate tier-related recommendations for a specific customer.
        """
        recommendations = []
        if overages:
            recommendations.append("Consider upgrading to a higher tier to avoid overage charges.")

        optimal = self.recommend_optimal_tier(customer_id)
        current_tier = self.customers[customer_id]['tier']
        if optimal.get('recommended_tier') != current_tier:
            recommendations.append(f"Optimal tier seems to be '{optimal['recommended_tier']}'. Consider switching for better value.")

        return recommendations

    def _assess_feature_needs(self, usage: Dict[str, int]) -> set:
        """
        Assess which features are needed based on usage.
        """
        features_needed = {'basic_monitoring'}  # Always needed

        if usage.get('api_calls', 0) > 1000:
            features_needed.add('api_access')

        if usage.get('devices', 0) > 5:
            features_needed.add('real_time_alerts')

        if usage.get('storage_gb', 0) > 10:
            features_needed.add('advanced_analytics')

        return features_needed

class APIMonetizationManager:
    """Manages API monetization and marketplace."""

    def __init__(self):
        self.api_endpoints = {
            'data_ingestion': {'base_price': 0.001, 'unit': 'per_request'},
            'analytics_query': {'base_price': 0.01, 'unit': 'per_query'},
        }
        self.api_plans = {
            'free': {'monthly_limit': 1000, 'price': 0},
            'developer': {'monthly_limit': 10000, 'price': 29},
        }
        self.api_users = {} # State management

    def add_api_user(self, user_id: str, plan: str):
        if plan not in self.api_plans:
            raise ValueError(f"Invalid API plan: {plan}")
        self.api_users[user_id] = {"plan": plan, "usage": defaultdict(int)}

    def log_api_usage(self, user_id: str, endpoint: str, count: int):
        if user_id not in self.api_users:
            raise ValueError(f"API user {user_id} not found.")
        self.api_users[user_id]["usage"][endpoint] += count

    def calculate_api_cost(self, user_id: str) -> Dict[str, Any]:
        if user_id not in self.api_users:
            return {"error": f"API user not found: {user_id}"}

        user_data = self.api_users[user_id]
        plan = user_data["plan"]
        usage = user_data["usage"]
        plan_config = self.api_plans[plan]

        total_requests = sum(usage.values())
        usage_cost = sum(self.api_endpoints[e]['base_price'] * c for e, c in usage.items() if e in self.api_endpoints)

        # Simplified overage
        overage_cost = 0
        if plan_config['monthly_limit'] != -1 and total_requests > plan_config['monthly_limit']:
            overage_cost = (total_requests - plan_config['monthly_limit']) * 0.002

        return {
            'user_id': user_id,
            'plan': plan,
            'plan_cost': plan_config['price'],
            'usage_cost': round(usage_cost, 2),
            'overage_cost': round(overage_cost, 2),
            'total_cost': round(plan_config['price'] + usage_cost + overage_cost, 2)
        }

    def optimize_api_pricing(self) -> Dict[str, Any]:
        # This method would now analyze self.api_users to provide recommendations
        return {"recommendation": "Analyze usage patterns in self.api_users to adjust plan limits and pricing."}

class PartnerEcosystemManager:
    """Manages partner ecosystems and integrations."""

    def __init__(self):
        self.partners = {}
        self.integrations = {}
        self.revenue_sharing_models = {
            'revenue_share': {'partner_percentage': 0.3},
            'per_transaction': {'fixed_fee': 0.05, 'variable_fee': 0.02}
        }

    def onboard_partner(self, partner_info: Dict[str, Any]) -> str:
        partner_id = f"partner_{len(self.partners) + 1}"
        self.partners[partner_id] = {
            'id': partner_id,
            'name': partner_info['name'],
            'revenue_model': partner_info.get('revenue_model', 'revenue_share'),
            'total_revenue_generated': 0,
            'total_transactions': 0,
        }
        return partner_id

    def log_partner_revenue(self, partner_id: str, revenue: float, transactions: int):
        if partner_id not in self.partners:
            raise ValueError(f"Partner {partner_id} not found.")
        self.partners[partner_id]['total_revenue_generated'] += revenue
        self.partners[partner_id]['total_transactions'] += transactions

    def calculate_partner_revenue(self, partner_id: str) -> Dict[str, Any]:
        if partner_id not in self.partners:
            return {"error": f"Partner not found: {partner_id}"}

        partner = self.partners[partner_id]
        revenue_model = partner['revenue_model']
        model_config = self.revenue_sharing_models[revenue_model]

        total_revenue = partner['total_revenue_generated']
        transactions = partner['total_transactions']

        if revenue_model == 'per_transaction':
            partner_share = (transactions * model_config['fixed_fee']) + (total_revenue * model_config['variable_fee'])
        else: # revenue_share
            partner_share = total_revenue * model_config['partner_percentage']

        return {
            'partner_id': partner_id,
            'total_revenue': total_revenue,
            'partner_share': round(partner_share, 2),
            'platform_share': round(total_revenue - partner_share, 2)
        }

class AdvancedBusinessModelManager:
    """Manages and simulates advanced business models."""

    def __init__(self):
        self.subscription_manager = SubscriptionTierManager()
        self.api_manager = APIMonetizationManager()
        self.partner_manager = PartnerEcosystemManager()

    def run_comprehensive_simulation(self):
        """Runs a detailed simulation demonstrating all business models."""
        print("--- Running Comprehensive Business Simulation ---")

        # 1. Setup Subscription Tiers for two customers
        print("\n1. Onboarding customers and logging usage...")
        self.subscription_manager.add_customer("cust_001", "professional")
        self.subscription_manager.log_customer_usage("cust_001", {'devices': 40, 'api_calls': 8000, 'storage_gb': 90})

        self.subscription_manager.add_customer("cust_002", "starter")
        self.subscription_manager.log_customer_usage("cust_002", {'devices': 10, 'api_calls': 2000, 'storage_gb': 25}) # Overage on all metrics

        # 2. Setup API Monetization for an API user
        print("\n2. Registering API users and logging calls...")
        self.api_manager.add_api_user("api_user_1", "developer")
        self.api_manager.log_api_usage("api_user_1", "analytics_query", 12000) # Overage

        # 3. Onboard a Partner and log their activity
        print("\n3. Onboarding partners and logging revenue...")
        partner_id = self.partner_manager.onboard_partner({
            "name": "IntegrationCorp",
            "revenue_model": "revenue_share"
        })
        self.partner_manager.log_partner_revenue(partner_id, 1000.0, 50)

        # 4. Calculate and Report Results
        print("\n--- Simulation Results ---")
        results = {
            "subscription_billing": {
                "cust_001": self.subscription_manager.calculate_subscription_cost("cust_001"),
                "cust_002": self.subscription_manager.calculate_subscription_cost("cust_002"),
            },
            "tier_recommendations": {
                "cust_001_optimal": self.subscription_manager.recommend_optimal_tier("cust_001"),
                "cust_002_optimal": self.subscription_manager.recommend_optimal_tier("cust_002"),
            },
            "api_billing": self.api_manager.calculate_api_cost("api_user_1"),
            "partner_payout": self.partner_manager.calculate_partner_revenue(partner_id),
            "api_pricing_optimization": self.api_manager.optimize_api_pricing()
        }

        print(json.dumps(results, indent=2))
        return results

# Example usage
if __name__ == "__main__":
    business_manager = AdvancedBusinessModelManager()
    business_manager.run_comprehensive_simulation()