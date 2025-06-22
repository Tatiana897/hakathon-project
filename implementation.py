import pandas as pd
from datetime import timedelta
from pathlib import Path

def price_recommendations(
        sales_path: str | Path,
        lookback_days: int = 42,
        min_sales: int = 50,
        cost_factor: float = 0.60,
        elasticity: float = 0.05,    
        max_delta: float = 0.20,      
        min_delta: float = 0.03      
    ) -> pd.DataFrame:

    sales = pd.read_excel(sales_path, sheet_name="Transactions")

    price_df = (sales.groupby("product_detail")["unit_price"]
                     .median()
                     .reset_index()
                     .rename(columns={"unit_price": "current_price"}))
    price_df["cost_per_unit"] = (price_df["current_price"] * cost_factor).round(2)

    sales["transaction_date"] = pd.to_datetime(sales["transaction_date"])
    cutoff = sales["transaction_date"].max() - timedelta(days=lookback_days)
    sales = sales[sales["transaction_date"] >= cutoff]

    grouped = (sales.groupby(["product_detail", "transaction_date"])["transaction_qty"]
                    .sum()
                    .reset_index())

    totals = grouped.groupby("product_detail")["transaction_qty"].sum()
    whitelisted = totals[totals >= min_sales].index
    grouped = grouped[grouped["product_detail"].isin(whitelisted)]

    recs = []

    for prod, sub in grouped.groupby("product_detail"):
        mean_qty = sub["transaction_qty"].mean()
        if mean_qty == 0:
            continue

        peak_row = sub.loc[sub["transaction_qty"].idxmax()]
        low_row  = sub.loc[sub["transaction_qty"].idxmin()]

        for row, tag in [(peak_row, "raise"), (low_row, "discount")]:
            ratio = (row["transaction_qty"] - mean_qty) / mean_qty
            delta_pct = elasticity * ratio
            delta_pct = max(min(delta_pct,  max_delta), -max_delta)

            if abs(delta_pct) < min_delta:
                continue  

            cur = price_df.loc[price_df["product_detail"] == prod, "current_price"].iat[0]
            cost = price_df.loc[price_df["product_detail"] == prod, "cost_per_unit"].iat[0]
            new = round(max(cur * (1 + delta_pct), cost * 1.2), 2)

            recs.append({
                "product_detail":   prod,
                "transaction_date": row["transaction_date"].date(),
                "current_price":    round(cur, 2),
                "new_price":        new,
                "delta_pct":        round(delta_pct * 100, 1),
                "action_type":      tag
            })

    return (pd.DataFrame(recs)
              .sort_values(["product_detail", "transaction_date"])
              .reset_index(drop=True))


if __name__ == "__main__":
    df_rec = price_recommendations(
        sales_path=r"D:/Users/ASUS-X509J/Desktop/Coffee Shop Sales.xlsx"
    )
    print(df_rec.head(10))
