import os
import json
import unittest
import pandas as pd
from datetime import datetime, timedelta

from database import get_db_connection, initialize_database
from models import seed_database_if_empty, fetch_all_users, fetch_all_products
from validator import DataValidator
from rule_engine import RuleEngine
from scorer import RecommendationScorer
from ranking import RecommendationRanker
from optimizer import RecommendationOptimizer
from logger import DecisionLogger
from reports import ReportGenerator


class TestRuleBasedRecommendationSystem(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up test environment and config."""
        cls.config_path = "config.json"
        try:
            initialize_database(cls.config_path)
            seed_database_if_empty(cls.config_path)
        except Exception as e:
            print(f"Warning in Test Setup (Database initialized or offline): {e}")

    # 1. Test Database Connectivity
    def test_database_connectivity(self):
        try:
            conn = get_db_connection(self.config_path, include_db=True)
            self.assertIsNotNone(conn)
            cursor = conn.cursor()
            cursor.execute("SELECT 1;")
            res = cursor.fetchone()
            cursor.close()
            conn.close()
            self.assertEqual(res[0], 1)
        except Exception as e:
            self.skipTest(f"MySQL server not reachable locally: {e}")

    # 2. Test Data Validation Layer
    def test_data_validation(self):
        validator = DataValidator()

        raw_df = pd.DataFrame([
            {"user_id": "U99", "product_id": "P99", "action_type": "VIEW", "timestamp": "2026-08-01 10:00:00", "interaction_count": "2"},
            {"user_id": "U99", "product_id": "P99", "action_type": "view", "timestamp": "2026-08-01 10:00:00", "interaction_count": "2"},  # Duplicate
            {"user_id": None, "product_id": "P99", "action_type": "purchase", "timestamp": "2026-08-01 10:00:00"},  # Missing user_id
            {"user_id": "U98", "product_id": "P98", "action_type": "invalid_action", "timestamp": "2026-08-01 10:00:00"},  # Invalid action
        ])

        clean_df = validator.validate_and_clean_behavior(raw_df)
        self.assertEqual(len(clean_df), 1)  # Only 1 valid record should remain
        self.assertEqual(clean_df.iloc[0]["user_id"], "U99")
        self.assertEqual(clean_df.iloc[0]["action_type"], "view")

    # 3. Test Rule Engine Evaluation
    def test_rule_evaluation_co_purchase(self):
        engine = RuleEngine(self.config_path)

        user_beh = pd.DataFrame([
            {"user_id": "U1001", "product_id": "P101", "action_type": "purchase", "timestamp": datetime.now(), "interaction_count": 1}
        ])

        candidates = engine._eval_co_purchase("U1001", user_beh)
        self.assertTrue(len(candidates) > 0)
        self.assertEqual(candidates[0]["rule_name"], "RULE_CO_PURCHASE")
        self.assertIn(candidates[0]["product_id"], ["P102", "P105"])

    def test_rule_evaluation_premium(self):
        engine = RuleEngine(self.config_path)
        user_prof = pd.DataFrame([
            {"user_id": "U1003", "user_tier": "Platinum", "total_spent": 1500.00}
        ])

        candidates = engine._eval_premium_catalog("U1003", user_prof)
        self.assertTrue(len(candidates) > 0)
        self.assertEqual(candidates[0]["rule_name"], "RULE_PREMIUM_CATALOG")

    # 4. Test Scoring Calculations
    def test_scoring_calculations(self):
        scorer = RecommendationScorer(self.config_path)

        candidates = [
            {"user_id": "U1", "product_id": "P101", "rule_name": "RULE_CO_PURCHASE", "rule_weight": 3.5}
        ]

        user_beh = pd.DataFrame([
            {"user_id": "U1", "product_id": "P101", "action_type": "view", "interaction_count": 3, "timestamp": pd.Timestamp.now()}
        ])
        products_df = pd.DataFrame([
            {"product_id": "P101", "popularity_score": 9.0}
        ])

        scored = scorer.compute_scores(candidates, user_beh, products_df)
        self.assertEqual(len(scored), 1)
        self.assertGreater(scored[0]["relevance_score"], 3.5)

    # 5. Test Ranking Logic
    def test_ranking_logic(self):
        ranker = RecommendationRanker(self.config_path)

        scored = [
            {"product_id": "P1", "relevance_score": 4.5},
            {"product_id": "P2", "relevance_score": 8.9},
            {"product_id": "P3", "relevance_score": 6.2},
            {"product_id": "P4", "relevance_score": 2.1},
            {"product_id": "P5", "relevance_score": 9.5},
            {"product_id": "P6", "relevance_score": 1.0},
        ]

        ranked = ranker.rank_recommendations(scored, top_n=3)
        self.assertEqual(len(ranked), 3)
        self.assertEqual(ranked[0]["product_id"], "P5")
        self.assertEqual(ranked[0]["rank_order"], 1)
        self.assertEqual(ranked[1]["product_id"], "P2")
        self.assertEqual(ranked[1]["rank_order"], 2)

    # 6. Test Optimizer Deduplication & Exclusion Filters
    def test_optimizer_filters(self):
        optimizer = RecommendationOptimizer(self.config_path)

        candidates = [
            {"user_id": "U1", "product_id": "P101", "rule_name": "RULE_CO_PURCHASE", "relevance_score": 5.0, "rule_weight": 3.5},
            {"user_id": "U1", "product_id": "P101", "rule_name": "RULE_PREMIUM_CATALOG", "relevance_score": 6.0, "rule_weight": 4.0},  # Duplicate P101
            {"user_id": "U1", "product_id": "P102", "rule_name": "RULE_CO_PURCHASE", "relevance_score": 4.0, "rule_weight": 3.5},  # Already purchased
            {"user_id": "U1", "product_id": "P108", "rule_name": "RULE_CO_PURCHASE", "relevance_score": 4.5, "rule_weight": 3.5},  # Out of stock
        ]

        user_beh = pd.DataFrame([
            {"user_id": "U1", "product_id": "P102", "action_type": "purchase"}
        ])
        products_df = pd.DataFrame([
            {"product_id": "P101", "stock_quantity": 10},
            {"product_id": "P102", "stock_quantity": 15},
            {"product_id": "P108", "stock_quantity": 0},  # Out of stock
        ])

        optimized = optimizer.optimize_recommendations(candidates, user_beh, products_df)
        p_ids = [item["product_id"] for item in optimized]

        self.assertIn("P101", p_ids)
        self.assertNotIn("P102", p_ids)  # Filtered because already purchased
        self.assertNotIn("P108", p_ids)  # Filtered because out of stock
        self.assertEqual(len(optimized), 1)  # Only P101 retained

    # 7. Test Dual Target Logger
    def test_decision_logger(self):
        logger = DecisionLogger(self.config_path)
        sample_recs = [
            {"product_id": "P101", "rank_order": 1, "relevance_score": 7.5, "applied_rule": "RULE_CO_PURCHASE", "reason": "Test reason"}
        ]
        logger.log_decision("U_TEST", sample_recs)

        # Check txt log file created
        self.assertTrue(os.path.exists("recommendations_log.txt"))

    # 8. Test CSV & Excel Report Generation
    def test_report_generation(self):
        generator = ReportGenerator(self.config_path)
        recs = [
            {"user_id": "U1001", "rank_order": 1, "product_id": "P101", "relevance_score": 8.5, "applied_rule": "RULE_CO_PURCHASE", "reason": "Complementary item"}
        ]
        csv_path, excel_path = generator.export_reports(recs)

        self.assertTrue(os.path.exists(csv_path))
        self.assertTrue(os.path.exists(excel_path))


if __name__ == "__main__":
    unittest.main()
