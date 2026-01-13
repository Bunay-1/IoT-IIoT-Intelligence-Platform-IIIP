"""
AI Enhanced Root Cause Workshop Tool

This module provides a dual functionality:
1.  An advanced backend engine for automated, data-driven root cause analysis of
    industrial incidents using expert systems and causal inference.
2.  An interactive, AI-driven workshop simulator that facilitates a "5 Whys"
    session, using the backend engine to provide intelligent insights, and
    generates an Ishikawa (fishbone) diagram.
"""

import asyncio
import json
import logging
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union
import random

# NOTE: These imports are placeholders for a larger project structure.
# from config import settings
# from utils.logging_config import LoggerMixin
# from utils.performance_monitor import monitor_operation
# from utils.security import SecurityError, input_validator, validate_input

# Since the utils are not available, create placeholder equivalents
class LoggerMixin:
    @property
    def logger(self):
        # A basic logger that prints to console
        return logging.getLogger(self.__class__.__name__)

def monitor_operation(name):
    def decorator(func):
        return func
    return decorator

def validate_input(schema):
    def decorator(func):
        return func
    return decorator

AUTOML_AVAILABLE = False
RL_AVAILABLE = False


class RootCauseAnalysisError(Exception):
    """Base exception for root cause analysis errors."""
    pass

class AIEnhancedRootCauseWorkshopTool(LoggerMixin):
    """
    Advanced AI-powered root cause analysis tool for industrial incidents.
    (Existing class from the original file, slightly adapted for standalone use)
    """
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.confidence_threshold = self.config.get("confidence_threshold", 0.7)
        self.max_hypotheses = self.config.get("max_hypotheses", 5)
        self.error_patterns = self._initialize_error_patterns()
        self.causal_graph = self._initialize_causal_graph()
        self.logger.info("AIEnhancedRootCauseWorkshopTool (Backend Engine) initialized")

    def _initialize_error_patterns(self) -> Dict[str, Dict[str, Any]]:
        # Simplified for workshop context
        return {
            "FRONTEND_ERROR": {"description": "A UI element failed to load", "root_causes": ["javascript_bug", "cdn_issue"], "category": "Technology"},
            "BACKEND_ERROR": {"description": "API returned a 500 error", "root_causes": ["database_connection_pool_exhausted", "unhandled_exception_in_api"], "category": "Technology"},
            "PERFORMANCE_DEGRADATION": {"description": "Slow API response time", "root_causes": ["inefficient_database_query", "resource_contention"], "category": "Technology"},
            "DATA_ISSUE": {"description": "Incorrect data shown to user", "root_causes": ["data_sync_process_failed", "incorrect_data_entry"], "category": "Process"},
            "USER_ERROR": {"description": "User performed an invalid action", "root_causes": ["confusing_ui_design", "lack_of_user_training"], "category": "People"},
            "CONFIG_ERROR": {"description": "Invalid API credentials", "root_causes": ["api_credential_error"], "category": "Technology"},
            "AUTOMATION_FAILURE": {"description": "A scheduled job for rotating secrets failed", "root_causes": ["expired_api_key"], "category": "Process"}
        }

    def _initialize_causal_graph(self) -> Dict[str, List[str]]:
        # Maps higher-level problems to more specific symptoms
        return {
            "website_registrations_down": ["slow_page_load", "registration_form_error", "payment_gateway_failure"],
            "slow_page_load": ["inefficient_database_query", "large_image_files", "cdn_issue"],
            "registration_form_error": ["javascript_bug", "api_validation_error", "database_connection_pool_exhausted"],
            "payment_gateway_failure": ["api_credential_error", "network_issue_to_provider"],
            "api_credential_error": ["expired_api_key", "wrong_environment_credentials"],
        }

    async def analyze_symptoms(self, symptoms: List[str]) -> Dict[str, Any]:
        """Simplified analysis for the facilitator to use."""
        hypotheses = []
        for symptom in symptoms:
            # Check causal graph
            for cause, effects in self.causal_graph.items():
                if symptom in effects:
                    hypotheses.append({"hypothesis": f"The issue might be related to {symptom}, which could be caused by '{cause}'.", "confidence": 0.6})
            # Check error patterns
            for code, pattern in self.error_patterns.items():
                if symptom in pattern["root_causes"]:
                     hypotheses.append({"hypothesis": f"A possible cause is '{symptom}', which is a known root cause for a {pattern['description']}.", "confidence": 0.75, "category": pattern.get('category', 'Unknown')})

        # Simulate a short analysis delay
        await asyncio.sleep(0.1)

        if not hypotheses:
            return {"hypotheses": [{"hypothesis": "The underlying cause is not immediately obvious from the knowledge base. Further investigation needed.", "confidence": 0.2, "category": "Unknown"}]}

        return {"hypotheses": sorted(hypotheses, key=lambda x: x['confidence'], reverse=True)}

# --- NEW: Interactive Workshop Simulation Layer ---

class AIFacilitator:
    """
    An AI agent that guides a team through a 5 Whys root cause analysis session.
    It uses the AIEnhancedRootCauseWorkshopTool as its knowledge base.
    """
    def __init__(self, rca_engine: AIEnhancedRootCauseWorkshopTool):
        self.rca_engine = rca_engine
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info("AI Facilitator is ready.")

    async def ask_why(self, current_problem: str, level: int, visited_causes: set) -> str:
        """
        Asks "Why?" and generates a plausible next-level cause, avoiding cycles.
        """
        self.logger.info(f"[Why #{level}] Asking: Why did '{current_problem}' occur?")

        # Step 1: Drill-down from a high-level problem to a more specific, unvisited symptom.
        if current_problem in self.rca_engine.causal_graph:
            possible_symptoms = [s for s in self.rca_engine.causal_graph[current_problem] if s not in visited_causes]
            if possible_symptoms:
                # Make the choice deterministic for a better demo path
                next_symptom = possible_symptoms[0] if 'payment_gateway_failure' not in possible_symptoms else 'payment_gateway_failure'
                self.logger.info(f"Generated Answer: One of the direct symptoms was '{next_symptom}'. Let's investigate that.")
                return next_symptom, "Drill-down"

        # Step 2: Find the root cause of the current symptom, filtering out visited causes.
        analysis = await self.rca_engine.analyze_symptoms([current_problem])

        # Find the best hypothesis that doesn't lead to a cycle
        for hypothesis in analysis['hypotheses']:
            next_problem = "unknown"
            if "caused by" in hypothesis['hypothesis']:
                next_problem = hypothesis['hypothesis'].split("caused by '")[-1].replace("'.", "")
            elif "is a known root cause" in hypothesis['hypothesis']:
                next_problem = hypothesis['hypothesis'].split("'")[1]

            if next_problem not in visited_causes:
                simulated_answer = f"(AI Insight: {hypothesis['hypothesis']})"
                self.logger.info(f"Generated Answer: It seems this was because '{next_problem}'. {simulated_answer}")
                return next_problem, hypothesis.get('category', 'Uncategorized')

        # If no unvisited cause is found
        return "unknown", "Uncategorized"

class RCAWorkshop:
    """
    Manages and simulates an interactive Root Cause Analysis workshop.
    """
    def __init__(self, problem_statement: str, rca_engine: AIEnhancedRootCauseWorkshopTool):
        self.problem_statement = problem_statement
        self.facilitator = AIFacilitator(rca_engine)
        self.why_chain: List[Dict] = []
        self.ishikawa_diagram: Dict[str, List[str]] = defaultdict(list)
        self.logger = logging.getLogger(self.__class__.__name__)

    async def run_5_whys(self, max_depth: int = 5):
        """Simulates the 5 Whys process, preventing cycles."""
        self.logger.info("-" * 50)
        self.logger.info(f"Starting 5 Whys Workshop for: '{self.problem_statement}'")
        self.logger.info("-" * 50)

        current_problem = self.problem_statement
        visited_causes = {current_problem}

        for i in range(1, max_depth + 1):
            next_cause, category = await self.facilitator.ask_why(current_problem, i, visited_causes)

            self.why_chain.append({"level": i, "cause": current_problem, "next_cause": next_cause, "category": category})

            if next_cause == "unknown" or not next_cause or next_cause in visited_causes:
                if next_cause in visited_causes:
                    self.logger.warning(f"Cycle detected! Already visited '{next_cause}'. Ending chain.")
                else:
                    self.logger.warning("The AI Facilitator could not determine a deeper cause. Ending chain.")
                break

            visited_causes.add(next_cause)
            current_problem = next_cause
            await asyncio.sleep(0.5)

        self.logger.info("\n5 Whys process complete.")

    def categorize_causes(self):
        """Categorizes the findings from the 5 Whys into an Ishikawa diagram structure."""
        self.logger.info("Categorizing causes for Ishikawa (Fishbone) Diagram...")

        # Map keywords to categories
        category_map = {
            "People": ["user", "training", "design", "team"],
            "Process": ["sync", "entry", "process", "deployment"],
            "Technology": ["database", "javascript", "cdn", "api", "query", "server"],
            "Environment": ["network", "cdn", "latency"]
        }

        # Add the initial problem statement as the 'head' of the fish
        self.ishikawa_diagram['Problem'] = [self.problem_statement]

        for item in self.why_chain:
            cause_to_categorize = item['next_cause']
            assigned_category = item['category']

            # Skip adding 'unknown' to the diagram
            if cause_to_categorize == "unknown":
                continue

            # Prioritize the category from the knowledge base if available and not a drill-down step
            if assigned_category and assigned_category not in ['Uncategorized', 'Drill-down']:
                if cause_to_categorize not in self.ishikawa_diagram[assigned_category]:
                    self.ishikawa_diagram[assigned_category].append(cause_to_categorize)
                continue

            # If no direct category, infer it using keywords
            inferred_category = "General"
            for cat, keywords in category_map.items():
                if any(kw in cause_to_categorize for kw in keywords):
                    inferred_category = cat
                    break

            if cause_to_categorize not in self.ishikawa_diagram[inferred_category]:
                self.ishikawa_diagram[inferred_category].append(cause_to_categorize)

    def print_ishikawa_diagram(self):
        """Prints a text-based representation of the Ishikawa diagram."""
        print("\n" + "="*60)
        print("          ISHIKAWA (FISHBONE) DIAGRAM          ")
        print("="*60)

        problem = self.ishikawa_diagram.get("Problem", ["Unknown Problem"])[0]

        for category, causes in self.ishikawa_diagram.items():
            if category == "Problem":
                continue
            print(f"\n  {category.upper()}")
            print("    |")
            for cause in causes:
                print(f"    '--> {cause}")

        print("\n" + "-"*25 + f"//---> [ PROBLEM: {problem} ]")
        print("="*60)

async def main():
    """Main function to run the interactive workshop simulation."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # 1. Define the problem statement for the workshop
    problem = "website_registrations_down"

    # 2. Initialize the backend analysis engine
    rca_engine = AIEnhancedRootCauseWorkshopTool()

    # 3. Start and run the workshop
    workshop = RCAWorkshop(problem, rca_engine)
    await workshop.run_5_whys()

    # 4. Generate and display the final report
    workshop.categorize_causes()
    workshop.print_ishikawa_diagram()


if __name__ == "__main__":
    asyncio.run(main())
