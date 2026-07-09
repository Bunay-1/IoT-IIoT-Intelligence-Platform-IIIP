import pandas as pd
import json
import re
import argparse
from collections import defaultdict

class AutomaticDatasetLabeler:
    def __init__(self, rules_path):
        """
        Инициализира системата за автоматично етикетиране.
        Args:
            rules_path (str): Път до JSON файла с правилата за етикетиране.
        """
        self.rules = self._load_rules(rules_path)
        print(f"Заредени са правила за етикетиране за категории: {list(self.rules.keys())}")

    def _load_rules(self, rules_path):
        """Зарежда и валидира правилата от JSON файл."""
        try:
            with open(rules_path, 'r') as f:
                rules = json.load(f)
            # Проста валидация на структурата
            for label, conditions in rules.items():
                if not isinstance(conditions, dict) or not ('keywords' in conditions or 'regex' in conditions):
                    raise ValueError(f"Невалидна структура за етикет '{label}' в {rules_path}")
            return rules
        except FileNotFoundError:
            print(f"Грешка: Файлът с правила '{rules_path}' не е намерен.")
            return {}
        except json.JSONDecodeError:
            print(f"Грешка: Невалиден JSON формат в '{rules_path}'.")
            return {}

    def _apply_rules_to_text(self, text):
        """
        Прилага правилата към единичен текст, за да намери най-добрия етикет.
        Връща етикета с най-много съвпадения.
        """
        if not isinstance(text, str) or not text:
            return "Unlabeled"

        text_lower = text.lower()
        scores = defaultdict(int)

        for label, conditions in self.rules.items():
            # Проверка по ключови думи
            for keyword in conditions.get('keywords', []):
                if keyword.lower() in text_lower:
                    scores[label] += 1

            # Проверка по регулярни изрази
            for pattern in conditions.get('regex', []):
                if re.search(pattern, text_lower, re.IGNORECASE):
                    scores[label] += 1

        if not scores:
            return "Unlabeled"

        # Връщане на етикета с най-висок резултат
        return max(scores, key=scores.get)

    def label_dataframe(self, df, text_column):
        """
        Етикетира цял DataFrame.
        Args:
            df (pd.DataFrame): DataFrame за етикетиране.
            text_column (str): Името на колоната, съдържаща текста за анализ.
        Returns:
            pd.DataFrame: DataFrame с добавена колона 'auto_label'.
        """
        if text_column not in df.columns:
            raise ValueError(f"Колоната '{text_column}' не е намерена в DataFrame-а.")

        print(f"Прилагане на правила върху колона '{text_column}'...")
        df['auto_label'] = df[text_column].apply(self._apply_rules_to_text)
        print("Етикетирането завърши.")
        return df

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Автоматично етикетиране на данни.")
    parser.add_argument(
        '--rules',
        type=str,
        default='labeling_rules.json',
        help='Път до JSON файла с правила за етикетиране.'
    )
    args = parser.parse_args()

    # --- Демонстрационна симулация ---

    # 1. Създаване на примерен набор от данни
    sample_data = {
        'product_description': [
            "Brand new smartphone with 128GB storage and a great camera.",
            "Comfortable cotton sweater, perfect for autumn.",
            "A historical novel set during the Second World War.",
            "4K LED TV with HDR support and smart features.",
            "Classic leather shoes, available in black and brown.",
            "This is a high-performance gaming console.",
            "A sci-fi biography about an astronaut.",
            "Wooden coffee maker for a stylish kitchen.",
            "Running shoes with advanced cushioning technology.",
            "This product has no matching keywords.",
            "A collection of paperback book classics.",
            "", # Празен ред
            None # Липсваща стойност
        ]
    }
    df_unlabeled = pd.DataFrame(sample_data)
    print("--- Първоначални данни (без етикети) ---")
    print(df_unlabeled)
    print("-" * 40)

    # 2. Инициализация и стартиране на системата за етикетиране
    try:
        labeler = AutomaticDatasetLabeler(rules_path=args.rules)
        if labeler.rules:
            df_labeled = labeler.label_dataframe(df_unlabeled, text_column='product_description')

            # 3. Показване на резултата
            print("\n--- Данни след автоматично етикетиране ---")
            print(df_labeled)
            print("-" * 40)

            # 4. Показване на обобщена статистика
            print("\n--- Обобщена статистика на етикетите ---")
            print(df_labeled['auto_label'].value_counts())
            print("-" * 40)

    except Exception as e:
        print(f"Възникна грешка по време на изпълнение: {e}")
