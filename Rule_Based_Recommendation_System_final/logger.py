import json
import logging
import os
from datetime import datetime
from models import insert_decision_log

logger = logging.getLogger("DecisionLogger")


class DecisionLogger:
    def __init__(self, config_path="config.json"):
        self.config_path = config_path
        self.log_file_path = self._load_log_file_path()

    def _load_log_file_path(self):
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            return config.get("logging", {}).get("log_file_path", "recommendations_log.txt")
        except Exception:
            return "recommendations_log.txt"

    def log_decision(self, user_id: str, recommendations: list):
        """
        Record recommendation decision logs to both:
        1. recommendations_log.txt
        2. decision_logs MySQL table
        """
        timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        applied_rules = list(set([r.get("applied_rule", r.get("rule_name", "UNKNOWN")) for r in recommendations]))
        rec_products = [r.get("product_id") for r in recommendations]
        scores = {r.get("product_id"): r.get("relevance_score") for r in recommendations}

        # 1. Log to text file recommendations_log.txt
        log_entry_lines = [
            f"=" * 60,
            f"TIMESTAMP        : {timestamp_str}",
            f"USER ID          : {user_id}",
            f"APPLIED RULES    : {', '.join(applied_rules) if applied_rules else 'None'}",
            f"RECOMMENDATIONS  :",
        ]
        for r in recommendations:
            log_entry_lines.append(
                f"  Rank #{r.get('rank_order')} | Product: {r.get('product_id')} | Score: {r.get('relevance_score')} | Rule: {r.get('applied_rule')} | Reason: {r.get('reason')}"
            )
        log_entry_lines.append("=" * 60 + "\n")

        with open(self.log_file_path, "a", encoding="utf-8") as f:
            f.write("\n".join(log_entry_lines) + "\n")

        logger.info(f"Decision logged to text file '{self.log_file_path}'.")

        # 2. Log to MySQL database decision_logs table
        try:
            insert_decision_log(
                user_id=user_id,
                applied_rules=applied_rules,
                recommendations=rec_products,
                relevance_scores=scores,
                timestamp=timestamp_str,
                config_path=self.config_path
            )
            logger.info(f"Decision logged to MySQL 'decision_logs' table for user {user_id}.")
        except Exception as e:
            logger.error(f"Failed to log decision to MySQL decision_logs table: {e}")
