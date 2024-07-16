import sqlite3

def create_tables():
    conn = sqlite3.connect('forex_data.db')
    cursor = conn.cursor()

    # Create tables for daily, monthly, and yearly data
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS daily_data (
            id INTEGER PRIMARY KEY,
            instrument TEXT,
            time TEXT,
            open REAL,
            high REAL,
            low REAL,
            close REAL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS monthly_data (
            id INTEGER PRIMARY KEY,
            instrument TEXT,
            time TEXT,
            open REAL,
            high REAL,
            low REAL,
            close REAL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS yearly_data (
            id INTEGER PRIMARY KEY,
            instrument TEXT,
            time TEXT,
            open REAL,
            high REAL,
            low REAL,
            close REAL
        )
    ''')

    conn.commit()
    conn.close()

create_tables()
