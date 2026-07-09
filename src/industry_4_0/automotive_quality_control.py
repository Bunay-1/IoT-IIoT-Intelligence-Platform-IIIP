"""
Automotive Quality Control Module (SPC & FMEA)

Интегрирана система за качествен контрол:
- Статистически процесен контрол (SPC)
- Изчисляване на Cp/Cpk индекси
- FMEA (Failure Mode and Effects Analysis)
- Визуализация на контролни карти
"""

import logging
import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime

from src.utils.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class FMEARecord:
    """Запис за FMEA анализ."""
    process_step: str
    potential_failure_mode: str
    potential_effect: str
    severity: int  # 1-10
    occurrence: int # 1-10
    detection: int # 1-10
    rpn: int = field(init=False)

    def __post_init__(self):
        self.rpn = self.severity * self.occurrence * self.detection


class StatisticalProcessControl:
    """Управление на статистическия процесен контрол."""

    def __init__(self, target: float, usl: float, lsl: float):
        self.target = target
        self.usl = usl
        self.lsl = lsl
        self.measurements = []
        logger.info(f"SPC initialized for Target: {target}, Limits: [{lsl}, {usl}]")

    def add_batch(self, data: List[float]):
        """Добавяне на партида от измервания."""
        self.measurements.extend(data)
        logger.debug(f"Added {len(data)} measurements.")

    def calculate_metrics(self) -> Dict[str, float]:
        """Изчислява ключови SPC метрики."""
        if len(self.measurements) < 2:
            return {}

        mean = np.mean(self.measurements)
        std = np.std(self.measurements, ddof=1)

        # Индекси на способност
        cp = (self.usl - self.lsl) / (6 * std) if std > 0 else 0
        cpu = (self.usl - mean) / (3 * std) if std > 0 else 0
        cpl = (mean - self.lsl) / (3 * std) if std > 0 else 0
        cpk = min(cpu, cpl)

        return {
            "mean": round(float(mean), 4),
            "std": round(float(std), 4),
            "cp": round(float(cp), 4),
            "cpk": round(float(cpk), 4),
            "is_capable": cpk >= 1.33
        }

    def get_control_limits(self) -> Dict[str, float]:
        """Изчислява контролните граници (3-sigma)."""
        if not self.measurements:
            return {}
        
        mean = np.mean(self.measurements)
        std = np.std(self.measurements, ddof=1)
        
        return {
            "ucl": round(float(mean + 3 * std), 4),
            "lcl": round(float(mean - 3 * std), 4),
            "cl": round(float(mean), 4)
        }


class AutomotiveQualityManager:
    """Главен мениджър по качеството."""

    def __init__(self):
        self.spc_modules: Dict[str, StatisticalProcessControl] = {}
        self.fmea_records: List[FMEARecord] = []

    def register_process(self, name: str, target: float, usl: float, lsl: float):
        """Регистрира нов процес за мониторинг."""
        self.spc_modules[name] = StatisticalProcessControl(target, usl, lsl)

    def add_fmea_entry(self, **kwargs):
        """Добавя нов FMEA запис."""
        entry = FMEARecord(**kwargs)
        self.fmea_records.append(entry)
        logger.info(f"FMEA entry added for {entry.process_step}. RPN: {entry.rpn}")

    def get_quality_health(self) -> Dict[str, Any]:
        """Връща обобщено състояние на качеството."""
        health = {
            "processes": {},
            "critical_rpn_count": sum(1 for r in self.fmea_records if r.rpn > 100)
        }

        for name, spc in self.spc_modules.items():
            health["processes"][name] = spc.calculate_metrics()

        return health


def run_demo():
    """Демонстрация на модула."""
    print("--- Automotive Quality Control Demo ---")

    manager = AutomotiveQualityManager()

    # 1. SPC
    manager.register_process("Piston Diameter", 80.0, 80.05, 79.95)
    measurements = np.random.normal(80.002, 0.015, 50).tolist()
    manager.spc_modules["Piston Diameter"].add_batch(measurements)

    # 2. FMEA
    manager.add_fmea_entry(
        process_step="Casting",
        potential_failure_mode="Porosity",
        potential_effect="Structural weakness",
        severity=8, occurrence=3, detection=5
    )

    health = manager.get_quality_health()
    print(f"\nСтатус на процесите: {health['processes']}")
    print(f"Критични RPN записи: {health['critical_rpn_count']}")


if __name__ == "__main__":
    run_demo()
