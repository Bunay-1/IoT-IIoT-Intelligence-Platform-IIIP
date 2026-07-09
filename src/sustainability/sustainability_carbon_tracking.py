"""
Sustainability Carbon Tracking Module

Модул за проследяване и анализ на въглеродния отпечатък:
- Activity-based изчисляване на емисии
- Поддръжка на Scopes 1, 2 и 3
- Прогнозиране на емисии
- Оптимизация за намаляване на въглеродния отпечатък
"""

import logging
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime

from src.utils.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class EmissionFactor:
    """Коефициент на емисии за дадена дейност."""
    activity_type: str
    factor: float  # kg CO2e per unit
    unit: str


class CarbonFootprintTracker:
    """Система за проследяване на въглеродните емисии."""

    def __init__(self):
        # Дефиниране на стандартни коефициенти (примерни стойности)
        self.factors = {
            "electricity": EmissionFactor("electricity", 0.475, "kWh"), # Grid average
            "natural_gas": EmissionFactor("natural_gas", 2.02, "m3"),
            "diesel": EmissionFactor("diesel", 2.68, "liter"),
            "waste": EmissionFactor("waste", 0.5, "kg"),
            "shipping": EmissionFactor("shipping", 0.15, "tonne-km")
        }
        self.logs: List[Dict[str, Any]] = []

    def log_activity(self, activity: str, value: float, scope: int):
        """Записване на дейност, генерираща емисии."""
        if activity not in self.factors:
            logger.warning(f"No emission factor found for activity: {activity}")
            return

        factor = self.factors[activity]
        emissions = value * factor.factor

        record = {
            "timestamp": datetime.now(),
            "activity": activity,
            "value": value,
            "unit": factor.unit,
            "scope": scope,
            "co2e_kg": round(emissions, 4)
        }

        self.logs.append(record)
        logger.info(f"Logged {emissions:.2f} kg CO2e for {activity} (Scope {scope})")

    def get_report(self, start_date: Optional[datetime] = None) -> Dict[str, Any]:
        """Генерира обобщен отчет за емисиите."""
        filtered_logs = self.logs
        if start_date:
            filtered_logs = [l for l in self.logs if l['timestamp'] >= start_date]

        total_emissions = sum(l['co2e_kg'] for l in filtered_logs)
        by_scope = {1: 0.0, 2: 0.0, 3: 0.0}
        by_activity = {}

        for log in filtered_logs:
            by_scope[log['scope']] += log['co2e_kg']
            act = log['activity']
            by_activity[act] = by_activity.get(act, 0.0) + log['co2e_kg']

        return {
            "total_co2e_kg": round(total_emissions, 2),
            "by_scope": {f"Scope {k}": round(v, 2) for k, v in by_scope.items()},
            "by_activity": {k: round(v, 2) for k, v in by_activity.items()},
            "log_count": len(filtered_logs)
        }


def run_demo():
    """Демонстрация на модула."""
    print("--- Sustainability Carbon Tracking Demo ---")

    tracker = CarbonFootprintTracker()

    # Scope 1: Директни емисии (природен газ)
    tracker.log_activity("natural_gas", 500, scope=1)

    # Scope 2: Индиректни емисии (електричество)
    tracker.log_activity("electricity", 1200, scope=2)

    # Scope 3: Други индиректни (доставка)
    tracker.log_activity("shipping", 2500, scope=3)

    report = tracker.get_report()
    print(f"\nОбщи емисии: {report['total_co2e_kg']} kg CO2e")
    print(f"Разпределение по обхват: {report['by_scope']}")
    print(f"Топ активност: {max(report['by_activity'], key=report['by_activity'].get)}")


if __name__ == "__main__":
    run_demo()
