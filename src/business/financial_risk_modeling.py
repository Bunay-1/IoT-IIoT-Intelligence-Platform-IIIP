"""
Financial Risk Modeling Module

This module provides AI-powered financial risk assessment and modeling for industrial operations.
It includes predictive analytics for financial risks, investment optimization, cost forecasting,
and risk mitigation strategies for manufacturing and industrial enterprises.

Features:
- Financial risk prediction and assessment
- Investment portfolio optimization
- Cost forecasting and budget optimization
- Risk mitigation strategy recommendations
- Financial KPI monitoring and alerting
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from sklearn.ensemble import RandomForestRegressor, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import warnings
warnings.filterwarnings('ignore')

class FinancialRiskPredictor:
    """
    Predicts financial risks using machine learning models.
    """

    def __init__(self):
        self.risk_model = GradientBoostingClassifier(n_estimators=100, random_state=42)
        self.cost_predictor = RandomForestRegressor(n_estimators=100, random_state=42)
        self.scaler = StandardScaler()
        self.is_trained = False

    def train_models(self, historical_data: pd.DataFrame):
        """
        Train the financial risk models.

        Args:
            historical_data: Historical financial and operational data
        """
        # Prepare features for risk prediction
        risk_features = [
            'revenue', 'costs', 'profit_margin', 'debt_ratio', 'cash_flow',
            'inventory_turnover', 'asset_utilization', 'market_volatility',
            'supplier_risk_score', 'regulatory_compliance_score'
        ]

        # Prepare features for cost prediction
        cost_features = [
            'production_volume', 'labor_costs', 'material_costs', 'energy_costs',
            'maintenance_costs', 'overhead_costs', 'market_prices'
        ]

        # Risk classification target (0: low risk, 1: high risk)
        risk_target = (historical_data['profit_margin'] < 0.05).astype(int)

        # Cost prediction target
        cost_target = historical_data['total_costs']

        # Train risk model
        X_risk = historical_data[risk_features]
        X_risk_scaled = self.scaler.fit_transform(X_risk)
        self.risk_model.fit(X_risk_scaled, risk_target)

        # Train cost predictor
        X_cost = historical_data[cost_features]
        self.cost_predictor.fit(X_cost, cost_target)

        self.is_trained = True

    def predict_financial_risk(self, current_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Predict financial risk level.

        Args:
            current_data: Current financial and operational data

        Returns:
            Dict[str, Any]: Risk assessment results
        """
        if not self.is_trained:
            return {"error": "Model not trained"}

        risk_features = [
            'revenue', 'costs', 'profit_margin', 'debt_ratio', 'cash_flow',
            'inventory_turnover', 'asset_utilization', 'market_volatility',
            'supplier_risk_score', 'regulatory_compliance_score'
        ]

        # Extract features
        features = np.array([[current_data.get(f, 0) for f in risk_features]])
        features_scaled = self.scaler.transform(features)

        # Predict risk probability
        risk_probability = float(self.risk_model.predict_proba(features_scaled)[0][1])

        # Determine risk level
        if risk_probability > 0.7:
            risk_level = "critical"
        elif risk_probability > 0.5:
            risk_level = "high"
        elif risk_probability > 0.3:
            risk_level = "medium"
        else:
            risk_level = "low"

        # Identify key risk factors
        risk_factors = self._identify_risk_factors(current_data)

        return {
            "risk_probability": risk_probability,
            "risk_level": risk_level,
            "key_risk_factors": risk_factors,
            "recommendations": self._generate_risk_recommendations(risk_level, risk_factors),
            "confidence_score": 0.85  # Mock confidence score
        }

    def forecast_costs(self, forecast_data: Dict[str, Any], periods: int = 12) -> Dict[str, Any]:
        """
        Forecast future costs.

        Args:
            forecast_data: Data for cost forecasting
            periods: Number of periods to forecast

        Returns:
            Dict[str, Any]: Cost forecast results
        """
        if not self.is_trained:
            return {"error": "Model not trained"}

        cost_features = [
            'production_volume', 'labor_costs', 'material_costs', 'energy_costs',
            'maintenance_costs', 'overhead_costs', 'market_prices'
        ]

        # Extract features
        features = np.array([[forecast_data.get(f, 0) for f in cost_features]])

        # Predict costs
        predicted_cost = float(self.cost_predictor.predict(features)[0])

        # Generate forecast with confidence intervals
        forecasts = []
        for i in range(periods):
            # Add some variation for different periods
            variation = np.random.normal(0, 0.1)
            period_cost = predicted_cost * (1 + variation + i * 0.02)  # Slight upward trend

            forecasts.append({
                "period": i + 1,
                "predicted_cost": round(period_cost, 2),
                "confidence_lower": round(period_cost * 0.9, 2),
                "confidence_upper": round(period_cost * 1.1, 2)
            })

        return {
            "current_predicted_cost": round(predicted_cost, 2),
            "forecasts": forecasts,
            "total_forecast_cost": round(sum(f["predicted_cost"] for f in forecasts), 2),
            "cost_trend": "increasing" if periods > 6 else "stable"
        }

    def _identify_risk_factors(self, data: Dict[str, Any]) -> List[str]:
        """
        Identify key financial risk factors.

        Args:
            data: Financial data

        Returns:
            List[str]: List of risk factors
        """
        factors = []

        if data.get('profit_margin', 1) < 0.05:
            factors.append("Low profit margin")
        if data.get('debt_ratio', 0) > 0.7:
            factors.append("High debt ratio")
        if data.get('cash_flow', 1) < 0:
            factors.append("Negative cash flow")
        if data.get('supplier_risk_score', 0) > 7:
            factors.append("High supplier risk")
        if data.get('regulatory_compliance_score', 10) < 7:
            factors.append("Poor regulatory compliance")
        if data.get('market_volatility', 0) > 0.8:
            factors.append("High market volatility")

        return factors

    def _generate_risk_recommendations(self, risk_level: str, risk_factors: List[str]) -> List[str]:
        """
        Generate risk mitigation recommendations.

        Args:
            risk_level: Risk level
            risk_factors: Identified risk factors

        Returns:
            List[str]: Recommendations
        """
        recommendations = []

        if risk_level == "critical":
            recommendations.extend([
                "Immediate cash flow management required",
                "Urgent debt restructuring needed",
                "Consider emergency financing options"
            ])
        elif risk_level == "high":
            recommendations.extend([
                "Implement cost reduction measures",
                "Diversify supplier base",
                "Strengthen cash reserves"
            ])
        elif risk_level == "medium":
            recommendations.extend([
                "Monitor key financial metrics closely",
                "Develop contingency plans",
                "Review pricing strategy"
            ])

        # Specific recommendations based on factors
        for factor in risk_factors:
            if "profit margin" in factor.lower():
                recommendations.append("Optimize pricing and cost structure")
            if "debt" in factor.lower():
                recommendations.append("Negotiate better credit terms")
            if "cash flow" in factor.lower():
                recommendations.append("Improve accounts receivable collection")
            if "supplier" in factor.lower():
                recommendations.append("Diversify supplier relationships")
            if "compliance" in factor.lower():
                recommendations.append("Address regulatory compliance issues")

        return list(set(recommendations))  # Remove duplicates

class InvestmentOptimizer:
    """
    Optimizes investment portfolios for industrial operations.
    """

    def __init__(self):
        self.portfolio_model = RandomForestRegressor(n_estimators=100, random_state=42)

    def optimize_portfolio(self, available_investments: List[Dict[str, Any]],
                          budget: float, risk_tolerance: str = "medium") -> Dict[str, Any]:
        """
        Optimize investment portfolio.

        Args:
            available_investments: List of available investment options
            budget: Total investment budget
            risk_tolerance: Risk tolerance level (low, medium, high)

        Returns:
            Dict[str, Any]: Optimized portfolio
        """
        # Mock optimization logic
        risk_weights = {
            "low": {"equipment": 0.4, "r&d": 0.3, "facilities": 0.2, "training": 0.1},
            "medium": {"equipment": 0.3, "r&d": 0.3, "facilities": 0.2, "training": 0.2},
            "high": {"equipment": 0.2, "r&d": 0.4, "facilities": 0.2, "training": 0.2}
        }

        weights = risk_weights.get(risk_tolerance, risk_weights["medium"])

        portfolio = []
        remaining_budget = budget

        for investment in available_investments:
            investment_type = investment.get("type", "equipment")
            weight = weights.get(investment_type, 0.2)

            allocation = min(remaining_budget * weight, investment.get("max_allocation", remaining_budget))
            if allocation > 0:
                portfolio.append({
                    "investment_id": investment["id"],
                    "name": investment["name"],
                    "allocation": round(allocation, 2),
                    "expected_roi": investment.get("expected_roi", 0.1),
                    "risk_level": investment.get("risk_level", "medium")
                })
                remaining_budget -= allocation

        total_allocation = sum(p["allocation"] for p in portfolio)
        expected_return = sum(p["allocation"] * p["expected_roi"] for p in portfolio)

        return {
            "portfolio": portfolio,
            "total_allocation": round(total_allocation, 2),
            "expected_annual_return": round(expected_return, 2),
            "expected_roi": round(expected_return / total_allocation if total_allocation > 0 else 0, 4),
            "risk_tolerance": risk_tolerance,
            "unallocated_budget": round(budget - total_allocation, 2)
        }

class FinancialKPIMonitor:
    """
    Monitors financial KPIs and generates alerts.
    """

    def __init__(self):
        self.kpi_thresholds = {
            "profit_margin": {"warning": 0.05, "critical": 0.02},
            "debt_ratio": {"warning": 0.6, "critical": 0.8},
            "current_ratio": {"warning": 1.2, "critical": 1.0},
            "inventory_turnover": {"warning": 4, "critical": 2},
            "cash_flow_coverage": {"warning": 1.5, "critical": 1.0}
        }

    def monitor_kpis(self, kpi_data: Dict[str, float]) -> Dict[str, Any]:
        """
        Monitor financial KPIs and generate alerts.

        Args:
            kpi_data: Current KPI values

        Returns:
            Dict[str, Any]: KPI monitoring results
        """
        alerts = []
        status_summary = {"normal": 0, "warning": 0, "critical": 0}

        for kpi_name, value in kpi_data.items():
            if kpi_name in self.kpi_thresholds:
                thresholds = self.kpi_thresholds[kpi_name]

                if kpi_name in ["debt_ratio"]:  # Higher values are worse
                    if value >= thresholds["critical"]:
                        status = "critical"
                    elif value >= thresholds["warning"]:
                        status = "warning"
                    else:
                        status = "normal"
                else:  # Lower values are worse
                    if value <= thresholds["critical"]:
                        status = "critical"
                    elif value <= thresholds["warning"]:
                        status = "warning"
                    else:
                        status = "normal"

                status_summary[status] += 1

                if status != "normal":
                    alerts.append({
                        "kpi": kpi_name,
                        "value": value,
                        "threshold": thresholds["warning"] if status == "warning" else thresholds["critical"],
                        "status": status,
                        "message": f"{kpi_name} is {status}: {value}"
                    })

        overall_status = "critical" if status_summary["critical"] > 0 else "warning" if status_summary["warning"] > 0 else "normal"

        return {
            "overall_status": overall_status,
            "status_summary": status_summary,
            "alerts": alerts,
            "monitored_kpis": len(kpi_data),
            "timestamp": datetime.utcnow()
        }

class IndustrialFinancialRiskManager:
    """
    Comprehensive financial risk management system for industrial operations.
    """

    def __init__(self):
        self.risk_predictor = FinancialRiskPredictor()
        self.investment_optimizer = InvestmentOptimizer()
        self.kpi_monitor = FinancialKPIMonitor()

    def comprehensive_risk_assessment(self, financial_data: Dict[str, Any],
                                    operational_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform comprehensive financial risk assessment.

        Args:
            financial_data: Financial metrics
            operational_data: Operational metrics

        Returns:
            Dict[str, Any]: Comprehensive risk assessment
        """
        # Combine financial and operational data
        combined_data = {**financial_data, **operational_data}

        # Risk prediction
        risk_assessment = self.risk_predictor.predict_financial_risk(combined_data)

        # Cost forecasting
        cost_forecast = self.risk_predictor.forecast_costs(combined_data)

        # KPI monitoring
        kpi_data = {
            "profit_margin": financial_data.get("profit_margin", 0.1),
            "debt_ratio": financial_data.get("debt_ratio", 0.5),
            "current_ratio": financial_data.get("current_ratio", 1.5),
            "inventory_turnover": operational_data.get("inventory_turnover", 6),
            "cash_flow_coverage": financial_data.get("cash_flow_coverage", 2.0)
        }

        kpi_monitoring = self.kpi_monitor.monitor_kpis(kpi_data)

        return {
            "risk_assessment": risk_assessment,
            "cost_forecast": cost_forecast,
            "kpi_monitoring": kpi_monitoring,
            "overall_risk_score": self._calculate_overall_risk_score(
                risk_assessment, kpi_monitoring
            ),
            "action_priority": self._determine_action_priority(risk_assessment, kpi_monitoring)
        }

    def _calculate_overall_risk_score(self, risk_assessment: Dict, kpi_monitoring: Dict) -> float:
        """
        Calculate overall risk score from multiple assessments.
        """
        risk_score = risk_assessment.get("risk_probability", 0) * 0.6
        kpi_score = (kpi_monitoring["status_summary"]["critical"] * 0.4 +
                    kpi_monitoring["status_summary"]["warning"] * 0.2) / len(kpi_monitoring.get("alerts", [])) if kpi_monitoring.get("alerts") else 0
        kpi_score = min(kpi_score, 1.0)  # Cap at 1.0

        return round((risk_score + kpi_score) / 2, 3)

    def _determine_action_priority(self, risk_assessment: Dict, kpi_monitoring: Dict) -> str:
        """
        Determine action priority based on assessments.
        """
        risk_level = risk_assessment.get("risk_level", "low")
        kpi_status = kpi_monitoring.get("overall_status", "normal")

        if risk_level == "critical" or kpi_status == "critical":
            return "immediate_action_required"
        elif risk_level == "high" or kpi_status == "warning":
            return "high_priority"
        elif risk_level == "medium":
            return "medium_priority"
        else:
            return "monitor_closely"

# Example usage
if __name__ == "__main__":
    # Initialize financial risk manager
    risk_manager = IndustrialFinancialRiskManager()

    # Mock historical data for training
    historical_data = pd.DataFrame({
        'revenue': np.random.normal(1000000, 100000, 100),
        'costs': np.random.normal(800000, 80000, 100),
        'profit_margin': np.random.normal(0.15, 0.05, 100),
        'debt_ratio': np.random.normal(0.4, 0.1, 100),
        'cash_flow': np.random.normal(150000, 30000, 100),
        'inventory_turnover': np.random.normal(6, 1, 100),
        'asset_utilization': np.random.normal(0.8, 0.1, 100),
        'market_volatility': np.random.normal(0.3, 0.1, 100),
        'supplier_risk_score': np.random.normal(4, 1, 100),
        'regulatory_compliance_score': np.random.normal(8, 1, 100),
        'production_volume': np.random.normal(10000, 1000, 100),
        'labor_costs': np.random.normal(200000, 20000, 100),
        'material_costs': np.random.normal(300000, 30000, 100),
        'energy_costs': np.random.normal(50000, 5000, 100),
        'maintenance_costs': np.random.normal(80000, 8000, 100),
        'overhead_costs': np.random.normal(150000, 15000, 100),
        'market_prices': np.random.normal(100, 10, 100),
        'total_costs': np.random.normal(780000, 78000, 100)
    })

    # Train models
    risk_manager.risk_predictor.train_models(historical_data)
    print("Models trained on historical data")

    # Current financial data
    current_financial = {
        'revenue': 950000,
        'costs': 820000,
        'profit_margin': 0.136,
        'debt_ratio': 0.55,
        'cash_flow': 120000,
        'inventory_turnover': 5.2,
        'asset_utilization': 0.75,
        'market_volatility': 0.6,
        'supplier_risk_score': 6.5,
        'regulatory_compliance_score': 7.8
    }

    current_operational = {
        'production_volume': 9500,
        'labor_costs': 210000,
        'material_costs': 320000,
        'energy_costs': 55000,
        'maintenance_costs': 85000,
        'overhead_costs': 160000,
        'market_prices': 105,
        'inventory_turnover': 5.2,
        'current_ratio': 1.3,
        'cash_flow_coverage': 1.8
    }

    # Comprehensive risk assessment
    assessment = risk_manager.comprehensive_risk_assessment(current_financial, current_operational)
    print("Comprehensive risk assessment:")
    print(f"Overall risk score: {assessment['overall_risk_score']}")
    print(f"Risk level: {assessment['risk_assessment']['risk_level']}")
    print(f"Action priority: {assessment['action_priority']}")
    print(f"KPI status: {assessment['kpi_monitoring']['overall_status']}")

    # Investment optimization
    investments = [
        {"id": "equip_upgrade", "name": "Equipment Upgrade", "type": "equipment", "max_allocation": 200000, "expected_roi": 0.15, "risk_level": "medium"},
        {"id": "r&d_project", "name": "R&D Innovation", "type": "r&d", "max_allocation": 150000, "expected_roi": 0.20, "risk_level": "high"},
        {"id": "facility_expansion", "name": "Facility Expansion", "type": "facilities", "max_allocation": 300000, "expected_roi": 0.12, "risk_level": "medium"},
        {"id": "training_program", "name": "Employee Training", "type": "training", "max_allocation": 50000, "expected_roi": 0.25, "risk_level": "low"}
    ]

    portfolio = risk_manager.investment_optimizer.optimize_portfolio(investments, 500000, "medium")
    print(f"\nOptimized portfolio total allocation: ${portfolio['total_allocation']}")
    print(f"Expected ROI: {portfolio['expected_roi']:.1%}")
    print(f"Unallocated budget: ${portfolio['unallocated_budget']}")