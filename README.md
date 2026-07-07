# IoT IIoT Intelligence Platform (IIIP) 🚀

[![Python Version](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Version](https://img.shields.io/badge/version-1.0.0-green.svg)](#)
[![Docker](https://img.shields.io/badge/docker-supported-blue.svg)](https://www.docker.com/)

Интелигентна платформа за индустриален интернет на нещата (IIoT), изкуствен интелект (AI) и управление на жизнения цикъл на Industry 4.0/5.0 процеси.

---

## 📅 Последна актуализация: 22.01.2025 | Версия: 1.0.0

## 🔭 Визия
IIIP е цялостна екосистема, проектирана да обедини авангардни технологии в единна, мащабируема и високопроизводителна платформа. Тя обхваща всичко от сензорни данни в реално време и дигитални двойници до етичен изкуствен интелект, квантови симулации и блокчейн интеграция.

## 🏗 Архитектура
```mermaid
graph TD
    A[IoT Sensors / IIoT Devices] -->|Data Stream| B(Kafka)
    B --> C{Core Platform}
    C --> D[AI/ML Engine]
    C --> E[Digital Twin Engine]
    C --> F[Quality Control]
    D --> G[MLflow Tracking]
    F --> H[Dash Dashboard]
    C --> I[API Gateway]
    I --> J[External Clients]
```

## 🛠 Технологичен стек

| Категория | Технологии |
|-----------|------------|
| **Език** | ![Python](https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white) |
| **Backend** | ![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat&logo=fastapi&logoColor=white) ![Uvicorn](https://img.shields.io/badge/Uvicorn-4051B5?style=flat) |
| **ML & AI** | ![Scikit-learn](https://img.shields.io/badge/scikit--learn-%23F7931E.svg?style=flat&logo=scikit-learn&logoColor=white) ![MLflow](https://img.shields.io/badge/mlflow-%23d9ead3.svg?style=flat&logo=mlflow&logoColor=blue) ![XGBoost](https://img.shields.io/badge/XGBoost-23303E?style=flat) |
| **Frontend** | ![Dash](https://img.shields.io/badge/Dash-0081C8?style=flat&logo=plotly&logoColor=white) ![Plotly](https://img.shields.io/badge/Plotly-3F4F75?style=flat&logo=plotly&logoColor=white) |
| **Infrastructure** | ![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=flat&logo=docker&logoColor=white) ![Kafka](https://img.shields.io/badge/Apache%20Kafka-231F20?style=flat&logo=apache-kafka&logoColor=white) |

## 📦 Основни Модули

Подробна документация за всеки модул можете да намерите в директория [Docs/](Docs/).

### 🧠 Изкуствен Интелект и ML
- **`automl_engine.py`**: Усъвършенстван AutoML енджин. [[Документация](Docs/AI_ML/automl_engine.md)]
- **`automated_ml_ops.py`**: Пълен MLOps жизнен цикъл. [[Документация](Docs/AI_ML/automated_ml_ops.md)]
- **`ai_ethics_monitor.py`**: Мониторинг на етиката в AI.

### 🏭 Индустриална Автоматизация
- **`automotive_quality_control.py`**: SPC контрол с X-bar и R карти. [[Документация](Docs/Industry_4_0/automotive_quality_control.md)]
- **`digital_twin_engine.py`**: Енджин за дигитални двойници.

### 🌐 Инфраструктура и Сигурност
- **`api_gateway_management.py`**: Асинхронен API Gateway. [[Документация](Docs/Infrastructure/api_gateway_management.md)]
- **`blockchain_integration.py`**: Блокчейн за IoT данни.

## 🐳 Контейнеризация (Docker)

Платформата е напълно контейнеризирана.

**Стартиране с Docker Compose:**
```bash
docker-compose up --build
```

## 🔧 Инсталация (Локално)

1. Клонирайте хранилището:
   ```bash
   git clone <repository-url>
   ```
2. Инсталирайте зависимостите:
   ```bash
   pip install -r requirements.txt
   ```
3. Изтеглете NLP моделите:
   ```bash
   python -m spacy download en_core_web_sm
   ```

## 🛡 Лиценз
Този проект е лицензиран под MIT Лиценз – вижте файла [LICENSE](LICENSE) за подробности.

---
© 2025 IoT IIoT Intelligence Platform Team.
