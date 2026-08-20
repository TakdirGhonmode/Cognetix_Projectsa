import json
import numpy as np
import pandas as pd
import logging
from datetime import datetime

logger = logging.getLogger("RecommendationScorer")


class RecommendationScorer:
    def __init__(self, config_path="config.json"):
        self.config_path = config_path
        self.scoring_config = self._load_scoring_config()

    def _load_scoring_config(self):
        with open(self.config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        return config.get("scoring", {})

    def compute_scores(self, candidate_list: list, user_beh: pd.DataFrame, products_df: pd.DataFrame) -> list:
        """
        Compute relevance scores for a list of raw recommendation candidates.
        Applies formula:
        Relevance Score = (Frequency * W_freq) + (Recency Decay * W_recency) + (Popularity * W_pop) + Sum(Rule Weights)
        """
        if not candidate_list:
            return []

        w_freq = self.scoring_config.get("frequency_weight", 1.5)
        w_recency = self.scoring_config.get("recency_weight", 2.0)
        w_pop = self.scoring_config.get("popularity_weight", 1.0)
        half_life_days = self.scoring_config.get("recency_half_life_days", 7.0)

        # Build product lookup dictionaries
        popularity_dict = {}
        if not products_df.empty and "popularity_score" in products_df.columns:
            popularity_dict = dict(zip(products_df["product_id"], products_df["popularity_score"]))

        # Build user interaction metrics (frequency and recency) per product
        freq_dict = {}
        recency_decay_dict = {}
        now = pd.Timestamp.now()

        if not user_beh.empty:
            for p_id, group in user_beh.groupby("product_id"):
                freq_dict[p_id] = group["interaction_count"].sum()
                most_recent = group["timestamp"].max()
                if pd.notnull(most_recent):
                    days_elapsed = max(0.0, (now - most_recent).total_seconds() / 86400.0)
                    # Exponential decay factor: 2^(-t / half_life)
                    decay = np.exp(- (np.log(2.0) / max(1.0, half_life_days)) * days_elapsed)
                    recency_decay_dict[p_id] = float(decay)

        scored_candidates = []
        for cand in candidate_list:
            p_id = cand["product_id"]

            freq = freq_dict.get(p_id, 0)
            recency_decay = recency_decay_dict.get(p_id, 0.5)
            popularity = float(popularity_dict.get(p_id, 5.0))
            rule_weight = float(cand.get("rule_weight", 1.0))

            # Calculate Component Scores
            freq_score = freq * w_freq
            recency_score = recency_decay * w_recency
            pop_score = (popularity / 10.0) * w_pop  # Normalize popularity 0-10 scale

            total_relevance_score = round(rule_weight + freq_score + recency_score + pop_score, 4)

            scored = dict(cand)
            scored["relevance_score"] = total_relevance_score
            scored["frequency_score"] = freq_score
            scored["recency_score"] = recency_score
            scored["popularity_score"] = pop_score
            scored_candidates.append(scored)

        logger.info(f"Scored {len(scored_candidates)} recommendation candidate items.")
        return scored_candidates
