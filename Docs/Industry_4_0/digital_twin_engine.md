# Документация: Digital Twin Engine

## Описание
`digital_twin_engine.py` е ядрото за управление на дигитални двойници в платформата.

## Ключови функционалности
- **Asset Health Monitoring**: Динамично изчисляване на здравен индекс (0-100) базиран на телеметрия.
- **RUL Prediction**: Прогнозиране на оставащия полезен живот чрез `GradientBoostingRegressor`.
- **Fleet Management**: Обобщен анализ на състоянието на целия машинен парк.
- **Telemetry History**: Съхранение и анализ на исторически данни за всеки актив.

## Употреба
```python
from digital_twin_engine import DigitalTwinEngine

engine = DigitalTwinEngine()
twin = engine.create_twin("ID-001", {"type": "Motor"})
twin.update_telemetry({"temperature": 75, "vibration": 1.5})
```
