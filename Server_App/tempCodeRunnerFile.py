import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for matplotlib
import matplotlib.pyplot as plt
from neuralprophet import NeuralProphet
import random
import numpy as np
import torch
import os
import pickle
import pytorch_lightning as pl
try:
    import torchvision
except ImportError:
    torchvision = None

# Strict version checks
required_versions = {
    'torch': '1.13.1',
    'torchvision': '0.14.1',
    'neuralprophet': '0.6.0',
    'pytorch_lightning': '1.9.5'
}
for lib, req_version in required_versions.items():
    try:
        module = __import__(lib.replace('-', '_'))
        installed_version = module.__version__.split('+')[0]  # Remove suffixes like +cu117
        if installed_version != req_version:
            raise RuntimeError(
                f"Installed {lib} version {installed_version} does not match required {req_version}. "
                f"Run: pip install {lib}=={req_version}"
            )
    except ImportError:
        raise RuntimeError(f"Library {lib} is not installed. Run: pip install {lib}=={req_version}")
    except AttributeError:
        raise RuntimeError(f"Could not determine version of {lib}.")

def train_and_save_models(file_path, out_path):
    random.seed(42)
    np.random.seed(42)
    torch.manual_seed(42)

    # Normalize and create directories
    out_path = os.path.normpath(out_path)
    models_dir = os.path.join(out_path, 'models')
    try:
        os.makedirs(models_dir, exist_ok=True)
        print(f"Created/verified directory: {models_dir}")
    except PermissionError:
        print(f"Error: No permission to create directory {models_dir}. Check write access.")
        return {}
    except Exception as e:
        print(f"Error creating directory {models_dir}: {e}")
        return {}

    # Load data
    try:
        df = pd.read_excel(file_path)
    except FileNotFoundError:
        print(f"Error: File {file_path} not found.")
        return {}
    except Exception as e:
        print(f"Error reading file: {e}")
        return {}
    
    # Check required columns
    required_columns = ['transaction_date', 'transaction_qty', 'unit_price', 'product_type']
    if not all(col in df.columns for col in required_columns):
        print(f"Error: Missing required columns: {set(required_columns) - set(df.columns)}")
        return {}

    # Transform date and price
    df['transaction_date'] = pd.to_datetime(df['transaction_date'], format='%d.%m.%Y', errors='coerce')
    if df['transaction_date'].isna().any():
        print("Error: Some 'transaction_date' values could not be converted to dates.")
        return {}
    
    df['unit_price'] = pd.to_numeric(df['unit_price'].astype(str).str.replace(',', '.'), errors='coerce')
    if df['unit_price'].isna().any():
        print("Warning: Some 'unit_price' values could not be converted to numbers.")

    # Create start_quantity
    df['start_quantity'] = df['transaction_qty'] * 1.2

    # Check for NaN in transaction_qty
    if df['transaction_qty'].isna().any():
        print("Error: 'transaction_qty' contains missing values.")
        return {}

    # Aggregate data by product_type and date
    daily_sales_by_product = df.groupby(['transaction_date', 'product_type']).agg({
        'transaction_qty': 'sum',
        'start_quantity': 'sum'
    }).reset_index()
    daily_sales_by_product.rename(columns={'transaction_date': 'ds', 'transaction_qty': 'y'}, inplace=True)

    # Get unique product types
    product_types = daily_sales_by_product['product_type'].unique()

    # Dictionary to store model information
    model_info = {}

    # Train model for each product_type
    for product in product_types:
        product_df = daily_sales_by_product[daily_sales_by_product['product_type'] == product].copy()
        
        if len(product_df) < 10:
            print(f"Skipped product {product}: insufficient data (<10 records).")
            continue
        
        # Sort and interpolate missing dates
        product_df = product_df.sort_values('ds')
        date_range = pd.date_range(start=product_df['ds'].min(), end=product_df['ds'].max(), freq='D')
        
        full_df = pd.DataFrame({'ds': date_range})
        full_df = full_df.merge(product_df, on='ds', how='left')
        
        full_df['y'] = full_df['y'].interpolate(method='linear').fillna(0)
        full_df['start_quantity'] = full_df['start_quantity'].interpolate(method='linear').fillna(0)
        full_df['product_type'] = product
        
        if len(full_df) > 15:
            print(f"Data type of 'ds' for product {product} (index 15): {type(full_df.iloc[15]['ds'])}")
        else:
            print(f"Product {product}: insufficient rows for index 15 (total {len(full_df)} rows).")

        train_df = full_df[['ds', 'y']].copy()
        
        try:
            train_df_split, val_df_split = NeuralProphet().split_df(train_df, valid_p=0.2)
        except Exception as e:
            print(f"Error splitting data for {product}: {e}")
            continue
        
        model = NeuralProphet(
            epochs=100,
            trend_reg=0.5,
            seasonality_reg=1.0,
            daily_seasonality=True,
            weekly_seasonality=True,
            yearly_seasonality=False,
            seasonality_mode='additive',
            learning_rate=0.05
        )
        try:
            model.fit(train_df_split, freq='D', validation_df=val_df_split)
        except Exception as e:
            print(f"Error training model for {product}: {e}")
            continue
        
        # Save model
        model_path = os.path.normpath(os.path.join(models_dir, f'model_{product.lower().replace(" ", "_")}.pkl'))
        data_path = os.path.normpath(os.path.join(models_dir, f'data_{product.lower().replace(" ", "_")}.pkl'))
        try:
            with open(model_path, 'wb') as f:
                pickle.dump(model, f)
            with open(data_path, 'wb') as f:
                pickle.dump(full_df, f)
            model_info[product] = {'model_path': model_path, 'data_path': data_path}
            print(f"Model and data for {product} saved to {model_path} and {data_path}")
        except PermissionError:
            print(f"Error saving model for {product}: No permission to write to {model_path}")
            continue
        except Exception as e:
            print(f"Error saving model for {product}: {e}")
            continue

    return model_info

def load_and_display_results(out_path, model_info):
    # Validate model_info type
    if not isinstance(model_info, dict):
        print(f"Error: model_info must be a dictionary, got {type(model_info)}: {model_info}")
        return {}, ["Анализ потребностей в продукции:\n"]

    out_path = os.path.normpath(out_path)  # Normalize path
    try:
        os.makedirs(out_path, exist_ok=True)
        print(f"Created/verified directory: {out_path}")
    except Exception as e:
        print(f"Error creating directory {out_path}: {e}")
        return {}, ["Анализ потребностей в продукции:\n"]

    forecast_results = {}
    
    for product, info in model_info.items():
        model_path = info['model_path']
        data_path = info['data_path']
        
        try:
            with open(model_path, 'rb') as f:
                model = pickle.load(f)
            with open(data_path, 'rb') as f:
                full_df = pickle.load(f)
        except Exception as e:
            print(f"Error loading model or data for {product}: {e}")
            continue
        
        train_df = full_df[['ds', 'y']].copy()
        try:
            train_df_split, _ = NeuralProphet().split_df(train_df, valid_p=0.2)
        except Exception as e:
            print(f"Error splitting data for {product}: {e}")
            continue
        
        try:
            future = model.make_future_dataframe(train_df_split, periods=30)
            print(f"For product {product}: future.head()\n{future.head()}")  # Debug output
            forecast = model.predict(future)
        except Exception as e:
            print(f"Error forecasting for {product}: {e}")
            continue
        
        last_date = train_df_split['ds'].max()
        forecast_future = forecast[forecast['ds'] > last_date]
        
        forecasted_demand = forecast_future['yhat1'].sum()
        
        last_month_start = train_df['ds'].max() - pd.Timedelta(days=30)
        last_month_data = full_df[(full_df['ds'] >= last_month_start) & (full_df['ds'] <= train_df['ds'].max())]
        current_supply = last_month_data['start_quantity'].sum() if not last_month_data.empty else 0
        
        if current_supply > 0:
            percentage_change = ((forecasted_demand - current_supply) / current_supply) * 100
        else:
            percentage_change = 0
        
        forecast_results[product] = percentage_change

    # Analyze and display results
    sorted_results = dict(sorted(forecast_results.items(), key=lambda x: abs(x[1]), reverse=True))
    
    text_results = ["Анализ потребностей в продукции:\n"]
    top_5_results = list(sorted_results.items())[:5]
    for product, change in top_5_results:
        action = 1 if change > 0 else 0
        result_line = f"{action} {product} {abs(change):.2f}\n"
        text_results.append(result_line)
        print(result_line.strip())

    # Save text results
    text_output_path = os.path.join(out_path, 'needs_analysis_results.txt')
    try:
        with open(text_output_path, 'w', encoding='utf-8') as f:
            f.writelines(text_results)
        print(f"Text results saved to {text_output_path}")
    except Exception as e:
        print(f"Error saving text file: {e}")

    # Visualize for the first product
    if top_5_results:
        sample_product = top_5_results[0][0]
        try:
            with open(model_info[sample_product]['model_path'], 'rb') as f:
                model = pickle.load(f)
            with open(model_info[sample_product]['data_path'], 'rb') as f:
                full_df = pickle.load(f)
            
            train_df = full_df[['ds', 'y']].copy()
            train_df_split, _ = NeuralProphet().split_df(train_df, valid_p=0.2)
            
            future = model.make_future_dataframe(train_df_split, periods=30)
            forecast = model.predict(future)
            forecast_future = forecast[forecast['ds'] > train_df_split['ds'].max()]
            
            plt.figure(figsize=(12, 6))
            plt.plot(train_df_split['ds'], train_df_split['y'], label=f'Исторические продажи {sample_product}', color='orange')
            plt.plot(forecast_future['ds'], forecast_future['yhat1'], label=f'Прогноз {sample_product}', color='blue')
            plt.axvline(x=train_df_split['ds'].max(), color='gray', linestyle='--', label='Конец исторических данных')
            plt.title(f'Прогноз продаж {sample_product} на следующие 30 дней')
            plt.xlabel('Дата')
            plt.ylabel('Продажи за день')
            plt.legend()
            plt.grid(True)
            plt.tight_layout()
            plt.savefig(os.path.join(out_path, f'forecast_{sample_product.lower().replace(" ", "_")}.png'))
            plt.close()
        except Exception as e:
            print(f"Error visualizing for {sample_product}: {e}")
    else:
        print("Warning: No results available for visualization (forecast_results is empty).")

    return forecast_results, text_results

# Example usage
file_path = 'C:/Users/Величайший/Desktop/Coffee Shop Sales.xlsx'
out_path = 'C:/Users/Величайший/Desktop/output/'

# Step 1: Train and save models
model_info = train_and_save_models(file_path, out_path)
if model_info:
    print("Training and saving models completed successfully.")
else:
    print("Training and saving models failed, model_info is empty or invalid.")

# Step 2: Load models and display results
if model_info:
    result = load_and_display_results(out_path, model_info)
    if result is not None:
        forecast_results, text_results = result
        print("Needs analysis completed successfully.")
        print("Forecast results:", forecast_results)
        print("Text results:\n" + ''.join(text_results))
else:
    print("Skipping load_and_display_results due to invalid model_info.")