# Версия на платформата: 1.2.6

FROM python:3.12-slim

# Настройка на работна директория
WORKDIR /app

# Инсталиране на системни зависимости
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    git \
    && rm -rf /var/lib/apt/lists/*

# Копиране на изискванията
COPY requirements.txt .

# Инсталиране на Python зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Изтегляне на NLP модели
RUN python -m spacy download en_core_web_sm
RUN python -c "import nltk; nltk.download('vader_lexicon'); nltk.download('punkt'); nltk.download('punkt_tab')"

# Копиране на останалия код
COPY . .

# Експониране на портове
EXPOSE 8000 8051

# Команда за стартиране (FastAPI по подразбиране)
CMD ["python", "main.py"]
