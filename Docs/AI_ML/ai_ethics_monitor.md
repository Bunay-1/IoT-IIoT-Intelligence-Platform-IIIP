# Документация: AI Ethics Monitor

## Описание
Модулът `ai_ethics_monitor.py` осигурява етичен надзор и съответствие на AI моделите и промпт-овете.

## Ключови функционалности
- **Safety Guardrails**: Проверка на входящи промпт-ове за токсичност и чувствителни теми.
- **Bias Analysis**: Изчисляване на демографска паритетност и откриване на пристрастия в предсказанията.
- **Ethics Auditing**: Детайлно логване на всяко решение, свързано с безопасността.
- **Risk Level Assessment**: Автоматично определяне на нивото на риск (Low/High).

## Употреба
```python
from ai_ethics_monitor import AIEthicsMonitor

monitor = AIEthicsMonitor()
safety = monitor.check_prompt_safety("Your text here")
```
