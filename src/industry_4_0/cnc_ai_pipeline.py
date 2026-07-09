"""
CNC AI Pipeline Module

Този модул имплементира цялостно управление на CNC машини с AI възможности:
- AI-базирана оптимизация на параметрите
- Предсказваща поддръжка (Predictive Maintenance) чрез RandomForest
- Мониторинг на качеството и ефективността в реално време
- Интегрирана симулация на индустриални процеси
"""

import asyncio
import logging
import time
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass, asdict
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.preprocessing import StandardScaler

from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class MachineStatus(Enum):
    """Статуси на CNC машините."""
    IDLE = "idle"
    RUNNING = "running"
    MAINTENANCE = "maintenance"
    ERROR = "error"
    OFFLINE = "offline"


class OptimizationType(Enum):
    """Типове оптимизация."""
    SPEED = "speed"
    QUALITY = "quality"
    EFFICIENCY = "efficiency"
    ENERGY = "energy"


@dataclass
class CNCMachine:
    """Представяне на CNC машина."""
    machine_id: str
    name: str
    status: MachineStatus
    current_speed: float
    optimal_speed: float
    quality_score: float
    efficiency: float
    energy_consumption: float
    last_maintenance: datetime
    operating_hours: int
    error_count: int


@dataclass
class OptimizationResult:
    """Резултат от AI оптимизация."""
    machine_id: str
    optimization_type: OptimizationType
    original_value: float
    optimized_value: float
    improvement_percentage: float
    timestamp: datetime
    confidence: float


class CNCAIEngine:
    """Усъвършенстван AI енджин за CNC оптимизация и прогнозиране."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or self._default_config()
        self.machines: Dict[str, CNCMachine] = {}
        self.optimization_history: List[OptimizationResult] = []

        # ML Модели
        self.maintenance_model = RandomForestRegressor(n_estimators=100, random_state=42)
        self.quality_model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.scaler = StandardScaler()
        self.is_trained = False
        
        self._initialize_sample_machines()
        self._pretrain_models()
        
    def _default_config(self) -> Dict[str, Any]:
        """Конфигурация по подразбиране."""
        return {
            "optimization_interval": 300,
            "quality_threshold": 95.0,
            "maintenance_warning_threshold": 0.75,
            "energy_optimization_enabled": True
        }
    
    def _initialize_sample_machines(self):
        """Инициализация на демонстрационни машини."""
        sample_data = [
            ("CNC-V1", "HAAS VF3", MachineStatus.RUNNING, 8000, 8500, 94.5, 87.2, 12.5, 30, 8760, 3),
            ("CNC-V2", "DMG MORI", MachineStatus.RUNNING, 6000, 6500, 96.8, 91.5, 10.2, 15, 6520, 1),
            ("CNC-V3", "MAZAK VTC", MachineStatus.MAINTENANCE, 0, 7000, 92.1, 82.3, 8.5, 2, 4320, 5)
        ]
        
        for mid, name, status, speed, opt_speed, qual, eff, energy, days_ago, hours, errors in sample_data:
            self.machines[mid] = CNCMachine(
                machine_id=mid,
                name=name,
                status=status,
                current_speed=speed,
                optimal_speed=opt_speed,
                quality_score=qual,
                efficiency=eff,
                energy_consumption=energy,
                last_maintenance=datetime.now() - timedelta(days=days_ago),
                operating_hours=hours,
                error_count=errors
            )

    def _pretrain_models(self):
        """Предварително обучение на моделите със симулирани данни."""
        logger.info("Pre-training CNC AI models...")

        # Данни за поддръжка (RUL - Remaining Useful Life)
        # Features: [operating_hours, error_count, temperature, vibration]
        X_train = np.array([
            [100, 0, 30, 0.5], [500, 1, 35, 0.8], [1000, 2, 40, 1.2],
            [2000, 5, 45, 2.0], [5000, 10, 50, 3.5], [8000, 20, 60, 5.0]
        ])
        y_train_rul = np.array([1000, 800, 600, 400, 100, 0])

        self.maintenance_model.fit(X_train, y_train_rul)

        # Данни за качество
        y_train_quality = np.array([1, 1, 1, 0, 0, 0]) # 1: Good, 0: Defect
        self.quality_model.fit(X_train, y_train_quality)

        self.is_trained = True
        logger.info("CNC AI models trained successfully.")

    async def optimize_parameters(self, machine_id: str, goal: OptimizationType) -> OptimizationResult:
        """Оптимизиране на параметрите на машината чрез AI логика."""
        if machine_id not in self.machines:
            raise ValueError(f"Machine {machine_id} not found.")

        machine = self.machines[machine_id]
        original_val = 0.0
        optimized_val = 0.0

        # Симулация на сложна оптимизационна логика
        if goal == OptimizationType.SPEED:
            original_val = machine.current_speed
            # Оптимална скорост базирана на качество и ефективност
            optimized_val = machine.optimal_speed * (machine.quality_score / 100.0) * (machine.efficiency / 100.0)
            machine.current_speed = optimized_val

        elif goal == OptimizationType.ENERGY:
            original_val = machine.energy_consumption
            # Намаляване на консумацията чрез фина настройка
            optimized_val = original_val * 0.92
            machine.energy_consumption = optimized_val

        improvement = ((optimized_val - original_val) / original_val * 100) if original_val != 0 else 0
        
        result = OptimizationResult(
            machine_id=machine_id,
            optimization_type=goal,
            original_value=original_val,
            optimized_value=optimized_val,
            improvement_percentage=abs(improvement),
            timestamp=datetime.now(),
            confidence=np.random.uniform(0.85, 0.99)
        )
        
        self.optimization_history.append(result)
        logger.info(f"Optimization ({goal.value}) for {machine_id}: {result.improvement_percentage:.2f}% improvement.")
        return result

    async def predict_maintenance(self, machine_id: str) -> Dict[str, Any]:
        """Прогнозиране на нуждата от поддръжка."""
        machine = self.machines.get(machine_id)
        if not machine:
            return {"error": "Machine not found"}

        # Симулирани сензорни данни
        temp = np.random.uniform(35, 55)
        vibration = np.random.uniform(0.5, 4.0)
        
        features = np.array([[machine.operating_hours, machine.error_count, temp, vibration]])
        predicted_rul = self.maintenance_model.predict(features)[0]
        
        # Изчисляване на вероятност за повреда
        failure_prob = 1.0 - (predicted_rul / 1000.0)
        failure_prob = max(0, min(failure_prob, 1.0))

        return {
            "machine_id": machine_id,
            "predicted_remaining_life_hours": round(predicted_rul, 2),
            "failure_probability": round(failure_prob, 4),
            "urgent_maintenance_required": failure_prob > self.config["maintenance_warning_threshold"],
            "timestamp": datetime.now().isoformat()
        }

    async def get_machine_telemetry(self, machine_id: str) -> Dict[str, Any]:
        """Връща пълна телеметрия за машината в реално време."""
        machine = self.machines.get(machine_id)
        if not machine:
            return {"error": "Machine not found"}

        return {
            **asdict(machine),
            "status": machine.status.value,
            "last_maintenance": machine.last_maintenance.isoformat(),
            "environment_temp": round(np.random.uniform(22, 28), 2),
            "spindle_vibration": round(np.random.uniform(0.01, 0.15), 4)
        }

    def get_summary_report(self) -> Dict[str, Any]:
        """Генерира обобщен отчет за всички машини."""
        total_machines = len(self.machines)
        running = sum(1 for m in self.machines.values() if m.status == MachineStatus.RUNNING)
        avg_quality = np.mean([m.quality_score for m in self.machines.values()])
        
        return {
            "total_machines": total_machines,
            "active_machines": running,
            "average_fleet_quality": round(avg_quality, 2),
            "optimization_count": len(self.optimization_history)
        }


# Global instance
engine = CNCAIEngine()


async def run_demo():
    """Демонстрация на функционалността на CNC AI Pipeline."""
    print("--- CNC AI Pipeline Demo ---")

    # 1. Списък на машините
    print("\n[1] Налични машини:")
    for m_id, machine in engine.machines.items():
        print(f"- {m_id}: {machine.name} | Статус: {machine.status.value}")

    # 2. Оптимизация
    print("\n[2] Изпълнение на AI оптимизация на скоростта за CNC-V1...")
    opt_res = await engine.optimize_parameters("CNC-V1", OptimizationType.SPEED)
    print(f"Резултат: {opt_res.improvement_percentage:.2f}% подобрение. Доверие: {opt_res.confidence:.2%}")

    # 3. Предсказваща поддръжка
    print("\n[3] Прогнозиране на поддръжка за CNC-V2...")
    maint_pred = await engine.predict_maintenance("CNC-V2")
    print(f"Оставащ полезен живот: {maint_pred['predicted_remaining_life_hours']} часа")
    print(f"Вероятност за повреда: {maint_pred['failure_probability']:.2%}")

    # 4. Телеметрия
    print("\n[4] Телеметрия в реално време за CNC-V3:")
    telemetry = await engine.get_machine_telemetry("CNC-V3")
    print(f"Ефективност: {telemetry['efficiency']}% | Температура: {telemetry['environment_temp']}°C")

    # 5. Обобщен отчет
    print("\n[5] Обобщен отчет за флота:")
    report = engine.get_summary_report()
    print(report)


if __name__ == "__main__":
    asyncio.run(run_demo())
