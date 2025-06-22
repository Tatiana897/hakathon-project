from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import pandas as pd

# Конфигурация
SERVICE_ACCOUNT_FILE = '../../google.json'  # Путь к вашему JSON-файлу
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
SPREADSHEET_ID = '1-pI8FLZ1hBfAiKSc7NM847Hw9SyrRLG75FIcXIxYK9Q'  # Из URL таблицы

# Аутентификация
creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
service = build('sheets', 'v4', credentials=creds)

def export_gsheet_to_excel(spreadsheet_id, output_file):
    # Получаем метаданные о листах
    spreadsheet = service.spreadsheets().get(
        spreadsheetId=spreadsheet_id
    ).execute()
    
    # Создаем Excel writer
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        for sheet in spreadsheet['sheets']:

            sheet_name = sheet['properties']['title']
            print(f"Обрабатываю лист: {sheet_name}")
            
            # Получаем все данные листа
            result = service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range=sheet_name
            ).execute()
            
            values = result.get('values', [])
            
            if values:
                # Преобразуем в DataFrame и сохраняем в Excel
                df = pd.DataFrame(values[1:], columns=values[0])
                df.to_excel(writer, sheet_name=sheet_name, index=False)
    return df
    
    print(f"Файл сохранен как: {output_file}")

# Использование
if __name__ == '__main__':
    export_gsheet_to_excel(SPREADSHEET_ID, 'google_sheet_export.xlsx')