import os
import random
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def generate_sample_sales_data(
    file_path_csv: str = "sales_data.csv",
    file_path_excel: str = "sales_data.xlsx",
    num_records: int = 1200,
    seed: int = 42
) -> pd.DataFrame:
    """
    Generates a realistic multi-year sales dataset with products, categories, 
    regions, customer segments, pricing, and intentional minor anomalies (for cleaning validation).
    """
    random.seed(seed)
    np.random.seed(seed)

    products = [
        {"id": "PROD-101", "name": "Enterprise Cloud Suite", "category": "Software", "base_price": 1200.00},
        {"id": "PROD-102", "name": "AI Analytics License", "category": "Software", "base_price": 850.00},
        {"id": "PROD-103", "name": "Pro Workstation Laptop", "category": "Hardware", "base_price": 1500.00},
        {"id": "PROD-104", "name": "Ultra-Wide Monitor 34", "category": "Hardware", "base_price": 600.00},
        {"id": "PROD-105", "name": "Ergonomic Desk Chair", "category": "Furniture", "base_price": 350.00},
        {"id": "PROD-106", "name": "Smart Conference Hub", "category": "Electronics", "base_price": 950.00},
        {"id": "PROD-107", "name": "Cybersecurity Gateway", "category": "Software", "base_price": 1100.00},
        {"id": "PROD-108", "name": "Standing Executive Desk", "category": "Furniture", "base_price": 750.00},
        {"id": "PROD-109", "name": "Wireless Noise-Canceling Headset", "category": "Electronics", "base_price": 250.00},
        {"id": "PROD-110", "name": "Server Rack Server X1", "category": "Hardware", "base_price": 3200.00},
    ]

    regions = ["North America", "Europe", "Asia-Pacific", "Latin America", "Middle East & Africa"]
    segments = ["Enterprise", "Small & Medium Business", "Consumer", "Government"]
    payment_methods = ["Credit Card", "Wire Transfer", "Corporate Invoice", "PayPal"]

    start_date = datetime(2023, 1, 1)
    end_date = datetime(2025, 12, 31)
    date_range_days = (end_date - start_date).days

    records = []
    for i in range(1, num_records + 1):
        prod = random.choice(products)
        days_offset = random.randint(0, date_range_days)
        tx_date = start_date + timedelta(days=days_offset)
        
        # Add seasonal sales volume boost in Q4
        quantity_weights = [1, 2, 3, 4, 5, 8, 10]
        if tx_date.month in [11, 12]:
            qty = random.choice([3, 5, 8, 10, 15, 20])
        else:
            qty = random.choice(quantity_weights)

        discount = random.choice([0.0, 0.05, 0.10, 0.15, 0.20])
        sales_amount = round(qty * prod["base_price"] * (1 - discount), 2)
        region = random.choice(regions)
        segment = random.choice(segments)
        payment = random.choice(payment_methods)

        records.append({
            "Transaction_ID": f"TXN-{10000 + i}",
            "Date": tx_date.strftime("%Y-%m-%d"),
            "Product_ID": prod["id"],
            "Product": prod["name"],
            "Category": prod["category"],
            "Unit_Price": prod["base_price"],
            "Region": region,
            "Quantity": qty,
            "Discount_Pct": discount,
            "Sales_Amount": sales_amount,
            "Customer_Segment": segment,
            "Payment_Method": payment
        })

    df = pd.DataFrame(records)

    # Introduce intentional anomalies for data validation and cleaning demonstration
    # 1. Duplicate rows (10 rows)
    duplicates = df.sample(n=10, random_state=seed)
    df = pd.concat([df, duplicates], ignore_index=True)

    # 2. Whitespace in categorical strings
    df.loc[df.sample(n=15, random_state=seed).index, "Region"] += "  "

    # 3. Missing non-critical entries
    df.loc[df.sample(n=8, random_state=seed).index, "Payment_Method"] = np.nan

    # Save to CSV
    df.to_csv(file_path_csv, index=False)
    print(f"Sample dataset successfully exported to CSV: {file_path_csv} ({len(df)} records)")

    # Save to Excel
    df.to_excel(file_path_excel, index=False, sheet_name="Sales_Data")
    print(f"Sample dataset successfully exported to Excel: {file_path_excel} ({len(df)} records)")

    return df

if __name__ == "__main__":
    generate_sample_sales_data()
