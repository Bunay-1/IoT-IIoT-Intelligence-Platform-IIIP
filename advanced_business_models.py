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
            },
            'custom': {
                'name': 'Custom Enterprise',
                'base_price': 0,  # Custom pricing
                'features': ['tailored_solution', 'dedicated_support', 'custom_integrations'],
                'limits': {}  # Custom limits
            }
        }

        self.usage_pricing = {
            'device_overage': 15,  # per additional device
            'api_overage': 0.01,   # per additional API call
            'storage_overage': 0.5  # per additional GB
        }

    def calculate_subscription_cost(self, tier: str, usage: Dict[str, int],
                                  billing_period: str = 'monthly') -> Dict[str, Any]:
        """
        Calculate subscription cost based on tier and usage.

        Args:
            tier: Subscription tier
            usage: Actual usage metrics
            billing_period: Billing period (monthly/yearly)

        Returns:
            Dict[str, Any]: Cost breakdown and recommendations
        """
        if tier not in self.tiers:
            return {"error": f"Invalid tier: {tier}"}

        tier_config = self.tiers[tier]
        base_cost = tier_config['base_price']
        limits = tier_config['limits']

        # Calculate overage costs
        overage_cost = 0
        overages = {}

        for metric, limit in limits.items():
            if limit != -1:  # Not unlimited
                actual_usage = usage.get(metric, 0)
                if actual_usage > limit:
                    overage = actual_usage - limit
                    overage_rate = self.usage_pricing.get(f'{metric}_overage', 0)
                    overage_cost += overage * overage_rate
                    overages[metric] = {
                        'limit': limit,
                        'actual': actual_usage,
                        'overage': overage,
                        'cost': overage * overage_rate
                    }

        total_cost = base_cost + overage_cost

        # Apply billing period multiplier
        if billing_period == 'yearly':
            total_cost *= 12 * 0.9  # 10% discount for yearly

        # Generate recommendations
        recommendations = self._generate_tier_recommendations(tier, usage, overages)

        return {
            'tier': tier,
            'base_cost': base_cost,
            'overage_cost': overage_cost,
            'total_cost': round(total_cost, 2),
            'billing_period': billing_period,
            'overages': overages,
            'recommendations': recommendations,
            'cost_breakdown': {
                'subscription': base_cost,
                'overages': overage_cost,
                'discounts': total_cost - (base_cost + overage_cost) if billing_period == 'yearly' else 0
            }
        }

    def recommend_optimal_tier(self, usage: Dict[str, int], budget: float = None) -> Dict[str, Any]:
        """
        Recommend the optimal subscription tier based on usage and budget.

        Args:
            usage: Expected usage metrics
            budget: Monthly budget constraint

        Returns:
            Dict[str, Any]: Tier recommendation
        """
        tier_scores = {}

        for tier_name, tier_config in self.tiers.items():
            if tier_name == 'custom':
                continue  # Skip custom for automated recommendations

            score = 0
            limits = tier_config['limits']

            # Score based on how well limits fit usage
            for metric, limit in limits.items():
                if limit == -1:  # Unlimited
                    score += 10
                else:
                    actual = usage.get(metric, 0)
                    if actual <= limit:
                        score += 5
                    elif actual <= limit * 1.5:  # Within 50% overage
                        score += 2
                    else:
                        score -= 2  # Significant overage

            # Score based on features needed
            features_needed = self._assess_feature_needs(usage)
            available_features = set(tier_config['features'])
            feature_coverage = len(features_needed & available_features) / len(features_needed)
            score += feature_coverage * 5

            tier_scores[tier_name] = score

        # Get best tier
        best_tier = max(tier_scores.items(), key=lambda x: x[1])

        # Calculate cost for best tier
        cost_analysis = self.calculate_subscription_cost(best_tier[0], usage)

        # Check budget constraint
        if budget and cost_analysis['total_cost'] > budget:
            # Find most expensive tier within budget
            affordable_tiers = [
                (tier, self.calculate_subscription_cost(tier, usage)['total_cost'])
                for tier in self.tiers.keys() if tier != 'custom'
            ]
            affordable_tiers = [(t, c) for t, c in affordable_tiers if c <= budget]

            if affordable_tiers:
                best_tier = max(affordable_tiers, key=lambda x: x[1])
                cost_analysis = self.calculate_subscription_cost(best_tier[0], usage)

        return {
            'recommended_tier': best_tier[0],
            'confidence_score': min(best_tier[1] / 10, 1.0),  # Normalize to 0-1
            'cost_analysis': cost_analysis,
            'alternative_tiers': sorted(tier_scores.items(), key=lambda x: x[1], reverse=True)[:3]
        }

    def _generate_tier_recommendations(self, current_tier: str, usage: Dict[str, int],
                                     overages: Dict[str, Any]) -> List[str]:
        """
        Generate tier-related recommendations.
        """
        recommendations = []

        if overages:
            recommendations.append("Consider upgrading to a higher tier to avoid overage charges")

        # Check if current tier is optimal
        optimal = self.recommend_optimal_tier(usage)
        if optimal['recommended_tier'] != current_tier:
            recommendations.append(f"Consider switching to {optimal['recommended_tier']} tier for better value")

        # Billing cycle recommendations
        cost_monthly = self.calculate_subscription_cost(current_tier, usage, 'monthly')['total_cost']
        cost_yearly = self.calculate_subscription_cost(current_tier, usage, 'yearly')['total_cost']

        if cost_yearly < cost_monthly * 12:
            recommendations.append("Consider yearly billing for cost savings")

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
    """
    Manages API monetization and marketplace.
    """

    def __init__(self):
        self.api_endpoints = {
            'data_ingestion': {'base_price': 0.001, 'unit': 'per_request'},
            'analytics_query': {'base_price': 0.01, 'unit': 'per_query'},
            'predictive_model': {'base_price': 0.1, 'unit': 'per_prediction'},
            'real_time_stream': {'base_price': 0.005, 'unit': 'per_minute'},
            'bulk_export': {'base_price': 0.05, 'unit': 'per_gb'}
        }

        self.api_plans = {
            'free': {'monthly_limit': 1000, 'price': 0},
            'developer': {'monthly_limit': 10000, 'price': 29},
            'business': {'monthly_limit': 100000, 'price': 99},
            'enterprise': {'monthly_limit': -1, 'price': 299}  # Unlimited
        }

    def calculate_api_cost(self, usage: Dict[str, int], plan: str = 'free') -> Dict[str, Any]:
        """
        Calculate API usage costs.

        Args:
            usage: API usage by endpoint
            plan: Subscription plan

        Returns:
            Dict[str, Any]: Cost analysis
        """
        if plan not in self.api_plans:
            return {"error": f"Invalid plan: {plan}"}

        plan_config = self.api_plans[plan]
        monthly_limit = plan_config['monthly_limit']
        plan_cost = plan_config['price']

        total_requests = sum(usage.values())
        overage_cost = 0
        breakdown = {}

        # Calculate costs for each endpoint
        for endpoint, count in usage.items():
            if endpoint in self.api_endpoints:
                config = self.api_endpoints[endpoint]
                cost = count * config['base_price']
                breakdown[endpoint] = {
                    'requests': count,
                    'rate': config['base_price'],
                    'cost': round(cost, 2)
                }

        total_cost = sum(item['cost'] for item in breakdown.values())

        # Check limits and calculate overages
        if monthly_limit != -1 and total_requests > monthly_limit:
            overage_requests = total_requests - monthly_limit
            overage_rate = 0.002  # $0.002 per additional request
            overage_cost = overage_requests * overage_rate
            total_cost += overage_cost

        return {
            'plan': plan,
            'plan_cost': plan_cost,
            'usage_cost': round(total_cost - overage_cost, 2),
            'overage_cost': round(overage_cost, 2),
            'total_cost': round(plan_cost + total_cost, 2),
            'total_requests': total_requests,
            'monthly_limit': monthly_limit,
            'breakdown': breakdown,
            'recommendations': self._generate_api_recommendations(plan, total_requests, monthly_limit)
        }

    def optimize_api_pricing(self, usage_history: pd.DataFrame) -> Dict[str, Any]:
        """
        Optimize API pricing based on usage patterns.

        Args:
            usage_history: Historical API usage data

        Returns:
            Dict[str, Any]: Pricing optimization recommendations
        """
        # Analyze usage patterns
        total_usage = usage_history.sum(axis=1)
        peak_usage = total_usage.max()
        avg_usage = total_usage.mean()

        # Calculate optimal pricing tiers
        optimal_tiers = {}

        for tier_name, config in self.api_plans.items():
            if config['monthly_limit'] == -1:  # Unlimited
                continue

            limit = config['monthly_limit']
            if avg_usage <= limit:
                optimal_tiers[tier_name] = {
                    'utilization': avg_usage / limit,
                    'cost_effectiveness': config['price'] / limit if limit > 0 else 0
                }

        # Recommend pricing adjustments
        recommendations = []
        if peak_usage > avg_usage * 2:
            recommendations.append("Consider usage-based pricing for high-variability customers")

        if len(optimal_tiers) < 2:
            recommendations.append("Consider adding intermediate pricing tiers")

        return {
            'current_metrics': {
                'avg_monthly_usage': int(avg_usage),
                'peak_monthly_usage': int(peak_usage),
                'usage_volatility': peak_usage / avg_usage if avg_usage > 0 else 0
            },
            'optimal_tiers': optimal_tiers,
            'recommendations': recommendations
        }

    def _generate_api_recommendations(self, plan: str, total_requests: int,
                                    monthly_limit: int) -> List[str]:
        """
        Generate API usage recommendations.
        """
        recommendations = []

        if monthly_limit != -1:
            utilization = total_requests / monthly_limit
            if utilization > 0.9:
                recommendations.append("Consider upgrading to a higher plan to avoid limits")
            elif utilization < 0.3:
                recommendations.append("Consider downgrading to a more cost-effective plan")

        # General recommendations
        recommendations.extend([
            "Implement API rate limiting to prevent abuse",
            "Use API versioning for backward compatibility",
            "Provide comprehensive API documentation"
        ])

        return recommendations

class PartnerEcosystemManager:
    """
    Manages partner ecosystems and integrations.
    """

    def __init__(self):
        self.partners = {}
        self.integrations = {}
        self.revenue_sharing_models = {
            'revenue_share': {'partner_percentage': 0.3, 'platform_percentage': 0.7},
            'subscription_split': {'partner_percentage': 0.2, 'platform_percentage': 0.8},
            'per_transaction': {'fixed_fee': 0.05, 'variable_fee': 0.02}
        }

    def onboard_partner(self, partner_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Onboard a new partner to the ecosystem.

        Args:
            partner_info: Partner information and requirements

        Returns:
            Dict[str, Any]: Onboarding results
        """
        partner_id = f"partner_{len(self.partners) + 1}"

        partner = {
            'id': partner_id,
            'name': partner_info['name'],
            'type': partner_info['type'],  # technology, integration, reseller, etc.
            'specialization': partner_info.get('specialization', []),
            'revenue_model': partner_info.get('revenue_model', 'revenue_share'),
            'status': 'active',
            'onboarded_at': datetime.utcnow(),
            'performance_metrics': {
                'customers_acquired': 0,
                'revenue_generated': 0,
                'satisfaction_score': 0
            }
        }

        self.partners[partner_id] = partner

        # Create integration if needed
        if partner_info.get('requires_integration', False):
            integration = self._create_integration(partner)
            self.integrations[partner_id] = integration

        return {
            'partner_id': partner_id,
            'status': 'onboarded',
            'integration_required': partner_info.get('requires_integration', False),
            'revenue_model': partner['revenue_model'],
            'next_steps': [
                'Complete integration setup',
                'Configure revenue sharing',
                'Set up partner portal access',
                'Schedule training session'
            ]
        }

    def calculate_partner_revenue(self, partner_id: str, revenue_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate revenue sharing for a partner.

        Args:
            partner_id: Partner identifier
            revenue_data: Revenue data from partner activities

        Returns:
            Dict[str, Any]: Revenue calculation
        """
        if partner_id not in self.partners:
            return {"error": f"Partner not found: {partner_id}"}

        partner = self.partners[partner_id]
        revenue_model = partner['revenue_model']

        if revenue_model not in self.revenue_sharing_models:
            return {"error": f"Invalid revenue model: {revenue_model}"}

        model_config = self.revenue_sharing_models[revenue_model]

        total_revenue = revenue_data.get('total_revenue', 0)
        transactions = revenue_data.get('transactions', 0)

        if revenue_model == 'per_transaction':
            partner_share = (transactions * model_config['fixed_fee'] +
                           total_revenue * model_config['variable_fee'])
        else:
            partner_percentage = model_config['partner_percentage']
            partner_share = total_revenue * partner_percentage

        platform_share = total_revenue - partner_share

        return {
            'partner_id': partner_id,
            'total_revenue': total_revenue,
            'partner_share': round(partner_share, 2),
            'platform_share': round(platform_share, 2),
            'revenue_model': revenue_model,
            'share_percentage': model_config.get('partner_percentage', 0),
            'transactions': transactions
        }

    def _create_integration(self, partner: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create integration configuration for a partner.
        """
        return {
            'partner_id': partner['id'],
            'api_endpoints': ['/api/v1/partners/data', '/api/v1/partners/webhook'],
            'authentication': 'oauth2',
            'data_format': 'json',
            'webhook_url': partner.get('webhook_url'),
            'status': 'pending_setup'
        }

class AdvancedBusinessManager:
    """
    Comprehensive advanced business models management system.
    """

    def __init__(self):
        self.subscription_manager = SubscriptionTierManager()
        self.api_manager = APIMonetizationManager()
        self.partner_manager = PartnerEcosystemManager()

    def comprehensive_business_analysis(self, business_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform comprehensive business model analysis.

        Args:
            business_data: Business metrics and requirements

        Returns:
            Dict[str, Any]: Comprehensive business analysis
        """
        analysis = {}

        # Subscription analysis
        if 'current_usage' in business_data:
            usage = business_data['current_usage']
            current_tier = business_data.get('current_tier', 'starter')

            analysis['subscription_analysis'] = {
                'current_cost': self.subscription_manager.calculate_subscription_cost(
                    current_tier, usage
                ),
                'optimal_tier': self.subscription_manager.recommend_optimal_tier(
                    usage, business_data.get('budget')
                )
            }

        # API monetization analysis
        if 'api_usage' in business_data:
            api_usage = business_data['api_usage']
            current_plan = business_data.get('api_plan', 'free')

            analysis['api_analysis'] = {
                'current_cost': self.api_manager.calculate_api_cost(api_usage, current_plan),
                'optimization': self.api_manager.optimize_api_pricing(
                    pd.DataFrame([api_usage]))  # Mock historical data
            }

        # Partner ecosystem analysis
        if 'partner_data' in business_data:
            partner_data = business_data['partner_data']
            analysis['partner_analysis'] = {
                'revenue_sharing': self.partner_manager.calculate_partner_revenue(
                    partner_data.get('partner_id', 'partner_1'),
                    partner_data
                ),
                'ecosystem_health': self._assess_ecosystem_health()
            }

        # Overall business recommendations
        analysis['business_recommendations'] = self._generate_business_recommendations(analysis)

        return analysis

    def _assess_ecosystem_health(self) -> Dict[str, Any]:
        """
        Assess the health of the partner ecosystem.
        """
        total_partners = len(self.partner_manager.partners)
        active_partners = sum(1 for p in self.partner_manager.partners.values()
                            if p['status'] == 'active')

        return {
            'total_partners': total_partners,
            'active_partners': active_partners,
            'activation_rate': active_partners / total_partners if total_partners > 0 else 0,
            'integrations_completed': len(self.partner_manager.integrations)
        }

    def _generate_business_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """
        Generate comprehensive business recommendations.
        """
        recommendations = []

        # Subscription recommendations
        if 'subscription_analysis' in analysis:
            sub_analysis = analysis['subscription_analysis']
            optimal_tier = sub_analysis['optimal_tier']['recommended_tier']
            current_tier = sub_analysis['current_cost']['tier']

            if optimal_tier != current_tier:
                recommendations.append(f"Consider switching from {current_tier} to {optimal_tier} tier")

        # API recommendations
        if 'api_analysis' in analysis:
            api_opt = analysis['api_analysis']['optimization']
            recommendations.extend(api_opt.get('recommendations', []))

        # Partner recommendations
        if 'partner_analysis' in analysis:
            ecosystem = analysis['partner_analysis']['ecosystem_health']
            if ecosystem['activation_rate'] < 0.8:
                recommendations.append("Focus on improving partner onboarding and activation")

        # General recommendations
        recommendations.extend([
            "Implement usage-based pricing for high-volume customers",
            "Develop partner certification programs",
            "Create marketplace for third-party integrations",
            "Establish customer success metrics for each tier"
        ])

        return recommendations

# Example usage
if __name__ == "__main__":
    business_manager = AdvancedBusinessManager()

    # Example business data
    business_data = {
        'current_usage': {
            'devices': 25,
            'api_calls': 5000,
            'storage_gb': 50
        },
        'current_tier': 'starter',
        'budget': 400,
        'api_usage': {
            'data_ingestion': 2000,
            'analytics_query': 500,
            'predictive_model': 100
        },
        'api_plan': 'developer',
        'partner_data': {
            'partner_id': 'partner_1',
            'total_revenue': 10000,
            'transactions': 500
        }
    }

    # Comprehensive business analysis
    analysis = business_manager.comprehensive_business_analysis(business_data)

    print("Advanced Business Models Analysis:")
    print(f"Current Subscription Cost: ${analysis['subscription_analysis']['current_cost']['total_cost']}")
    print(f"Recommended Tier: {analysis['subscription_analysis']['optimal_tier']['recommended_tier']}")
    print(f"API Cost: ${analysis['api_analysis']['current_cost']['total_cost']}")
    print(f"Partner Revenue Share: ${analysis['partner_analysis']['revenue_sharing']['partner_share']}")

    print(f"\nTop Business Recommendations:")
    for i, rec in enumerate(analysis['business_recommendations'][:5], 1):
        print(f"{i}. {rec}")