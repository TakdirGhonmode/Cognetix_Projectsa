import pandas as pd
import numpy as np
import logging
from typing import Dict, Any, Tuple, List

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("RiskScorer")


class RiskScorer:
    """
    Calculates weighted risk scores (0-100) for transactions based on triggered rules,
    rule weights, and frequency. Strictly classifies risk into 3 categories:
    - LOW (0 - 39)
    - MEDIUM (40 - 69)
    - HIGH (70 - 100)
    """

    DEFAULT_WEIGHTS = {
        "HighAmountRule": 25,
        "RapidVelocityRule": 30,
        "GeographicalAnomalyRule": 20,
        "FailedPaymentRule": 15,
        "BlacklistRule": 40,
        "SpikeDetectionRule": 20
    }

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.weights = config.get("rule_weights", self.DEFAULT_WEIGHTS)
        self.risk_categories = config.get("risk_scoring", {
            "low": {"min": 0, "max": 39, "label": "LOW"},
            "medium": {"min": 40, "max": 69, "label": "MEDIUM"},
            "high": {"min": 70, "max": 100, "label": "HIGH"}
        })

    def categorize_risk(self, score: int) -> str:
        """
        Classifies numerical risk score strictly into LOW, MEDIUM, or HIGH.
        """
        if score <= 39:
            return "LOW"
        elif score <= 69:
            return "MEDIUM"
        else:
            return "HIGH"

    def calculate_scores(self, df: pd.DataFrame, rule_results: Dict[str, pd.Series]) -> pd.DataFrame:
        """
        Computes composite risk score and risk level for every transaction in df.
        """
        df_out = df.copy()

        scores = np.zeros(len(df_out), dtype=int)
        triggered_rules_list: List[List[str]] = [[] for _ in range(len(df_out))]
        rule_counts = np.zeros(len(df_out), dtype=int)

        for rule_name, series in rule_results.items():
            weight = self.weights.get(rule_name, 15)
            mask = series.values

            # Add weight to score where rule triggered
            scores += (mask * weight)

            # Record rule names
            for idx, is_triggered in enumerate(mask):
                if is_triggered:
                    triggered_rules_list[idx].append(rule_name)
                    rule_counts[idx] += 1

        # Cap score between 0 and 100
        scores = np.clip(scores, 0, 100)

        # Categorize risk levels
        risk_levels = [self.categorize_risk(s) for s in scores]

        df_out["Risk Score"] = scores
        df_out["Risk Level"] = risk_levels
        df_out["Triggered Rules"] = triggered_rules_list
        df_out["Rule Count"] = rule_counts
        df_out["Is Flagged"] = df_out["Risk Score"] >= 30  # Flagged if Risk Score >= 30 or any high rule triggered

        high_count = sum(1 for lvl in risk_levels if lvl == "HIGH")
        med_count = sum(1 for lvl in risk_levels if lvl == "MEDIUM")
        low_count = sum(1 for lvl in risk_levels if lvl == "LOW")

        logger.info(f"Risk Scoring Completed: HIGH={high_count}, MEDIUM={med_count}, LOW={low_count}")

        return df_out
