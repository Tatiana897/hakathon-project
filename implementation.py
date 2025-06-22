import pandas as pd
from datetime import timedelta

sales_path = r"D:/Users/ASUS-X509J/Desktop/Coffee Shop Sales.xlsx"
sales = pd.read_excel(sales_path, sheet_name="Transactions")

price_df = (sales.groupby("product_detail")["unit_price"]
                 .median()
                 .reset_index()
                 .rename(columns={"unit_price": "current_price"}))
price_df["cost_per_unit"] = (price_df["current_price"] * 0.6).round(2)

sales["transaction_date"] = pd.to_datetime(sales["transaction_date"])
cutoff = sales["transaction_date"].max() - timedelta(days=42)
sales = sales[sales["transaction_date"] >= cutoff]

grouped = (sales.groupby(["product_detail", "transaction_date"])["transaction_qty"]
                .sum()
                .reset_index())

total_qty = grouped.groupby("product_detail")["transaction_qty"].sum()
products_ok = total_qty[total_qty >= 50].index
grouped = grouped[grouped["product_detail"].isin(products_ok)]

recommendations = []

for prod, sub in grouped.groupby("product_detail"):
    sub = sub.copy()
    mean = sub["transaction_qty"].mean()
    if mean == 0:
        continue

    peak_row = sub.loc[sub["transaction_qty"].idxmax()]
    low_row  = sub.loc[sub["transaction_qty"].idxmin()]

    for row, label in [(peak_row, "raise"), (low_row, "discount")]:
        ratio = (row["transaction_qty"] - mean) / mean
        delta_pct = 0.05 * ratio
        delta_pct = max(min(delta_pct, 0.20), -0.20)
        if abs(delta_pct) < 0.03:
            continue

        current_price = price_df[price_df["product_detail"] == prod]["current_price"].values[0]
        cost = price_df[price_df["product_detail"] == prod]["cost_per_unit"].values[0]
        new_price = round(max(current_price * (1 + delta_pct), cost * 1.2), 2)

        recommendations.append({
            "product_detail": prod,
            "transaction_date": row["transaction_date"].date(),
            "current_price": round(current_price, 2),
            "new_price": new_price,
            "delta_pct": round(delta_pct * 100, 1),
            "action_type": label
        })

recommend_df = pd.DataFrame(recommendations)
recommend_df = recommend_df.sort_values(["product_detail", "transaction_date"])
print(recommend_df.head(15))

