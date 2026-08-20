import json
import logging
import pandas as pd

logger = logging.getLogger("RuleEngine")


class RuleEngine:
    def __init__(self, config_path="config.json"):
        self.config_path = config_path
        self.rules_config = self._load_rules_config()

    def _load_rules_config(self):
        with open(self.config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        return config.get("rules", {})

    def evaluate_user_recommendations(self, user_id: str, behavior_df: pd.DataFrame, products_df: pd.DataFrame, users_df: pd.DataFrame):
        """
        Evaluate all active business rules for a given user.
        Returns a list of raw recommendation candidate dicts:
        [
          {
            "user_id": user_id,
            "product_id": product_id,
            "rule_name": rule_name,
            "rule_weight": rule_weight,
            "reason": reason
          }, ...
        ]
        """
        user_beh = behavior_df[behavior_df["user_id"] == user_id] if not behavior_df.empty else pd.DataFrame()
        user_prof = users_df[users_df["user_id"] == user_id] if not users_df.empty else pd.DataFrame()

        candidates = []

        # 1. RULE: Co-Purchase Recommendations
        candidates.extend(self._eval_co_purchase(user_id, user_beh))

        # 2. RULE: Category-based Recommendations
        candidates.extend(self._eval_category_top_sellers(user_id, user_beh, products_df))

        # 3. RULE: Premium Customer Recommendations
        candidates.extend(self._eval_premium_catalog(user_id, user_prof))

        # 4. RULE: Search-Intent Recommendations
        candidates.extend(self._eval_search_intent(user_id, user_beh, products_df))

        # 5. RULE: Cart-Abandonment Recommendations
        candidates.extend(self._eval_cart_abandonment(user_id, user_beh))

        logger.info(f"Rule Engine evaluated {len(candidates)} candidate suggestions across active rules for User {user_id}.")
        return candidates

    def _eval_co_purchase(self, user_id: str, user_beh: pd.DataFrame):
        rule_cfg = self.rules_config.get("RULE_CO_PURCHASE", {})
        if not rule_cfg.get("enabled", True) or user_beh.empty:
            return []

        purchased_items = user_beh[user_beh["action_type"] == "purchase"]["product_id"].unique()
        co_map = rule_cfg.get("co_purchase_map", {})
        weight = rule_cfg.get("weight", 3.5)

        candidates = []
        for p_id in purchased_items:
            if p_id in co_map:
                for rec_pid in co_map[p_id]:
                    candidates.append({
                        "user_id": user_id,
                        "product_id": rec_pid,
                        "rule_name": "RULE_CO_PURCHASE",
                        "rule_weight": weight,
                        "reason": f"Complementary product cross-sell based on past purchase of {p_id}"
                    })
        return candidates

    def _eval_category_top_sellers(self, user_id: str, user_beh: pd.DataFrame, products_df: pd.DataFrame):
        rule_cfg = self.rules_config.get("RULE_CATEGORY_TOP", {})
        if not rule_cfg.get("enabled", True) or user_beh.empty or products_df.empty:
            return []

        weight = rule_cfg.get("weight", 2.5)
        top_sellers_map = rule_cfg.get("top_sellers_by_category", {})

        # Merge behavior with products catalog to get categories
        merged = user_beh.merge(products_df[["product_id", "category"]], on="product_id", how="left")
        cat_counts = merged["category"].value_counts()

        candidates = []
        if not cat_counts.empty:
            top_category = cat_counts.index[0]
            # Use configured top sellers or top popularity products in that category
            cat_top_pids = top_sellers_map.get(top_category, [])
            if not cat_top_pids:
                cat_prods = products_df[products_df["category"] == top_category].sort_values(by="popularity_score", ascending=False)
                cat_top_pids = cat_prods["product_id"].tolist()[:3]

            for rec_pid in cat_top_pids:
                candidates.append({
                    "user_id": user_id,
                    "product_id": rec_pid,
                    "rule_name": "RULE_CATEGORY_TOP",
                    "rule_weight": weight,
                    "reason": f"Top-selling product in preferred category '{top_category}'"
                })
        return candidates

    def _eval_premium_catalog(self, user_id: str, user_prof: pd.DataFrame):
        rule_cfg = self.rules_config.get("RULE_PREMIUM_CATALOG", {})
        if not rule_cfg.get("enabled", True) or user_prof.empty:
            return []

        weight = rule_cfg.get("weight", 4.0)
        spend_thresh = rule_cfg.get("spend_threshold", 500.0)
        premium_tiers = set(rule_cfg.get("premium_tiers", ["Gold", "Platinum"]))
        premium_pids = rule_cfg.get("premium_product_ids", [])

        user_row = user_prof.iloc[0]
        user_tier = user_row.get("user_tier", "Standard")
        total_spent = float(user_row.get("total_spent", 0.0))

        candidates = []
        if user_tier in premium_tiers or total_spent >= spend_thresh:
            for rec_pid in premium_pids:
                candidates.append({
                    "user_id": user_id,
                    "product_id": rec_pid,
                    "rule_name": "RULE_PREMIUM_CATALOG",
                    "rule_weight": weight,
                    "reason": f"Exclusive premium catalog selection for {user_tier} tier / VIP spend"
                })
        return candidates

    def _eval_search_intent(self, user_id: str, user_beh: pd.DataFrame, products_df: pd.DataFrame):
        rule_cfg = self.rules_config.get("RULE_SEARCH_INTENT", {})
        if not rule_cfg.get("enabled", True) or user_beh.empty:
            return []

        weight = rule_cfg.get("weight", 3.0)
        search_kw_map = rule_cfg.get("search_keywords", {})

        search_rows = user_beh[user_beh["action_type"] == "search"]
        candidates = []

        for _, row in search_rows.iterrows():
            query = str(row.get("search_query", "")).lower()
            if not query:
                continue

            matched_pids = set()
            # Match via config keyword map
            for kw, pids in search_kw_map.items():
                if kw in query:
                    matched_pids.update(pids)

            # Match via product catalog tags & title
            if not products_df.empty:
                for _, prod in products_df.iterrows():
                    p_id = prod["product_id"]
                    tags = str(prod.get("tags", "")).lower()
                    title = str(prod.get("product_name", "")).lower()
                    if any(term in tags or term in title for term in query.split()):
                        matched_pids.add(p_id)

            for rec_pid in matched_pids:
                candidates.append({
                    "user_id": user_id,
                    "product_id": rec_pid,
                    "rule_name": "RULE_SEARCH_INTENT",
                    "rule_weight": weight,
                    "reason": f"Search intent match for query '{query}'"
                })
        return candidates

    def _eval_cart_abandonment(self, user_id: str, user_beh: pd.DataFrame):
        rule_cfg = self.rules_config.get("RULE_CART_ABANDONMENT", {})
        if not rule_cfg.get("enabled", True) or user_beh.empty:
            return []

        weight = rule_cfg.get("weight", 3.2)
        min_views = rule_cfg.get("min_views_without_purchase", 2)

        purchased_pids = set(user_beh[user_beh["action_type"] == "purchase"]["product_id"].unique())

        cart_pids = set(user_beh[user_beh["action_type"] == "cart"]["product_id"].unique()) - purchased_pids

        view_counts = user_beh[user_beh["action_type"] == "view"].groupby("product_id")["interaction_count"].sum()
        frequent_view_pids = set(view_counts[view_counts >= min_views].index) - purchased_pids

        target_pids = cart_pids.union(frequent_view_pids)

        candidates = []
        for rec_pid in target_pids:
            candidates.append({
                "user_id": user_id,
                "product_id": rec_pid,
                "rule_name": "RULE_CART_ABANDONMENT",
                "rule_weight": weight,
                "reason": "Re-engagement offer for items in cart or repeatedly viewed without checkout"
            })
        return candidates
