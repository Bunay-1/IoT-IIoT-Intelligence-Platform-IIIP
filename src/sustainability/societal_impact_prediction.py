"""
Societal Impact Prediction Module
A simulation tool to forecast the potential societal effects of new technologies,
policies, or large-scale projects.
"""
import numpy as np
import matplotlib.pyplot as plt
from typing import Dict, List, Any

from src.utils.logging_config import get_logger

logger = get_logger(__name__)

class SocietalImpactPredictor:
    """
    Simulates and predicts the impact of a given scenario on various societal domains.
    """
    def __init__(self, scenario_name: str, scenario_factors: Dict[str, float]):
        """
        Initializes the predictor with a specific scenario.
        Args:
            scenario_name (str): The name of the scenario (e.g., "AI Automation Wave").
            scenario_factors (Dict[str, float]): A dictionary where keys are impact factors
                                                 and values are their intensity (-1.0 to 1.0).
        """
        self.scenario_name = scenario_name
        self.scenario_factors = scenario_factors

        # Define societal domains and their baseline metrics.
        # Each domain has a weight indicating its importance in the overall impact score.
        self.societal_domains = {
            "economy": {"weight": 0.25, "metrics": {"gdp_growth": 1.0, "employment_rate": 1.0, "income_inequality": 0.0}},
            "environment": {"weight": 0.20, "metrics": {"carbon_emissions": 0.0, "resource_depletion": 0.0, "biodiversity": 1.0}},
            "health": {"weight": 0.20, "metrics": {"life_expectancy": 1.0, "access_to_care": 1.0, "mental_wellbeing": 1.0}},
            "social_equity": {"weight": 0.25, "metrics": {"poverty_rate": 0.0, "social_mobility": 1.0, "education_access": 1.0}},
            "governance": {"weight": 0.10, "metrics": {"political_stability": 1.0, "citizen_trust": 1.0, "corruption_index": 0.0}}
        }

        # Define how scenario factors influence domain metrics.
        # Key: scenario_factor, Value: Dict[domain.metric, influence_multiplier]
        # Positive multiplier means positive effect, negative means negative.
        self.impact_matrix = self._get_default_impact_matrix()

    def _get_default_impact_matrix(self) -> Dict[str, Dict[str, float]]:
        """Returns a default mapping of factors to metric impacts."""
        return {
            # Example Factors
            "ai_automation": {
                "economy.gdp_growth": 0.8, "economy.employment_rate": -0.6, "economy.income_inequality": 0.7,
                "social_equity.social_mobility": -0.4
            },
            "green_energy_transition": {
                "economy.gdp_growth": 0.4, "economy.employment_rate": 0.3,
                "environment.carbon_emissions": -0.9, "environment.resource_depletion": -0.5,
                "health.life_expectancy": 0.2
            },
            "universal_basic_income": {
                "economy.income_inequality": -0.8, "social_equity.poverty_rate": -0.9,
                "health.mental_wellbeing": 0.6, "governance.citizen_trust": 0.3
            },
            "plastic_ban": {
                "environment.biodiversity": 0.7, "environment.carbon_emissions": -0.2,
                "economy.gdp_growth": -0.1
            }
        }

    def predict_impact(self) -> Dict[str, Any]:
        """
        Runs the simulation and predicts the societal impact.
        Returns:
            Dict[str, Any]: A detailed report of the predicted impact.
        """
        predicted_metrics = {domain: metrics_data["metrics"].copy() for domain, metrics_data in self.societal_domains.items()}

        # Calculate the change for each metric based on scenario factors
        for factor, intensity in self.scenario_factors.items():
            if factor in self.impact_matrix:
                for metric_key, influence in self.impact_matrix[factor].items():
                    domain, metric = metric_key.split('.')
                    if domain in predicted_metrics and metric in predicted_metrics[domain]:
                        # A positive influence on a "negative" metric (like inequality) is bad.
                        # Metrics that are "good" when low start at 0.
                        is_negative_metric = self.societal_domains[domain]["metrics"][metric] == 0.0
                        change = intensity * influence
                        if is_negative_metric:
                            predicted_metrics[domain][metric] += change
                        else:
                            predicted_metrics[domain][metric] += change

        # Calculate domain scores and the final societal impact index
        domain_scores = self._calculate_domain_scores(predicted_metrics)

        total_weight = sum(d['weight'] for d in self.societal_domains.values())
        societal_impact_score = sum(domain_scores[domain] * self.societal_domains[domain]['weight'] for domain in domain_scores) / total_weight

        logger.info(f"Prediction for '{self.scenario_name}' complete. Societal Impact Score: {societal_impact_score:.3f}")

        return {
            "scenario_name": self.scenario_name,
            "societal_impact_score": societal_impact_score,
            "domain_scores": domain_scores,
            "predicted_metrics": predicted_metrics
        }

    def _calculate_domain_scores(self, predicted_metrics: Dict[str, Dict[str, float]]) -> Dict[str, float]:
        """Calculates the aggregated score for each societal domain."""
        domain_scores = {}
        for domain, metrics_data in self.societal_domains.items():
            baseline_metrics = metrics_data["metrics"]
            current_metrics = predicted_metrics[domain]

            score_changes = []
            for metric, baseline_value in baseline_metrics.items():
                predicted_value = current_metrics[metric]
                # If baseline is 1, it's a "good" metric (higher is better)
                # If baseline is 0, it's a "bad" metric (lower is better, so we invert the change)
                if baseline_value > 0:
                    change = predicted_value - baseline_value
                else: # Lower is better, so a negative change is a positive score
                    change = baseline_value - predicted_value
                score_changes.append(change)

            # Average the changes to get the domain score
            domain_scores[domain] = np.mean(score_changes) if score_changes else 0.0

        return domain_scores

def plot_radar_chart(results: List[Dict[str, Any]], filename: str = "societal_impact_comparison.png"):
    """
    Creates a radar chart to compare the domain scores of multiple scenarios.
    """
    labels = list(results[0]['domain_scores'].keys())
    num_vars = len(labels)

    angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))

    for result in results:
        values = list(result['domain_scores'].values())
        values += values[:1]
        ax.plot(angles, values, label=result['scenario_name'])
        ax.fill(angles, values, alpha=0.25)

    ax.set_yticklabels([])
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels)

    plt.title('Сравнение на общественото въздействие по домейни', size=20)
    plt.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1))
    plt.savefig(filename)
    logger.info(f"Радарната диаграма е запазена в {filename}")

if __name__ == '__main__':
    # --- Демонстрация на предсказване на обществено въздействие ---
    print("\n" + "="*50)
    print("ДЕМОНСТРАЦИЯ НА ПРЕДСКАЗВАНЕ НА ОБЩЕСТВЕНО ВЪЗДЕЙСТВИЕ")
    print("="*50 + "\n")

    # 1. Дефиниране на сценарии за анализ
    scenarios = [
        {
            "name": "Вълна от AI Автоматизация",
            "factors": {"ai_automation": 0.9, "green_energy_transition": 0.2}
        },
        {
            "name": "Агресивен Зелен Преход",
            "factors": {"green_energy_transition": 1.0, "plastic_ban": 0.8, "ai_automation": 0.3}
        },
        {
            "name": "Въвеждане на Универсален Базов Доход",
            "factors": {"universal_basic_income": 0.8, "ai_automation": 0.4}
        },
        {
            "name": "Пълна забрана на пластмасата",
            "factors": {"plastic_ban": 1.0, "economy.gdp_growth": -0.1} # Direct impact for demo
        }
    ]

    all_results = []

    # 2. Изпълнение на симулация за всеки сценарий
    for scenario in scenarios:
        print(f"--- Анализ на сценарий: {scenario['name']} ---")
        predictor = SocietalImpactPredictor(scenario['name'], scenario['factors'])
        result = predictor.predict_impact()
        all_results.append(result)

        print(f"  Общ индекс на обществено въздействие: {result['societal_impact_score']:.3f}")
        print("  Резултати по домейни (промяна спрямо базовото ниво):")
        for domain, score in result['domain_scores'].items():
            print(f"    - {domain.capitalize()}: {score:+.3f}")
        print("-"*(len(scenario['name']) + 24) + "\n")

    # 3. Генериране на сравнителна визуализация
    if all_results:
        plot_radar_chart(all_results)

    print("\n" + "="*50)
    print("ДЕМОНСТРАЦИЯТА ПРИКЛЮЧИ")
    print("="*50 + "\n")