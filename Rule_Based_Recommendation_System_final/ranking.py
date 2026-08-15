import json
import logging

logger = logging.getLogger("RecommendationRanker")


class RecommendationRanker:
    def __init__(self, config_path="config.json"):
        self.config_path = config_path
        self.top_n = self._load_top_n()

    def _load_top_n(self):
        with open(self.config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        return config.get("ranking", {}).get("top_n", 5)

    def rank_recommendations(self, scored_list: list, top_n: int = None) -> list:
        """
        Sort recommendations by relevance_score descending, assign rank numbers (1..N),
        and limit output to top N recommendations.
        """
        if not scored_list:
            return []

        limit = top_n if top_n is not None else self.top_n

        # Sort descending by relevance_score
        sorted_list = sorted(scored_list, key=lambda x: x.get("relevance_score", 0.0), reverse=True)

        ranked_list = []
        for idx, item in enumerate(sorted_list[:limit], start=1):
            ranked_item = dict(item)
            ranked_item["rank_order"] = idx
            ranked_list.append(ranked_item)

        logger.info(f"Ranked {len(ranked_list)} top recommendations (Limited to Top-{limit}).")
        return ranked_list
