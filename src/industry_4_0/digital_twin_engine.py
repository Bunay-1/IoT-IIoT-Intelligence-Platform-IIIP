"""
Digital Twin Engine Module

Модул за създаване и управление на дигитални двойници (Digital Twins):
- Предсказваща поддръжка (RUL)
- Оптимизация на симулации
- Мониторинг на здравето на активите
"""

import logging
import numpy as np
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from sklearn.ensemble import GradientBoostingRegressor

from src.utils.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class AssetHealth:
    """Здравословно състояние на актив."""
    score: float  # 0-100
    status: str
    predicted_failure_date: Optional[datetime]
    last_update: datetime = field(default_factory=datetime.now)


class DigitalTwin:
    """Представяне на дигитален двойник на индустриален актив."""

    def __init__(self, asset_id: str, metadata: Dict[str, Any]):
        self.asset_id = asset_id
        self.metadata = metadata
        self.telemetry_history: List[Dict[str, Any]] = []
        self.health = AssetHealth(100.0, "Healthy", None)

        # Модел за прогнозиране
        self.prediction_model = GradientBoostingRegressor(n_estimators=50, random_state=42)
        self._is_model_trained = False

    def update_telemetry(self, data: Dict[str, Any]):
        """Обновяване на състоянието на двойника с нови данни."""
        data['timestamp'] = datetime.now()
        self.telemetry_history.append(data)
        self._analyze_health(data)

        # Поддържане на лимит на историята
        if len(self.telemetry_history) > 1000:
            self.telemetry_history.pop(0)

    def _analyze_health(self, latest_data: Dict[str, Any]):
        """Вътрешен анализ на здравето."""
        # Опростена логика за демонстрация
        temp = latest_data.get('temperature', 0)
        vibration = latest_data.get('vibration', 0)

        score = 100.0
        if temp > 80: score -= 20
        if vibration > 2.0: score -= 30

        self.health.score = max(0.0, score)
        self.health.status = "Warning" if score < 70 else "Healthy"
        if score < 40: self.health.status = "Critical"

        self.health.last_update = datetime.now()

    def train_predictive_model(self):
        """Обучение на модела за RUL (Remaining Useful Life)."""
        if len(self.telemetry_history) < 20:
            logger.warning(f"Not enough data to train model for {self.asset_id}")
            return

        # Симулиране на обучаващо множество от историята
        X = np.array([[d.get('temperature', 0), d.get('vibration', 0), d.get('load', 0)] for d in self.telemetry_history])
        y = np.linspace(1000, 0, len(self.telemetry_history)) # Симулиран RUL

        self.prediction_model.fit(X, y)
        self._is_model_trained = True
        logger.info(f"Predictive model trained for asset {self.asset_id}")

    def predict_remaining_life(self, current_telemetry: Dict[str, Any]) -> float:
        """Прогнозира оставащия живот в часове."""
        if not self._is_model_trained:
            return -1.0

        X_now = np.array([[current_telemetry.get('temperature', 0),
                           current_telemetry.get('vibration', 0),
                           current_telemetry.get('load', 0)]])
        prediction = self.prediction_model.predict(X_now)
        return float(prediction[0])


class DigitalTwinEngine:
    """Управляващ енджин за множество дигитални двойници."""

    def __init__(self):
        self.twins: Dict[str, DigitalTwin] = {}

    def create_twin(self, asset_id: str, metadata: Dict[str, Any]) -> DigitalTwin:
        """Създава нов дигитален двойник."""
        twin = DigitalTwin(asset_id, metadata)
        self.twins[asset_id] = twin
        logger.info(f"Digital Twin created for asset {asset_id}")
        return twin

    def get_fleet_health(self) -> Dict[str, Any]:
        """Връща обобщена информация за здравето на всички активи."""
        return {
            "total_assets": len(self.twins),
            "healthy_count": sum(1 for t in self.twins.values() if t.health.status == "Healthy"),
            "critical_count": sum(1 for t in self.twins.values() if t.health.status == "Critical"),
            "average_health_score": np.mean([t.health.score for t in self.twins.values()]) if self.twins else 0
        }


def run_demo():
    """Демонстрация на модула."""
    print("--- Digital Twin Engine Demo ---")

    engine = DigitalTwinEngine()
    twin = engine.create_twin("Robot-Arm-01", {"type": "FANUC", "location": "Sector A"})

    # Симулиране на данни
    for _ in range(25):
        twin.update_telemetry({
            "temperature": np.random.uniform(50, 90),
            "vibration": np.random.uniform(0.5, 3.0),
            "load": np.random.uniform(60, 100)
        })

    twin.train_predictive_model()
    rul = twin.predict_remaining_life({"temperature": 65, "vibration": 1.2, "load": 80})

    print(f"\nСтатус на актива: {twin.health.status} (Score: {twin.health.score})")
    print(f"Прогнозиран оставащ живот: {rul:.2f} часа")
    print(f"Здраве на целия флот: {engine.get_fleet_health()}")


if __name__ == "__main__":
    run_demo()
