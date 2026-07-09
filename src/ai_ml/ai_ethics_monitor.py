"""
AI Ethics Monitor Module

Модул за мониторинг и контрол на етиката в AI системите:
- Детекция на пристрастия (Bias Detection)
- Проверка за токсичност и безопасност
- Одит на решенията на моделите
- LLM Guardrails симулация
"""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class AIEthicsMonitor:
    """Система за етичен надзор над AI моделите."""

    def __init__(self):
        self.audit_logs: List[Dict[str, Any]] = []
        self.safety_rules = {
            "toxic_keywords": ["hate", "harm", "kill", "exploit"],
            "sensitive_groups": ["race", "gender", "religion", "age"]
        }

    def check_prompt_safety(self, prompt: str) -> Dict[str, Any]:
        """Проверява входящия промпт за етични рискове."""
        violations = []
        lower_prompt = prompt.lower()
        
        for word in self.safety_rules["toxic_keywords"]:
            if word in lower_prompt:
                violations.append(f"Toxic content detected: {word}")

        is_safe = len(violations) == 0

        result = {
            "is_safe": is_safe,
            "violations": violations,
            "risk_level": "High" if len(violations) > 0 else "Low"
        }

        self._log_audit("prompt_check", {"prompt": prompt, "result": result})
        return result

    def analyze_model_bias(self, predictions: List[Any], sensitive_features: List[Any]) -> Dict[str, float]:
        """Анализира предсказанията на модела за признаци на пристрастие."""
        # Опростена проверка за демографска паритетност
        df = pd.DataFrame({"pred": predictions, "group": sensitive_features})
        group_rates = df.groupby("group")["pred"].mean().to_dict()

        max_rate = max(group_rates.values())
        min_rate = min(group_rates.values())
        disparity = max_rate - min_rate

        result = {
            "group_rates": group_rates,
            "max_disparity": round(disparity, 4),
            "bias_detected": disparity > 0.1
        }

        self._log_audit("bias_analysis", result)
        return result

    def _log_audit(self, event_type: str, details: Dict[str, Any]):
        """Записване на етичен одит."""
        log_entry = {
            "timestamp": datetime.now(),
            "event": event_type,
            "details": details
        }
        self.audit_logs.append(log_entry)
        if details.get("bias_detected") or details.get("risk_level") == "High":
            logger.warning(f"ETHICS ALERT: {event_type} - {details}")

    def generate_ethics_report(self) -> Dict[str, Any]:
        """Генерира обобщен доклад за етичното състояние на системата."""
        return {
            "total_checks": len(self.audit_logs),
            "alerts_count": sum(1 for l in self.audit_logs if "detected" in str(l) or "High" in str(l)),
            "last_check": self.audit_logs[-1]["timestamp"] if self.audit_logs else None
        }


import pandas as pd # Needed for analysis

def run_demo():
    """Демонстрация на модула."""
    print("--- AI Ethics Monitor Demo ---")

    monitor = AIEthicsMonitor()

    # 1. Проверка на промпт
    safe_check = monitor.check_prompt_safety("How can I improve factory efficiency?")
    unsafe_check = monitor.check_prompt_safety("How to harm a competitor's network?")

    print(f"\nPrompt 1 (Safe): {safe_check['is_safe']}")
    print(f"Prompt 2 (Unsafe): {unsafe_check['is_safe']} | Риск: {unsafe_check['risk_level']}")

    # 2. Анализ на пристрастия
    preds = [1, 0, 1, 1, 0, 1, 0, 0]
    groups = ['A', 'A', 'B', 'B', 'A', 'B', 'A', 'B']
    bias_res = monitor.analyze_model_bias(preds, groups)

    print(f"\nАнализ на пристрастия: {bias_res['group_rates']}")
    print(f"Открит риск от пристрастие: {bias_res['bias_detected']}")


if __name__ == "__main__":
    run_demo()
