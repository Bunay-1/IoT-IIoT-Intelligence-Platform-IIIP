"""
System Integration Test

Тестване на интегрираната работа на множество модули:
1. Advanced Analytics
2. Automotive Quality Control
3. Digital Twin Engine
4. Carbon Tracking
5. AI Ethics
"""

import asyncio
import pandas as pd
import numpy as np
from datetime import datetime

from src.ai_ml.advanced_analytics import AdvancedAnalytics
from src.industry_4_0.automotive_quality_control import AutomotiveQualityManager
from src.industry_4_0.digital_twin_engine import DigitalTwinEngine
from src.sustainability.sustainability_carbon_tracking import CarbonFootprintTracker
from src.ai_ml.ai_ethics_monitor import AIEthicsMonitor

async def run_system_test():
    print("=== STARTING SYSTEM INTEGRATION TEST (v1.1.0) ===")

    # 1. AI Ethics Check
    ethics = AIEthicsMonitor()
    prompt_res = ethics.check_prompt_safety("Analyze factory performance for optimization.")
    print(f"[Ethics] Safety Check: {'PASSED' if prompt_res['is_safe'] else 'FAILED'}")

    # 2. Advanced Analytics
    analytics = AdvancedAnalytics()
    data = pd.DataFrame(np.random.normal(50, 10, (50, 4)), columns=['t', 'v', 'p', 'l'])
    report = analytics.generate_analytics_report(data)
    print(f"[Analytics] Anomalies found: {report['anomalies_found']}")

    # 3. Quality Control
    quality = AutomotiveQualityManager()
    quality.register_process("Assembly", 10.0, 10.1, 9.9)
    quality.spc_modules["Assembly"].add_batch(np.random.normal(10, 0.02, 20).tolist())
    q_health = quality.get_quality_health()
    print(f"[Quality] Assembly Cpk: {q_health['processes']['Assembly']['cpk']}")

    # 4. Digital Twin & RUL
    twins = DigitalTwinEngine()
    t = twins.create_twin("Twin-01", {"type": "Pump"})
    for _ in range(30):
        t.update_telemetry({"temperature": 60, "vibration": 1.1, "load": 85})
    t.train_predictive_model()
    rul = t.predict_remaining_life({"temperature": 65, "vibration": 1.2, "load": 80})
    print(f"[Digital Twin] Predicted RUL: {rul:.2f} hours")

    # 5. Carbon Tracking
    carbon = CarbonFootprintTracker()
    carbon.log_activity("electricity", 500, scope=2)
    c_report = carbon.get_report()
    print(f"[Sustainability] Total Emissions: {c_report['total_co2e_kg']} kg")

    print("\n=== SYSTEM INTEGRATION TEST COMPLETED SUCCESSFULLY ===")

if __name__ == "__main__":
    asyncio.run(run_system_test())
