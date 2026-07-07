# Документация: Advanced Analytics

## Описание
Модулът `advanced_analytics.py` предоставя високо ниво на аналитични възможности чрез машинно обучение. Проектиран е за обработка на големи масиви от индустриални данни.

## Ключови функционалности
- **PCA (Principal Component Analysis)**: Автоматично намаляване на размерността с отчет за обяснената вариация.
- **Интелигентна клъстеризация**: Поддръжка на KMeans и Gaussian Mixture Models (GMM).
- **Isolation Forest**: Усъвършенствано откриване на аномалии в реално време.
- **Статистическо отчитане**: Генериране на JSON-базирани отчети за разпределението на данните.

## Употреба
```python
from advanced_analytics import AdvancedAnalytics

analytics = AdvancedAnalytics()
report = analytics.generate_analytics_report(data_frame)
```

## Технически изисквания
- `scikit-learn`
- `pandas`
- `numpy`
- `matplotlib`
