import logging
import pandas as pd
import numpy as np
from datetime import datetime

logger = logging.getLogger("DataValidator")


class DataValidator:
    def __init__(self):
        self.allowed_action_types = {"view", "purchase", "cart", "search"}

    def validate_and_clean_behavior(self, behavior_df: pd.DataFrame) -> pd.DataFrame:
        """
        Validate and clean raw user behavior DataFrame.
        Steps:
        1. Check missing required fields
        2. Validate & coerce data types
        3. Validate timestamps
        4. Remove duplicates
        5. Clean search queries and strings
        """
        if behavior_df is None or behavior_df.empty:
            logger.warning("Empty behavior DataFrame passed for validation.")
            return pd.DataFrame(columns=["user_id", "product_id", "action_type", "search_query", "interaction_count", "timestamp"])

        initial_count = len(behavior_df)
        df = behavior_df.copy()

        # 1. Missing Values Check
        required_cols = ["user_id", "product_id", "action_type", "timestamp"]
        for col in required_cols:
            if col not in df.columns:
                raise ValueError(f"Missing required column in behavior data: '{col}'")

        # Drop records where core fields are null/NaN
        df = df.dropna(subset=["user_id", "product_id", "action_type", "timestamp"])

        # 2. Data Type Coercion & Action Type Filter
        df["user_id"] = df["user_id"].astype(str).str.strip()
        df["product_id"] = df["product_id"].astype(str).str.strip()
        df["action_type"] = df["action_type"].astype(str).str.strip().str.lower()
        df = df[df["action_type"].isin(self.allowed_action_types)]

        if "interaction_count" in df.columns:
            df["interaction_count"] = pd.to_numeric(df["interaction_count"], errors="coerce").fillna(1).astype(int)
            df = df[df["interaction_count"] > 0]
        else:
            df["interaction_count"] = 1

        # 3. Timestamp Validation
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
        df = df.dropna(subset=["timestamp"])

        # Reject extreme future timestamps (e.g., beyond tomorrow)
        max_valid_date = pd.Timestamp.now() + pd.Timedelta(days=1)
        df = df[df["timestamp"] <= max_valid_date]

        # 4. Duplicate Records Removal
        dup_cols = ["user_id", "product_id", "action_type", "timestamp"]
        df = df.drop_duplicates(subset=dup_cols, keep="first")

        # 5. Data Cleaning (Search Queries)
        if "search_query" in df.columns:
            df["search_query"] = df["search_query"].fillna("").astype(str).str.strip().str.lower()

        cleaned_count = len(df)
        removed_count = initial_count - cleaned_count
        logger.info(f"Data Validation Complete: {cleaned_count} valid records retained, {removed_count} invalid/duplicate records removed.")

        return df

    def validate_products(self, products_df: pd.DataFrame) -> pd.DataFrame:
        """Validate and clean products catalog DataFrame."""
        if products_df is None or products_df.empty:
            return pd.DataFrame()

        df = products_df.copy()
        df = df.dropna(subset=["product_id", "product_name", "category", "price"])
        df["product_id"] = df["product_id"].astype(str).str.strip()
        df["price"] = pd.to_numeric(df["price"], errors="coerce").fillna(0.0)
        df["popularity_score"] = pd.to_numeric(df["popularity_score"], errors="coerce").fillna(0.0)
        df["stock_quantity"] = pd.to_numeric(df["stock_quantity"], errors="coerce").fillna(0).astype(int)
        df["tags"] = df["tags"].fillna("").astype(str).str.lower()
        return df

    def validate_users(self, users_df: pd.DataFrame) -> pd.DataFrame:
        """Validate and clean users DataFrame."""
        if users_df is None or users_df.empty:
            return pd.DataFrame()

        df = users_df.copy()
        df = df.dropna(subset=["user_id"])
        df["user_id"] = df["user_id"].astype(str).str.strip()
        df["user_tier"] = df["user_tier"].fillna("Standard").astype(str).str.strip()
        df["total_spent"] = pd.to_numeric(df["total_spent"], errors="coerce").fillna(0.0)
        return df
