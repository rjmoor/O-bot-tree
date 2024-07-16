import sqlite3
import pandas as pd

class SQLiteDatabase:
    def __init__(self, db_name):
        self.conn = sqlite3.connect(db_name)

    def store_data(self, df, table_name):
        df.to_sql(table_name, self.conn, if_exists='append', index=False)

    def get_data(self, table_name):
        return pd.read_sql(f'SELECT * FROM {table_name}', self.conn)

# Usage Example
db = SQLiteDatabase()
df = pd.DataFrame({
    'instrument': ['EUR_USD'] * 5,
    'time': ['2023-01-01', '2023-01-02', '2023-01-03', '2023-01-04', '2023-01-05'],
    'open': [1.1, 1.2, 1.3, 1.4, 1.5],
    'high': [1.2, 1.3, 1.4, 1.5, 1.6],
    'low': [1.0, 1.1, 1.2, 1.3, 1.4],
    'close': [1.15, 1.25, 1.35, 1.45, 1.55]
})
db.store_data(df, 'daily_data')
print(db.get_data('daily_data'))
