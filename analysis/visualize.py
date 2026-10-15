"""
Mamaearth Returns & Growth Intelligence Pipeline.
Part 2 Task 11: Visualizations.
Pipeline saves two chart images into visual directory.
Command runs from project root: python analysis/visualize.py
"""

import pathlib
import sys

import matplotlib.pyplot as plt
import pandas as pd

# UTF-8 stdout configuration for Windows terminals
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

ROOT     = pathlib.Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
VIZ_DIR  = ROOT / "visualizations"
VIZ_DIR.mkdir(exist_ok=True)

# Pipeline cleaning steps

customers = pd.read_csv(DATA_DIR / "customers.csv")
products  = pd.read_csv(DATA_DIR / "products.csv")
orders    = pd.read_csv(DATA_DIR / "orders.csv")

orders["payment_method"] = orders["payment_method"].str.strip().str.upper()

NAT_KEY = [
    "customer_id", "product_id", "order_date", "quantity",
    "discount_pct", "payment_method", "rating", "returned",
]
orders_clean = orders[~orders.duplicated(subset=NAT_KEY, keep="first")].copy().reset_index(drop=True)

orders_clean["discount_pct"] = orders_clean["discount_pct"].fillna(0)
orders_clean["rating"]       = orders_clean["rating"].fillna(orders_clean["rating"].median())

merged = (
    orders_clean
    .merge(products,  on="product_id")
    .merge(customers, on="customer_id")
)
merged["order_value"] = (
    merged["quantity"] * merged["price"] * (1 - merged["discount_pct"] / 100)
)

# Outlier detection bounds use upper limit of 3.5 units.
Q1, Q3 = merged["quantity"].quantile(0.25), merged["quantity"].quantile(0.75)
IQR    = Q3 - Q1
merged["is_outlier"] = (
    (merged["quantity"] < Q1 - 1.5 * IQR) | (merged["quantity"] > Q3 + 1.5 * IQR)
)

# Plot 1: Return rate by payment method

ret_by_pay = (
    merged.groupby("payment_method")["returned"]
    .mean()
    .mul(100)
    .round(1)
    .sort_values(ascending=False)
)

fig, ax = plt.subplots(figsize=(8, 5))
colors = ["#e74c3c", "#3498db", "#2ecc71"]
bars   = ax.bar(ret_by_pay.index, ret_by_pay.values, color=colors, width=0.5, edgecolor="white")

for bar, val in zip(bars, ret_by_pay.values):
    ax.text(
        bar.get_x() + bar.get_width() / 2,
        bar.get_height() + 0.8,
        f"{val}%",
        ha="center", va="bottom", fontsize=13, fontweight="bold",
    )

ax.set_title("COD Returns at 44.4% - 3x Card", fontsize=14, fontweight="bold", pad=14)
ax.set_xlabel("Payment Method", fontsize=11)
ax.set_ylabel("Return Rate (%)", fontsize=11)
ax.set_ylim(0, 56)
ax.spines[["top", "right"]].set_visible(False)

plt.tight_layout()
out1 = VIZ_DIR / "return_rate_by_payment.png"
plt.savefig(out1, dpi=150)
plt.close()
print(f"Saved -> {out1}")

# Plot 2: Monthly revenue trend

merged["order_date"] = pd.to_datetime(merged["order_date"])
merged["year_month"] = merged["order_date"].dt.to_period("M")

monthly_corrected = (
    merged[~merged["is_outlier"]]
    .groupby("year_month")["order_value"]
    .sum()
    .round(2)
)

months   = [str(p) for p in monthly_corrected.index]
revenues = monthly_corrected.values

fig, ax = plt.subplots(figsize=(10, 5))
ax.plot(months, revenues, marker="o", linewidth=2.5, color="#2980b9", markersize=8, zorder=3)
ax.fill_between(months, revenues, alpha=0.12, color="#2980b9")

for x, y in zip(months, revenues):
    ax.annotate(
        f"INR {y:,.0f}",
        xy=(x, y),
        xytext=(0, 12),
        textcoords="offset points",
        ha="center", fontsize=9,
    )

ax.set_title(
    "Monthly Revenue Trend - Peak: March 2026",
    fontsize=14, fontweight="bold", pad=14,
)
ax.set_xlabel("Month", fontsize=11)
ax.set_ylabel("Revenue (INR)", fontsize=11)
ax.set_ylim(0, max(revenues) * 1.25)
ax.spines[["top", "right"]].set_visible(False)
plt.xticks(rotation=20, ha="right")
plt.tight_layout()

out2 = VIZ_DIR / "monthly_revenue_trend.png"
plt.savefig(out2, dpi=150)
plt.close()
print(f"Saved -> {out2}")
