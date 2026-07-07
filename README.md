# IoT IIoT Intelligence Platform (IIIP) 🚀

[![Python Version](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Version](https://img.shields.io/badge/version-1.1.0-green.svg)](#)
[![Docker](https://img.shields.io/badge/docker-supported-blue.svg)](https://www.docker.com/)

Интелигентна платформа за индустриален интернет на нещата (IIoT), изкуствен интелект (AI) и управление на жизнения цикъл на Industry 4.0/5.0 процеси.

---

## 📅 Последна актуализация: 22.01.2025 | Версия: 1.1.0 (Advanced AI Update)

## 🔭 Визия
IIIP е цялостна екосистема, проектирана да обедини авангардни технологии в единна, мащабируема и високопроизводителна платформа. Тя обхваща всичко от сензорни данни в реално време и дигитални двойници до етичен изкуствен интелект, квантови симулации и блокчейн интеграция.

## 🏗 Архитектура
```mermaid
graph TD
    A[IoT Sensors / IIoT Devices] -->|Data Stream| B(Kafka)
    B --> C{Core Platform}
    C --> D[Advanced AI Engine]
    C --> E[Digital Twin / RUL]
    C --> F[Quality / SPC / FMEA]
    D --> G[MLflow Tracking]
    F --> H[Dash Dashboard]
    C --> I[API Gateway]
    I --> J[External Clients]
    D --> K[Ethics Monitor]
```

## 🛠 Технологичен стек

| Категория | Технологии |
|-----------|------------|
| **Език** | ![Python](https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white) |
| **Backend** | ![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat&logo=fastapi&logoColor=white) ![Aiohttp](https://img.shields.io/badge/Aiohttp-2C5BB4?style=flat) |
| **ML & AI** | ![Scikit-learn](https://img.shields.io/badge/scikit--learn-%23F7931E.svg?style=flat&logo=scikit-learn&logoColor=white) ![Pandas](https://img.shields.io/badge/Pandas-150458?style=flat&logo=pandas&logoColor=white) ![MLflow](https://img.shields.io/badge/mlflow-%23d9ead3.svg?style=flat&logo=mlflow&logoColor=blue) |
| **Frontend** | ![Dash](https://img.shields.io/badge/Dash-0081C8?style=flat&logo=plotly&logoColor=white) ![Plotly](https://img.shields.io/badge/Plotly-3F4F75?style=flat&logo=plotly&logoColor=white) |
| **Infrastructure** | ![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=flat&logo=docker&logoColor=white) ![Kafka](https://img.shields.io/badge/Apache%20Kafka-231F20?style=flat&logo=apache-kafka&logoColor=white) |

## 📦 Основни Модули

Подробна документация за всеки модул можете да намерите в директория [Docs/](Docs/).

### 🧠 Изкуствен Интелект и ML
- **`advanced_analytics.py`**: PCA, клъстеризация и детекция на аномалии. [[Документация](Docs/AI_ML/advanced_analytics.md)]
- **`ai_ethics_monitor.py`**: Етичен надзор и анализ на пристрастия. [[Документация](Docs/AI_ML/ai_ethics_monitor.md)]
- **`automl_engine.py`**: Усъвършенстван AutoML енджин.
- **`automated_ml_ops.py`**: Пълен MLOps жизнен цикъл.

### 🏭 Индустриална Автоматизация (Industry 5.0)
- **`automotive_quality_control.py`**: SPC и FMEA анализ. [[Документация](Docs/Industry_4_0/automotive_quality_control.md)]
- **`digital_twin_engine.py`**: Дигитални двойници и RUL прогнози. [[Документация](Docs/Industry_4_0/digital_twin_engine.md)]
- **`cnc_ai_pipeline.py`**: Интелигентно управление на CNC.

### 🌐 Инфраструктура и Устойчивост
- **`api_gateway_management.py`**: Асинхронен API Gateway.
- **`sustainability_carbon_tracking.py`**: Проследяване на емисии (Scopes 1-3).

## 🐳 Контейнеризация (Docker)
```bash
docker-compose up --build
```

## 🛡 Лиценз
MIT Лиценз – вижте [LICENSE](LICENSE) за подробности.

---
© 2025 IoT IIoT Intelligence Platform Team.
