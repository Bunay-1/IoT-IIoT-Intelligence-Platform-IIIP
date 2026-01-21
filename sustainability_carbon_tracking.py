"""
Sustainability and Carbon Tracking Module

This module provides comprehensive carbon footprint tracking, green AI optimization,
and circular economy support for industrial operations. It enables real-time monitoring
of environmental impact, optimization of energy consumption, and sustainable decision-making.

Features:
- Real-time carbon footprint calculation
- Green AI optimization (energy-efficient models)
- Circular economy analytics
- Sustainability KPI monitoring
- Environmental impact assessment
- Renewable energy integration tracking
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any
from datetime import datetime
import matplotlib.pyplot as plt
import warnings

from utils.logging_config import get_logger

warnings.filterwarnings('ignore')
logger = get_logger(__name__)

class CarbonFootprintTracker:
    """
    Tracks and calculates carbon footprint for industrial operations, categorized by Scope 1, 2, and 3.
    """

    def __init__(self):
        # Emission factors (kg CO2e per unit)
        self.emission_factors = {
            # Scope 1: Direct emissions
            'natural_gas_m3': {'factor': 2.0, 'scope': 1},
            'diesel_liter': {'factor': 2.7, 'scope': 1},
            'petrol_liter': {'factor': 2.3, 'scope': 1},
            'company_vehicles_km': {'factor': 0.18, 'scope': 1}, # Avg for cars

            # Scope 2: Indirect emissions from purchased energy
            'electricity_kwh': {'factor': 0.4, 'scope': 2},

            # Scope 3: Other indirect emissions
            'purchased_goods_value': {'factor': 0.5, 'scope': 3}, # kg CO2e per EUR/USD
            'waste_disposal_ton': {'factor': 500, 'scope': 3}, # Methane emissions
            'business_travel_km': {'factor': 0.15, 'scope': 3}, # Air travel
            'employee_commuting_km': {'factor': 0.12, 'scope': 3},
        }

        self.activities = []
        self.baseline_emissions = {}

    def log_activity(self, activity_type: str, value: float, unit: str, date: datetime = None):
        """Logs a single business activity that produces emissions."""
        if date is None:
            date = datetime.utcnow()

        self.activities.append({
            "date": date,
            "activity": activity_type,
            "value": value,
            "unit": unit
        })

    def calculate_footprint(self) -> Dict[str, Any]:
        """
        Calculates the total carbon footprint from all logged activities,
        broken down by scope.
        """
        if not self.activities:
            return {"total_emissions": 0, "by_scope": {}, "by_activity": {}}

        report = {
            "total_emissions": 0.0,
            "by_scope": {1: 0.0, 2: 0.0, 3: 0.0},
            "by_activity": {}
        }

        for activity_log in self.activities:
            key = f"{activity_log['activity']}_{activity_log['unit']}"
            if key in self.emission_factors:
                ef_data = self.emission_factors[key]
                emissions = activity_log['value'] * ef_data['factor']

                report['total_emissions'] += emissions
                report['by_scope'][ef_data['scope']] += emissions

                activity_name = activity_log['activity']
                if activity_name not in report['by_activity']:
                    report['by_activity'][activity_name] = 0.0
                report['by_activity'][activity_name] += emissions

        # Round the results for cleaner output
        for activity, value in report['by_activity'].items():
            report['by_activity'][activity] = round(value, 2)
        for scope, value in report['by_scope'].items():
            report['by_scope'][scope] = round(value, 2)
        report['total_emissions'] = round(report['total_emissions'], 2)

        return report

    def generate_report(self) -> Dict[str, Any]:
        """
        Generates a comprehensive report including footprint, trends, and recommendations.
        """
        footprint_data = self.calculate_footprint()

        recommendations = self._generate_recommendations(footprint_data)
        baseline_comparison = self._compare_to_baseline(footprint_data.get('total_emissions', 0))

        footprint_data['recommendations'] = recommendations
        footprint_data['baseline_comparison'] = baseline_comparison

        logger.info("Carbon footprint report generated successfully.")
        return footprint_data

    def _generate_recommendations(self, footprint: Dict[str, Any]) -> List[str]:
        """
        Generate sustainability recommendations based on the footprint breakdown.
        """
        recommendations = []
        total = footprint.get('total_emissions', 0)
        if total == 0:
            return ["Log activities to generate recommendations."]

        by_scope = footprint.get('by_scope', {})

        # Scope 1 Recommendations
        if by_scope.get(1, 0) / total > 0.3:
            recommendations.append("Focus on reducing direct emissions: upgrade fleet to EVs, improve on-site fuel efficiency.")

        # Scope 2 Recommendations
        if by_scope.get(2, 0) / total > 0.4:
            recommendations.append("Address energy consumption: switch to a renewable electricity provider or install on-site generation (solar).")

        # Scope 3 Recommendations
        if by_scope.get(3, 0) / total > 0.3:
            recommendations.append("Engage with supply chain to reduce Scope 3 emissions: prioritize sustainable suppliers and promote employee commuting alternatives.")

        if not recommendations:
            recommendations.append("Emissions are well-balanced. Focus on continuous improvement across all scopes.")

        return recommendations

    def _compare_to_baseline(self, current_emissions: float) -> Dict[str, Any]:
        """
        Compare current emissions to baseline.
        """
        if not self.baseline_emissions:
            self.baseline_emissions = {
                'value': current_emissions,
                'timestamp': datetime.utcnow()
            }
            return {"status": "baseline_set", "comparison": "N/A"}

        baseline = self.baseline_emissions['value']
        difference = current_emissions - baseline
        percent_change = (difference / baseline) * 100 if baseline > 0 else 0

        return {
            "baseline_value": round(baseline, 2),
            "current_value": round(current_emissions, 2),
            "difference": round(difference, 2),
            "percent_change": round(percent_change, 2),
            "status": "improving" if percent_change < 0 else "worsening"
        }

if __name__ == "__main__":

    def plot_scope_distribution(report: Dict[str, Any], filename="carbon_footprint_scopes.png"):
        """Generates a pie chart for the emissions distribution by scope."""
        labels = [f"Scope {s}" for s in report['by_scope'].keys()]
        sizes = report['by_scope'].values()

        fig, ax = plt.subplots(figsize=(8, 8))
        ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90, colors=['#ff9999','#66b3ff','#99ff99'])
        ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.

        plt.title(f"Разпределение на емисиите по категории\nОбщо: {report['total_emissions']} kg CO2e", pad=20)
        plt.savefig(filename)
        logger.info(f"Графиката с разпределението по категории е запазена в {filename}")

    # --- Демонстрация на проследяване на въглероден отпечатък ---
    print("\n" + "="*50)
    print("ДЕМОНСТРАЦИЯ НА ПРОСЛЕДЯВАНЕ НА ВЪГЛЕРОДЕН ОТПЕЧАТЪК")
    print("="*50 + "\n")

    # 1. Инициализация на тракера
    tracker = CarbonFootprintTracker()
    logger.info("Системата за проследяване е инициализирана.")

    # 2. Симулация и регистриране на дейности за един месец
    print("Регистриране на симулирани бизнес дейности...")
    tracker.log_activity("electricity", 15000, "kwh") # Scope 2
    tracker.log_activity("natural_gas", 2000, "m3") # Scope 1
    tracker.log_activity("company_vehicles", 5000, "km") # Scope 1
    tracker.log_activity("purchased_goods", 25000, "value") # Scope 3
    tracker.log_activity("waste_disposal", 15, "ton") # Scope 3
    tracker.log_activity("business_travel", 12000, "km") # Scope 3
    tracker.log_activity("employee_commuting", 40000, "km") # Scope 3
    logger.info(f"Регистрирани са {len(tracker.activities)} дейности.")
    print("-" * 50 + "\n")

    # 3. Генериране на подробен доклад
    print("Генериране на доклад за въглеродния отпечатък...")
    final_report = tracker.generate_report()

    print(f"\nОБЩ ВЪГЛЕРОДЕН ОТПЕЧАТЪК: {final_report['total_emissions']} kg CO2e\n")

    print("Разбивка по категории (Scopes):")
    for scope, emissions in final_report['by_scope'].items():
        percentage = (emissions / final_report['total_emissions']) * 100 if final_report['total_emissions'] > 0 else 0
        print(f"  - Scope {scope}: {emissions} kg CO2e ({percentage:.1f}%)")

    print("\nРазбивка по дейности:")
    for activity, emissions in final_report['by_activity'].items():
        print(f"  - {activity.replace('_', ' ').capitalize()}: {emissions} kg CO2e")

    print("\nСравнение с базова линия:")
    baseline_info = final_report['baseline_comparison']
    if baseline_info['status'] == 'baseline_set':
        print("  - Базовата линия е зададена сега. При следващо изчисление ще има сравнение.")
    else:
        print(f"  - Статус: {baseline_info['status']} ({baseline_info['percent_change']:.1f}%)")

    print("\nПрепоръки за намаляване на емисиите:")
    for rec in final_report['recommendations']:
        print(f"  - {rec}")

    print("\n" + "-" * 50)

    # 4. Генериране на визуализация
    if final_report['total_emissions'] > 0:
        plot_scope_distribution(final_report)

    print("\n" + "="*50)
    print("ДЕМОНСТРАЦИЯТА ПРИКЛЮЧИ")
    print("="*50 + "\n")
