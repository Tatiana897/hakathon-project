import pandas as pd
import matplotlib.pyplot as plt
from textwrap import wrap

file_path = r"D:/Users/ASUS-X509J/Desktop/Coffee Shop Sales.xlsx"   
df = pd.read_excel(file_path, sheet_name="Transactions")

df["hour"]   = pd.to_datetime(df["transaction_time"].astype(str)).dt.hour
df["minute"] = pd.to_datetime(df["transaction_time"].astype(str)).dt.minute
df = df[(df["hour"] >= 8) & (df["hour"] < 22)]                     

bins   = list(range(8, 24, 2))                                     # 08-10, 10-12, …
labels = [f"{h:02d}-{h+2:02d}" for h in bins[:-1]]
df["time_bin"] = pd.cut(df["hour"] + df["minute"]/60,
                        bins=bins, labels=labels, right=False)

total_qty = (df.groupby("time_bin")["transaction_qty"]
               .sum()
               .reindex(labels)
               .fillna(0))

agg = (df.groupby(["time_bin", "product_detail"])["transaction_qty"]
         .sum()
         .reset_index())

top_df = (agg.sort_values(["time_bin", "transaction_qty"], ascending=[True, False])
                .drop_duplicates("time_bin")
                .set_index("time_bin")
                .reindex(labels)
                .reset_index())

least_df = (agg[agg["transaction_qty"] > 0]                 
                .sort_values(["time_bin", "transaction_qty"])
                .drop_duplicates("time_bin")
                .set_index("time_bin")
                .reindex(labels)
                .reset_index())
least_df["transaction_qty"].fillna(0, inplace=True)
least_df["product_detail"].fillna("нет продаж", inplace=True)

plt.figure(figsize=(12, 6))
bars = plt.bar(total_qty.index, total_qty.values, color="#3366cc")

for bar, prod in zip(bars, top_df["product_detail"]):
    wrapped = "\n".join(wrap(prod, 12))
    h = bar.get_height()
    if h < 2000:                                                 
        plt.text(bar.get_x()+bar.get_width()/2, h+500, wrapped,
                 ha="center", va="bottom", fontsize=9, fontweight="bold")
    else:                                                       
        plt.text(bar.get_x()+bar.get_width()/2, h/2, wrapped,
                 ha="center", va="center", fontsize=9, fontweight="bold",
                 color="white")

plt.title("Самые востребованные продукты дня по времени", fontweight="bold")
plt.xlabel("Интервал времени")
plt.ylabel("Количество проданных позиций")
plt.grid(axis="y", linestyle="--", alpha=0.5)
plt.tight_layout()
plt.show()

plt.figure(figsize=(12, 6))
bars = plt.bar(least_df["time_bin"], least_df["transaction_qty"], color="#cc3333")

for bar, name, qty in zip(bars, least_df["product_detail"], least_df["transaction_qty"]):
    wrapped = "\n".join(wrap(name, 14))
    h = bar.get_height()
    txt_y = h/2 if h >= 3 else h + 0.2
    va    = "center" if h >= 3 else "bottom"
    color = "white" if h >= 3 else "black"
    plt.text(bar.get_x()+bar.get_width()/2, txt_y, wrapped,
             ha="center", va=va, fontsize=8, fontweight="bold", color=color)

plt.title("Наименее востребованные товары по времени суток", fontweight="bold")
plt.xlabel("Интервал времени")
plt.ylabel("Количество продаж товара-аутсайдера")
plt.grid(axis="y", linestyle="--", alpha=0.4)
plt.tight_layout()
plt.show()
