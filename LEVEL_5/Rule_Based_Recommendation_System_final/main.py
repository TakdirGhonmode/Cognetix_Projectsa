import sys
import logging
import argparse
from database import initialize_database
from models import seed_database_if_empty, insert_recommendations_batch
from data_loader import DataLoader
from validator import DataValidator
from rule_engine import RuleEngine
from scorer import RecommendationScorer
from ranking import RecommendationRanker
from optimizer import RecommendationOptimizer
from logger import DecisionLogger
from reports import ReportGenerator

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("MainWorkflow")


def run_recommendation_pipeline(target_user_id: str = None, config_path: str = "config.json"):
    """
    Execute the 11-step rule-based recommendation workflow.
    """
    print("\n" + "=" * 70)
    print("      PROJECT 2 — RULE-BASED RECOMMENDATION SYSTEM (MySQL ENGINE)")
    print("=" * 70)

    # STEP 1 — Database & Seed Initialization
    print("\n[STEP 1] Initializing MySQL Database & Seeding Data...")
    try:
        initialize_database(config_path)
        seed_database_if_empty(config_path)
    except Exception as e:
        logger.warning(f"MySQL connection warning ({e}). Please set valid MySQL credentials in config.json. Pipeline will proceed using loaded dataset.")

    # STEP 2 — Load User Behavior & Catalog Data from MySQL
    print("[STEP 2] Loading Behavior, Products, and User Data...")
    loader = DataLoader(config_path)
    users_df, products_df, raw_behavior_df = loader.load_all_data()

    if raw_behavior_df.empty:
        print("No user behavior data found in database. Exiting pipeline.")
        return

    # STEP 3 — Validate & Clean Data
    print("[STEP 3] Validating and Cleaning Behavior Data...")
    validator = DataValidator()
    clean_behavior_df = validator.validate_and_clean_behavior(raw_behavior_df)
    clean_products_df = validator.validate_products(products_df)
    clean_users_df = validator.validate_users(users_df)

    # STEP 4 — Load Business Rules Configuration
    print("[STEP 4] Loading Business Rules Configuration...")
    rule_engine = RuleEngine(config_path)

    # Determine user IDs to process
    if target_user_id:
        user_ids = [target_user_id]
    else:
        user_ids = clean_users_df["user_id"].unique().tolist() if not clean_users_df.empty else clean_behavior_df["user_id"].unique().tolist()

    all_final_recommendations = []
    scorer = RecommendationScorer(config_path)
    ranker = RecommendationRanker(config_path)
    optimizer = RecommendationOptimizer(config_path)
    decision_logger = DecisionLogger(config_path)

    print(f"\nProcessing recommendations for {len(user_ids)} user(s)...\n")

    for u_id in user_ids:
        print(f"--- Processing User: {u_id} ---")
        user_beh = clean_behavior_df[clean_behavior_df["user_id"] == u_id]

        # STEP 5 — Apply Rule Engine
        raw_candidates = rule_engine.evaluate_user_recommendations(u_id, clean_behavior_df, clean_products_df, clean_users_df)

        if not raw_candidates:
            print(f"  No recommendation candidates generated for User {u_id}.")
            continue

        # STEP 6 — Calculate Relevance Scores
        scored_candidates = scorer.compute_scores(raw_candidates, user_beh, clean_products_df)

        # STEP 7 — Optimize Output (Deduplicate & Filter Purchased/Out-of-Stock)
        optimized_candidates = optimizer.optimize_recommendations(scored_candidates, user_beh, clean_products_df)

        # STEP 8 — Rank Recommendations
        ranked_recs = ranker.rank_recommendations(optimized_candidates)

        if not ranked_recs:
            print(f"  No items remaining after optimization for User {u_id}.")
            continue

        # STEP 9 — Log Recommendation Decisions (File & MySQL)
        decision_logger.log_decision(u_id, ranked_recs)

        # Insert batch into recommendations MySQL table
        try:
            insert_recommendations_batch(ranked_recs, config_path)
        except Exception as err:
            logger.error(f"Could not persist recommendations to MySQL table: {err}")

        all_final_recommendations.extend(ranked_recs)

        # STEP 11 Preview (User Table Output)
        print(f"  Top Recommendations for {u_id}:")
        for r in ranked_recs:
            p_name = ""
            if not clean_products_df.empty:
                match = clean_products_df[clean_products_df["product_id"] == r["product_id"]]
                if not match.empty:
                    p_name = match.iloc[0]["product_name"]
            print(f"    Rank #{r['rank_order']} | Product: {r['product_id']} ({p_name}) | Score: {r['relevance_score']} | Rule: {r['applied_rule']}")

    # STEP 10 — Generate Reports (CSV + Excel)
    print("\n[STEP 10] Generating Recommendation Reports (CSV & Excel)...")
    report_gen = ReportGenerator(config_path)
    csv_file, excel_file = report_gen.export_reports(all_final_recommendations, clean_products_df)
    print(f"  -> CSV Report Saved:   {csv_file}")
    print(f"  -> Excel Report Saved: {excel_file}")

    print("\n" + "=" * 70)
    print("      RECOMMENDATION WORKFLOW COMPLETED SUCCESSFULLY!")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Rule-Based Recommendation System")
    parser.add_argument("--user", type=str, help="Target specific User ID (e.g. U1001)", default=None)
    parser.add_argument("--config", type=str, help="Path to custom config.json", default="config.json")
    args = parser.parse_args()

    run_recommendation_pipeline(target_user_id=args.user, config_path=args.config)
