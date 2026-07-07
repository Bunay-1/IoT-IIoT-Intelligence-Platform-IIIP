# Документация: Advanced Analytics

## Описание
Модулът `advanced_analytics.py` предоставя разширени инструменти за статистически анализ и машинно обучение върху индустриални данни.

## Ключови функционалности
- **PCA (Principal Component Analysis)**: Намаляване на размерността на данните за идентифициране на ключови фактори.
- **Клъстеризация (K-Means)**: Автоматично групиране на данни/сензори за откриване на скрити зависимости.
- **Визуализация на клъстери**: Генериране на 2D графики за разпределението на клъстерите.

## Употреба
```python
from advanced_analytics import AdvancedAnalytics

analytics = AdvancedAnalytics()
clusters = analytics.perform_clustering(data, n_clusters=3)
```
