import json
import logging
from datetime import datetime, timedelta
from database import get_db_connection

logger = logging.getLogger("Models")


def seed_database_if_empty(config_path="config.json"):
    """
    Populate MySQL database with sample dataset if tables are empty.
    """
    conn = get_db_connection(config_path)
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("SELECT COUNT(*) as cnt FROM users;")
        user_cnt = cursor.fetchone()["cnt"]

        if user_cnt > 0:
            logger.info("Database already contains data. Skipping seed population.")
            return

        logger.info("Seeding initial dataset into MySQL tables...")

        # 1. Seed Users
        users_data = [
            ("U1001", "Alice Smith", "alice@example.com", "Gold", 750.00),
            ("U1002", "Bob Jones", "bob@example.com", "Standard", 120.00),
            ("U1003", "Carol White", "carol@example.com", "Platinum", 1500.00),
            ("U1004", "David Brown", "david@example.com", "Standard", 45.00),
            ("U1005", "Eve Davis", "eve@example.com", "Gold", 600.00),
        ]
        insert_user_sql = """
        INSERT INTO users (user_id, username, email, user_tier, total_spent)
        VALUES (%s, %s, %s, %s, %s);
        """
        cursor.executemany(insert_user_sql, users_data)

        # 2. Seed Products
        products_data = [
            ("P101", "Pro Ultra Laptop 15", "Electronics", 1299.99, 9.5, 15, "laptop,pro,ultra,electronics,computer"),
            ("P102", "Wireless Noise-Canceling Headphones", "Electronics", 249.99, 8.8, 30, "audio,headphones,wireless,noise-canceling"),
            ("P103", "Smart Espresso Coffee Machine", "Home", 499.99, 8.2, 8, "coffee,espresso,kitchen,home,smart"),
            ("P104", "Ergonomic Mesh Office Chair", "Home", 199.99, 7.9, 20, "chair,furniture,office,home,ergonomic"),
            ("P105", "Fast Charging Power Bank 20000mAh", "Accessories", 49.99, 9.1, 50, "powerbank,battery,charging,wireless,accessories"),
            ("P106", "Premium Titanium Smart Watch", "Electronics", 399.99, 9.0, 12, "watch,smartwatch,titanium,premium,wearable"),
            ("P107", "Waterproof Travel Backpack 30L", "Accessories", 79.99, 8.5, 25, "backpack,travel,waterproof,bag,accessories"),
            ("P108", "Pro Air Running Shoes", "Footwear", 129.99, 8.9, 0, "shoes,running,sports,footwear,air"),  # Out of stock
            ("P109", "Casual Canvas Sneakers", "Footwear", 59.99, 7.5, 40, "shoes,casual,sneakers,footwear,canvas"),
            ("P110", "All-Weather Insulated Jacket", "Apparel", 189.99, 8.7, 18, "jacket,apparel,clothing,all-weather,insulated"),
        ]
        insert_prod_sql = """
        INSERT INTO products (product_id, product_name, category, price, popularity_score, stock_quantity, tags)
        VALUES (%s, %s, %s, %s, %s, %s, %s);
        """
        cursor.executemany(insert_prod_sql, products_data)

        # 3. Seed User Behavior
        now = datetime.now()
        behavior_data = [
            # U1001 (Gold user, bought P101, viewed headphones P102, searched 'wireless')
            ("U1001", "P101", "purchase", None, 1, now - timedelta(days=2)),
            ("U1001", "P102", "view", None, 3, now - timedelta(days=1)),
            ("U1001", "P105", "cart", None, 2, now - timedelta(hours=5)),
            ("U1001", "P101", "search", "laptop wireless", 1, now - timedelta(days=1)),

            # U1002 (Standard user, viewed coffee machine & office chair)
            ("U1002", "P103", "view", None, 4, now - timedelta(days=3)),
            ("U1002", "P103", "cart", None, 1, now - timedelta(days=2)),
            ("U1002", "P104", "view", None, 2, now - timedelta(days=1)),
            ("U1002", "P104", "search", "ergonomic chair", 1, now - timedelta(hours=10)),

            # U1003 (Platinum user, bought P107, looking for premium watches & jackets)
            ("U1003", "P107", "purchase", None, 1, now - timedelta(days=5)),
            ("U1003", "P106", "view", None, 5, now - timedelta(days=1)),
            ("U1003", "P110", "view", None, 3, now - timedelta(hours=2)),
            ("U1003", "P106", "search", "titanium watch", 2, now - timedelta(hours=4)),

            # U1004 (Standard user, searched running shoes, viewed out-of-stock P108)
            ("U1004", "P108", "view", None, 3, now - timedelta(days=4)),
            ("U1004", "P109", "view", None, 1, now - timedelta(days=2)),
            ("U1004", "P108", "search", "running shoes", 1, now - timedelta(days=3)),

            # U1005 (Gold user, cart abandoned P104 and P110)
            ("U1005", "P104", "cart", None, 2, now - timedelta(days=1)),
            ("U1005", "P110", "cart", None, 1, now - timedelta(hours=12)),
            ("U1005", "P106", "view", None, 2, now - timedelta(hours=3)),
        ]
        insert_beh_sql = """
        INSERT INTO user_behavior (user_id, product_id, action_type, search_query, interaction_count, timestamp)
        VALUES (%s, %s, %s, %s, %s, %s);
        """
        cursor.executemany(insert_beh_sql, behavior_data)

        conn.commit()
        logger.info("Sample database records successfully seeded into MySQL.")

    finally:
        cursor.close()
        conn.close()


def fetch_all_users(config_path="config.json"):
    """Fetch all users from MySQL users table."""
    conn = get_db_connection(config_path)
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM users;")
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def fetch_all_products(config_path="config.json"):
    """Fetch product catalog from MySQL products table."""
    conn = get_db_connection(config_path)
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM products;")
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def fetch_all_user_behavior(config_path="config.json"):
    """Fetch all user behavior logs from MySQL user_behavior table."""
    conn = get_db_connection(config_path)
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM user_behavior;")
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def insert_recommendations_batch(recommendations, config_path="config.json"):
    """Insert generated recommendations into MySQL recommendations table."""
    conn = get_db_connection(config_path)
    cursor = conn.cursor()
    try:
        sql = """
        INSERT INTO recommendations (user_id, product_id, score, rank_order, applied_rule)
        VALUES (%s, %s, %s, %s, %s);
        """
        records = [
            (rec["user_id"], rec["product_id"], rec.get("relevance_score", rec.get("score", 0.0)), rec["rank_order"], rec["applied_rule"])
            for rec in recommendations
        ]
        cursor.executemany(sql, records)
        conn.commit()
        logger.info(f"Inserted {len(records)} recommendations into MySQL recommendations table.")
    finally:
        cursor.close()
        conn.close()


def insert_decision_log(user_id, applied_rules, recommendations, relevance_scores, timestamp, config_path="config.json"):
    """Insert audit trail entry into MySQL decision_logs table."""
    conn = get_db_connection(config_path)
    cursor = conn.cursor()
    try:
        sql = """
        INSERT INTO decision_logs (user_id, applied_rules_json, recommendations_json, relevance_scores_json, timestamp)
        VALUES (%s, %s, %s, %s, %s);
        """
        cursor.execute(sql, (
            user_id,
            json.dumps(applied_rules),
            json.dumps(recommendations),
            json.dumps(relevance_scores),
            timestamp
        ))
        conn.commit()
        logger.info(f"Logged recommendation decision for User {user_id} into MySQL decision_logs table.")
    finally:
        cursor.close()
        conn.close()
