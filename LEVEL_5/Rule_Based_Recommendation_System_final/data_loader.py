import logging
import pandas as pd
from models import fetch_all_users, fetch_all_products, fetch_all_user_behavior

logger = logging.getLogger("DataLoader")


class DataLoader:
    def __init__(self, config_path="config.json"):
        self.config_path = config_path

    def load_user_profiles(self) -> pd.DataFrame:
        """Fetch users table from MySQL and return as pandas DataFrame."""
        try:
            users_raw = fetch_all_users(self.config_path)
            df = pd.DataFrame(users_raw)
            logger.info(f"Loaded {len(df)} user profiles from MySQL.")
            return df
        except Exception as e:
            logger.warning(f"Could not load users from MySQL ({e}). Using in-memory seed user profiles.")
            return pd.DataFrame([
                {"user_id": "U1001", "username": "Alice Smith", "email": "alice@example.com", "user_tier": "Gold", "total_spent": 750.00},
                {"user_id": "U1002", "username": "Bob Jones", "email": "bob@example.com", "user_tier": "Standard", "total_spent": 120.00},
                {"user_id": "U1003", "username": "Carol White", "email": "carol@example.com", "user_tier": "Platinum", "total_spent": 1500.00},
                {"user_id": "U1004", "username": "David Brown", "email": "david@example.com", "user_tier": "Standard", "total_spent": 45.00},
                {"user_id": "U1005", "username": "Eve Davis", "email": "eve@example.com", "user_tier": "Gold", "total_spent": 600.00},
            ])

    def load_products_catalog(self) -> pd.DataFrame:
        """Fetch products table from MySQL and return as pandas DataFrame."""
        try:
            products_raw = fetch_all_products(self.config_path)
            df = pd.DataFrame(products_raw)
            logger.info(f"Loaded {len(df)} products from MySQL catalog.")
            return df
        except Exception as e:
            logger.warning(f"Could not load products from MySQL ({e}). Using in-memory seed products catalog.")
            return pd.DataFrame([
                {"product_id": "P101", "product_name": "Pro Ultra Laptop 15", "category": "Electronics", "price": 1299.99, "popularity_score": 9.5, "stock_quantity": 15, "tags": "laptop,pro,ultra,electronics,computer"},
                {"product_id": "P102", "product_name": "Wireless Noise-Canceling Headphones", "category": "Electronics", "price": 249.99, "popularity_score": 8.8, "stock_quantity": 30, "tags": "audio,headphones,wireless,noise-canceling"},
                {"product_id": "P103", "product_name": "Smart Espresso Coffee Machine", "category": "Home", "price": 499.99, "popularity_score": 8.2, "stock_quantity": 8, "tags": "coffee,espresso,kitchen,home,smart"},
                {"product_id": "P104", "product_name": "Ergonomic Mesh Office Chair", "category": "Home", "price": 199.99, "popularity_score": 7.9, "stock_quantity": 20, "tags": "chair,furniture,office,home,ergonomic"},
                {"product_id": "P105", "product_name": "Fast Charging Power Bank 20000mAh", "category": "Accessories", "price": 49.99, "popularity_score": 9.1, "stock_quantity": 50, "tags": "powerbank,battery,charging,wireless,accessories"},
                {"product_id": "P106", "product_name": "Premium Titanium Smart Watch", "category": "Electronics", "price": 399.99, "popularity_score": 9.0, "stock_quantity": 12, "tags": "watch,smartwatch,titanium,premium,wearable"},
                {"product_id": "P107", "product_name": "Waterproof Travel Backpack 30L", "category": "Accessories", "price": 79.99, "popularity_score": 8.5, "stock_quantity": 25, "tags": "backpack,travel,waterproof,bag,accessories"},
                {"product_id": "P108", "product_name": "Pro Air Running Shoes", "category": "Footwear", "price": 129.99, "popularity_score": 8.9, "stock_quantity": 0, "tags": "shoes,running,sports,footwear,air"},
                {"product_id": "P109", "product_name": "Casual Canvas Sneakers", "category": "Footwear", "price": 59.99, "popularity_score": 7.5, "stock_quantity": 40, "tags": "shoes,casual,sneakers,footwear,canvas"},
                {"product_id": "P110", "product_name": "All-Weather Insulated Jacket", "category": "Apparel", "price": 189.99, "popularity_score": 8.7, "stock_quantity": 18, "tags": "jacket,apparel,clothing,all-weather,insulated"},
            ])

    def load_user_behavior(self) -> pd.DataFrame:
        """Fetch user_behavior table from MySQL and return as pandas DataFrame."""
        try:
            behavior_raw = fetch_all_user_behavior(self.config_path)
            df = pd.DataFrame(behavior_raw)
            logger.info(f"Loaded {len(df)} user behavior records from MySQL.")
            return df
        except Exception as e:
            logger.warning(f"Could not load behavior from MySQL ({e}). Using in-memory seed behavior data.")
            now = pd.Timestamp.now()
            return pd.DataFrame([
                {"user_id": "U1001", "product_id": "P101", "action_type": "purchase", "search_query": None, "interaction_count": 1, "timestamp": now - pd.Timedelta(days=2)},
                {"user_id": "U1001", "product_id": "P102", "action_type": "view", "search_query": None, "interaction_count": 3, "timestamp": now - pd.Timedelta(days=1)},
                {"user_id": "U1001", "product_id": "P105", "action_type": "cart", "search_query": None, "interaction_count": 2, "timestamp": now - pd.Timedelta(hours=5)},
                {"user_id": "U1001", "product_id": "P101", "action_type": "search", "search_query": "laptop wireless", "interaction_count": 1, "timestamp": now - pd.Timedelta(days=1)},
                {"user_id": "U1002", "product_id": "P103", "action_type": "view", "search_query": None, "interaction_count": 4, "timestamp": now - pd.Timedelta(days=3)},
                {"user_id": "U1002", "product_id": "P103", "action_type": "cart", "search_query": None, "interaction_count": 1, "timestamp": now - pd.Timedelta(days=2)},
                {"user_id": "U1002", "product_id": "P104", "action_type": "view", "search_query": None, "interaction_count": 2, "timestamp": now - pd.Timedelta(days=1)},
                {"user_id": "U1002", "product_id": "P104", "action_type": "search", "search_query": "ergonomic chair", "interaction_count": 1, "timestamp": now - pd.Timedelta(hours=10)},
                {"user_id": "U1003", "product_id": "P107", "action_type": "purchase", "search_query": None, "interaction_count": 1, "timestamp": now - pd.Timedelta(days=5)},
                {"user_id": "U1003", "product_id": "P106", "action_type": "view", "search_query": None, "interaction_count": 5, "timestamp": now - pd.Timedelta(days=1)},
                {"user_id": "U1003", "product_id": "P110", "action_type": "view", "search_query": None, "interaction_count": 3, "timestamp": now - pd.Timedelta(hours=2)},
                {"user_id": "U1003", "product_id": "P106", "action_type": "search", "search_query": "titanium watch", "interaction_count": 2, "timestamp": now - pd.Timedelta(hours=4)},
                {"user_id": "U1004", "product_id": "P108", "action_type": "view", "search_query": None, "interaction_count": 3, "timestamp": now - pd.Timedelta(days=4)},
                {"user_id": "U1004", "product_id": "P109", "action_type": "view", "search_query": None, "interaction_count": 1, "timestamp": now - pd.Timedelta(days=2)},
                {"user_id": "U1004", "product_id": "P108", "action_type": "search", "search_query": "running shoes", "interaction_count": 1, "timestamp": now - pd.Timedelta(days=3)},
                {"user_id": "U1005", "product_id": "P104", "action_type": "cart", "search_query": None, "interaction_count": 2, "timestamp": now - pd.Timedelta(days=1)},
                {"user_id": "U1005", "product_id": "P110", "action_type": "cart", "search_query": None, "interaction_count": 1, "timestamp": now - pd.Timedelta(hours=12)},
                {"user_id": "U1005", "product_id": "P106", "action_type": "view", "search_query": None, "interaction_count": 2, "timestamp": now - pd.Timedelta(hours=3)},
            ])

    def load_all_data(self):
        """Convenience method to load user_profiles, products, and user_behavior DataFrames."""
        users_df = self.load_user_profiles()
        products_df = self.load_products_catalog()
        behavior_df = self.load_user_behavior()
        return users_df, products_df, behavior_df
