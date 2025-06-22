import pandas as pd
import matplotlib.pyplot as plt
import os

def dashboard_analysis(file_path, out_path):


    try:
        df = pd.read_excel(file_path)
    except FileNotFoundError:
        print(f"Ошибка: Файл {file_path} не найден.")
        return
    except Exception as e:
        print(f"Ошибка при чтении файла: {e}")
        return

    df['transaction_date'] = pd.to_datetime(df['transaction_date'], format='%d.%m.%Y')
    df['unit_price'] = pd.to_numeric(df['unit_price'].astype(str).str.replace(',', '.'), errors='coerce')
    if df['unit_price'].isna().any():
        print("Предупреждение: Некоторые значения в 'unit_price' не удалось преобразовать в числа.")
    df['month'] = df['transaction_date'].dt.to_period('M')

    last_month = df['transaction_date'].max().month
    df_last_month = df[df['transaction_date'].dt.month == last_month]

    if df_last_month.empty:
        print("Нет данных за последний месяц.")
        return

    total_revenue = (df_last_month['transaction_qty'] * df_last_month['unit_price']).sum()
    total_cost = (df_last_month['transaction_qty'] * df_last_month['unit_price'] * 0.65).sum()
    net_profit = total_revenue - total_cost

    print("🧾 Доход за последний месяц:", round(total_revenue, 2))
    print("💸 Расход за последний месяц:", round(total_cost, 2))
    print("📈 Чистая прибыль за последний месяц:", round(net_profit, 2))

    monthly_sales = df.groupby('month')['transaction_qty'].sum().reset_index()
    monthly_sales['label'] = (monthly_sales['transaction_qty'] / 1000).round(2).astype(str) + ' тыс.'

    plt.figure(figsize=(8, 5))
    bars = plt.bar(monthly_sales['month'].astype(str), monthly_sales['transaction_qty'], color='skyblue')
    for bar, label in zip(bars, monthly_sales['label']):
        plt.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.1, label, ha='center', va='bottom')

    plt.title('Месячные продажи (в штуках)')
    plt.xlabel('Месяц')
    plt.ylabel('Количество проданных товаров')
    plt.xticks(rotation=45)
    plt.grid(axis='y', linestyle='--', alpha=0.5)
    plt.tight_layout()
    plt.savefig(os.path.join(out_path, 'month_sales.png'))
    plt.close()

    product_sales = df.groupby('product_detail').agg({
        'transaction_qty': 'sum',
        'unit_price': 'mean'
    }).reset_index()

    product_sales['revenue'] = product_sales['transaction_qty'] * product_sales['unit_price']
    product_sales['cost'] = product_sales['transaction_qty'] * product_sales['unit_price'] * 0.65
    product_sales['profit'] = product_sales['revenue'] - product_sales['cost']

    top_10 = product_sales.sort_values(by='transaction_qty', ascending=False).head(10)

    plt.figure(figsize=(10, 6))
    bars = plt.barh(top_10['product_detail'], top_10['profit'], color='mediumseagreen')
    plt.xlabel('Прибыль (в у.е.)')
    plt.title('Топ-10 продуктов по прибыли')

    for bar in bars:
        plt.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height()/2,
                 f"{bar.get_width():.2f}", va='center')

    plt.gca().invert_yaxis()
    plt.tight_layout()
    plt.savefig(os.path.join(out_path, 'products_profit.png'))
    plt.close()

    return total_revenue, total_cost, net_profit

# Пример вызова функции
file_path = 'C:/Users/Величайший/Desktop/Coffee Shop Sales.xlsx'
out_path = 'C:/Users/Величайший/Desktop/output/'
result = dashboard_analysis(file_path, out_path)
if result:
    print("Возвращенные значения:", result)