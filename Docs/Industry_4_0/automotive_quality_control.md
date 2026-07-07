# Документация: Automotive Quality Control

## Описание
Модулът `automotive_quality_control.py` е фокусиран върху осигуряването на качеството в производството чрез Статистически Процесен Контрол (SPC).

## Ключови функционалности
- **Контролни карти**: Генериране на X-bar и R карти за мониторинг на стабилността на процеса.
- **Анализ на възможностите (Cp/Cpk)**: Изчисляване на индекси за процесна способност.
- **Визуализация**: Автоматично генериране на графики с контролни граници (UCL, LCL).
- **FMEA Интеграция**: Поддръжка на анализ на видовете и ефектите от откази.

## Употреба
```python
from automotive_quality_control import StatisticalProcessControl

spc = StatisticalProcessControl(process_name="Cylinder Boring")
spc.add_measurements(data)
fig = spc.generate_control_charts()
```
