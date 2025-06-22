import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
from neuralprophet import NeuralProphet
import random
import numpy as np
import torch
import os

def forecast_next_month_onething(file_path, out_path):

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
    df['unit_price'] = df['unit_price'].astype(str).str.replace(',', '.').astype(float)

    daily_sales = df.groupby('transaction_date')['transaction_qty'].sum().reset_index()
    daily_sales.rename(columns={'transaction_date': 'ds', 'transaction_qty': 'y'}, inplace=True)

    daily_sales = daily_sales.sort_values('ds').reset_index(drop=True)
    date_range = pd.date_range(start=daily_sales['ds'].min(), end=daily_sales['ds'].max(), freq='D')
    daily_sales = daily_sales.set_index('ds').reindex(date_range).reset_index()
    daily_sales['y'] = daily_sales['y'].interpolate(method='linear')  
    daily_sales.rename(columns={'index': 'ds'}, inplace=True)



    train_df = daily_sales.copy()

    model = NeuralProphet(
        epochs=150, 
        trend_reg=0.5, 
        seasonality_reg=1.0,  
        daily_seasonality=True,
        weekly_seasonality=True,
        yearly_seasonality=False,  
        seasonality_mode='additive',
        learning_rate=0.05  
    )

    train_df, val_df = model.split_df(train_df, valid_p=0.2)  
    model.fit(train_df, freq='D', validation_df=val_df)

    last_date = train_df['ds'].max()
    future = model.make_future_dataframe(train_df, periods=30)  
    forecast = model.predict(future)

    forecast_future = forecast[forecast['ds'] > last_date]

    print("Forecast Sample:")
    print(forecast_future[['ds', 'yhat1']].head(35))

    plt.figure(figsize=(12, 6))
    plt.plot(train_df['ds'], train_df['y'], label='Исторические продажи', color='orange')
    plt.plot(forecast_future['ds'], forecast_future['yhat1'], label='Прогноз на 30 дней', color='blue')
    plt.axvline(x=train_df['ds'].iloc[-1], color='gray', linestyle='--', label='Конец исторических данных')
    plt.title('Прогноз продаж на следующие 30 дней')
    plt.xlabel('Дата')
    plt.ylabel('Продажи за день')
    plt.legend()
    plt.grid(True)
    
    plt.savefig(os.path.join(out_path, 'forecast_next_alldata.png'))
    plt.close()
    try:
        model.plot_components(forecast_future)
        plt.show()
    except Exception as e:
        print(f"Error in plot_components: {e}")

# Пример вызова функции
file_path = 'C:/Users/Величайший/Desktop/Coffee Shop Sales.xlsx'
out_path = 'C:/Users/Величайший/Desktop/output/'
product_name = 'Hot chocolate'
result = forecast_next_month_onething(file_path, out_path)
