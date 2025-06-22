import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
from neuralprophet import NeuralProphet
import random
import numpy as np
import torch
import os

def forecast_next_month_onething(file_path, out_path, product_name):
    matplotlib.use('TkAgg')

    random.seed(42)
    np.random.seed(42)
    torch.manual_seed(42)

    if not os.path.exists(out_path):
        os.makedirs(out_path)

    try:
        df = pd.read_excel(file_path)
    except FileNotFoundError:
        print(f"Ошибка: Файл {file_path} не найден.")
        return None
    except Exception as e:
        print(f"Ошибка при чтении файла: {e}")
        return None

    df['transaction_date'] = pd.to_datetime(df['transaction_date'], format='%d.%m.%Y')
    df['unit_price'] = pd.to_numeric(df['unit_price'].astype(str).str.replace(',', '.'), errors='coerce')
    if df['unit_price'].isna().any():
        print("Предупреждение: Некоторые значения в 'unit_price' не удалось преобразовать в числа.")

    product_df = df[df['product_type'] == product_name].copy()
    if product_df.empty:
        print(f"Ошибка: Данные для продукта '{product_name}' не найдены.")
        return None

    daily_sales = product_df.groupby('transaction_date')['transaction_qty'].sum().reset_index()
    daily_sales.rename(columns={'transaction_date': 'ds', 'transaction_qty': 'y'}, inplace=True)

    daily_sales = daily_sales.sort_values('ds').reset_index(drop=True)

    date_range = pd.date_range(start=daily_sales['ds'].min(), end=daily_sales['ds'].max(), freq='D')
    daily_sales = daily_sales.set_index('ds').reindex(date_range, fill_value=0).reset_index()
    daily_sales.rename(columns={'index': 'ds'}, inplace=True)


    train_df = daily_sales.copy()

    model = NeuralProphet(
        epochs=100,
        trend_reg=2.0,  
        seasonality_reg=2,  
        daily_seasonality=True,
        weekly_seasonality=True,
        yearly_seasonality=False,  
        seasonality_mode='additive'
    )

    model.fit(train_df, freq='D')

    future = model.make_future_dataframe(train_df, periods=30)
    forecast = model.predict(future)


    plt.figure(figsize=(12, 6))
    plt.plot(train_df['ds'], train_df['y'], label=f'Исторические продажи {product_name}', color='orange')
    plt.plot(forecast['ds'], forecast['yhat1'], label=f'Прогноз на 30 дней {product_name}', color='blue')
    plt.axvline(x=train_df['ds'].iloc[-1], color='gray', linestyle='--', label='Конец исторических данных')
    plt.title(f'Прогноз продаж {product_name} на следующие 30 дней')
    plt.xlabel('Дата')
    plt.ylabel('Продажи за день')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(os.path.join(out_path, 'forecast_next_m1.png'))
    plt.close()

  

# Пример вызова функции
file_path = 'C:/Users/Величайший/Desktop/Coffee Shop Sales.xlsx'
out_path = 'C:/Users/Величайший/Desktop/output/'
product_name = 'Hot chocolate'
result = forecast_next_month_onething(file_path, out_path, product_name)
if result is not None:
    print("Прогнозирование завершено успешно.")
    print("Прогноз на следующие 30 дней:")
    print(result)