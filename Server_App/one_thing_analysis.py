import pandas as pd
import matplotlib.pyplot as plt

# Загрузка данных из Excel
file_path = 'C://Users//Величайший//Desktop//Coffee Shop Sales.xlsx'
df = pd.read_excel(file_path)

# Преобразование данных
df['transaction_date'] = pd.to_datetime(df['transaction_date'], format='%d.%m.%Y')
df['unit_price'] = df['unit_price'].astype(str).str.replace(',', '.').astype(float)
df['month'] = df['transaction_date'].dt.to_period('M')
df['hour'] = pd.to_datetime(df['transaction_time'], format='%H:%M:%S').dt.hour

# Фильтрация по продукту
chai_df = df[df['product_type'] == 'Brewed Chai tea']

# ----- 1. Динамика продаж по месяцам -----
monthly_chai = chai_df.groupby('month')['transaction_qty'].sum()

plt.figure(figsize=(8, 4))
monthly_chai.plot(kind='bar', color='sandybrown')
plt.title('Динамика продаж Brewed Chai tea по месяцам')
plt.ylabel('Количество проданных единиц')
plt.xlabel('Месяц')
plt.grid(axis='y', linestyle='--', alpha=0.5)
plt.tight_layout()
plt.show()

# ----- 2. Доход и прибыль по месяцам -----
chai_df['revenue'] = chai_df['transaction_qty'] * chai_df['unit_price']
chai_df['cost'] = chai_df['revenue'] * 0.65
chai_df['profit'] = chai_df['revenue'] - chai_df['cost']

monthly_finance = chai_df.groupby('month')[['Доход', 'Расход', 'Прибыль']].sum()

monthly_finance.plot(kind='bar', figsize=(10, 5), color=['#4caf50', '#f44336', '#2196f3'])
plt.title('Доход, себестоимость и прибыль по Brewed Chai tea')
plt.ylabel('Сумма (у.е.)')
plt.xlabel('Месяц')
plt.grid(axis='y', linestyle='--', alpha=0.5)
plt.tight_layout()
plt.show()

# ----- 3. Продажи по времени суток -----
def time_period(hour):
    if 6 <= hour < 12:
        return 'Утро'
    elif 12 <= hour < 18:
        return 'День'
    elif 18 <= hour < 24:
        return 'Вечер'
    else:
        return 'Ночь'

chai_df['time_period'] = chai_df['hour'].apply(time_period)
time_sales = chai_df.groupby('time_period')['transaction_qty'].sum().reindex(['Утро', 'День', 'Вечер', 'Ночь'])

plt.figure(figsize=(6, 4))
time_sales.plot(kind='bar', color='mediumpurple')
plt.title('Продажи Brewed Chai tea по времени суток')
plt.ylabel('Количество проданных единиц')
plt.xlabel('Время суток')
plt.grid(axis='y', linestyle='--', alpha=0.5)
plt.tight_layout()
plt.show()
