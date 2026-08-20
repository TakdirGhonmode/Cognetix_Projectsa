import json
import logging
import pandas as pd

logger = logging.getLogger("RecommendationOptimizer")


class RecommendationOptimizer:
    def __init__(self, config_path="config.json"):
        self.config_path = config_path
        self.opt_config = self._load_opt_config()

    def _load_opt_config(self):
        with open(self.config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        return config.get("optimization", {})

    def optimize_recommendations(
        self,
        candidate_list: list,
        user_beh: pd.DataFrame,
        products_df: pd.DataFrame
    ) -> list:
        """
        Deduplicate candidates, filter out already purchased items, filter out-of-stock items,
        and enforce score thresholds.
        """
        if not candidate_list:
            return []

        exclude_purchased = self.opt_config.get("exclude_already_purchased", True)
        exclude_out_of_stock = self.opt_config.get("exclude_out_of_stock", True)
        min_score_thresh = self.opt_config.get("min_score_threshold", 0.5)

        # 1. Deduplication across candidate rules
        dedup_map = {}
        for item in candidate_list:
            p_id = item["product_id"]
            if p_id not in dedup_map:
                dedup_map[p_id] = dict(item)
                dedup_map[p_id]["applied_rules"] = [item["rule_name"]]
            else:
                # Merge rule metadata & keep maximum relevance score + bonus weight
                existing = dedup_map[p_id]
                if item["rule_name"] not in existing["applied_rules"]:
                    existing["applied_rules"].append(item["rule_name"])
                    # Combine score boost for multi-rule consensus
                    existing["relevance_score"] = round(existing["relevance_score"] + (item.get("rule_weight", 1.0) * 0.5), 4)

                # Keep higher relevance score
                if item.get("relevance_score", 0.0) > existing.get("relevance_score", 0.0):
                    existing["relevance_score"] = item["relevance_score"]
                    existing["reason"] = item["reason"]

        deduped_items = list(dedup_map.values())

        # 2. Exclude previously purchased products
        purchased_pids = set()
        if exclude_purchased and not user_beh.empty and "action_type" in user_beh.columns:
            purchased_pids = set(user_beh[user_beh["action_type"] == "purchase"]["product_id"].unique())

        # 3. Build stock quantity lookup
        stock_dict = {}
        if not products_df.empty and "stock_quantity" in products_df.columns:
            stock_dict = dict(zip(products_df["product_id"], products_df["stock_quantity"]))

        optimized = []
        for item in deduped_items:
            p_id = item["product_id"]

            # Filter purchased
            if exclude_purchased and p_id in purchased_pids:
                logger.info(f"Filtering out product {p_id}: Already purchased by user.")
                continue

            # Filter out of stock
            stock = stock_dict.get(p_id, 1)
            if exclude_out_of_stock and stock <= 0:
                logger.info(f"Filtering out product {p_id}: Out of stock (quantity = {stock}).")
                continue

            # Filter minimum score threshold
            if item.get("relevance_score", 0.0) < min_score_thresh:
                logger.info(f"Filtering out product {p_id}: Below min score threshold ({item.get('relevance_score')} < {min_score_thresh}).")
                continue

            # Format merged applied rule string
            item["applied_rule"] = ", ".join(item.get("applied_rules", [item.get("rule_name", "CUSTOM_RULE")]))
            optimized.append(item)

        logger.info(f"Optimization complete: {len(optimized)} refined recommendation items ready for display.")
        return optimized
