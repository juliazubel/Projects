"""
Generates a realistic financial transactions dataset for demo purposes.
Run this once to create data/transactions.csv
"""

from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

np.random.seed(42)

OUTPUT_PATH = Path(__file__).parent / "transactions.csv"

N = 2000
start_date = datetime(2023, 1, 1)
dates = [start_date + timedelta(days=np.random.randint(0, 730)) for _ in range(N)]

categories = ["Revenue", "Expenses", "Investment", "Refund", "Transfer"]
regions = ["North", "South", "East", "West", "Central"]
departments = ["Sales", "Marketing", "Operations", "R&D", "HR"]

category_weights = {
    "Revenue":    (5000, 50000),
    "Expenses":   (-20000, -500),
    "Investment": (-100000, -5000),
    "Refund":     (-5000, -100),
    "Transfer":   (-10000, 10000),
}

amounts = []
for _ in range(N):
    cat = np.random.choice(categories, p=[0.35, 0.30, 0.10, 0.10, 0.15])
    lo, hi = category_weights[cat]
    amounts.append((cat, round(np.random.uniform(lo, hi), 2)))

cat_col, amt_col = zip(*amounts, strict=True)

# Inject ~3% anomalies
anomaly_idx = np.random.choice(N, size=int(N * 0.03), replace=False)
amt_list = list(amt_col)
for i in anomaly_idx:
    amt_list[i] = round(amt_list[i] * np.random.choice([-8, 7, 10]), 2)

# Inject ~2% nulls
df = pd.DataFrame({
    "transaction_id": [f"TXN-{i:05d}" for i in range(1, N + 1)],
    "date": dates,
    "category": list(cat_col),
    "amount": amt_list,
    "region": np.random.choice(regions, N),
    "department": np.random.choice(departments, N),
    "approved": np.random.choice([True, False], N, p=[0.92, 0.08]),
})

null_rows = np.random.choice(N, size=int(N * 0.02), replace=False)
df.loc[null_rows, "amount"] = np.nan

df.to_csv(OUTPUT_PATH, index=False)
print(f"Generated {len(df)} transactions → {OUTPUT_PATH}")
