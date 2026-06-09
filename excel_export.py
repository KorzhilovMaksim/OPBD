import pandas as pd
from db import execute_query

def export_table_to_excel(table_name, filename):
    data = execute_query(f"SELECT * FROM {table_name}", fetch_all=True)
    if not data:
        raise Exception(f"Таблица {table_name} пуста, нечего экспортировать")
    df = pd.DataFrame(data)
    df.to_excel(filename, index=False)