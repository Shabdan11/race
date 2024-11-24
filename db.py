import sqlite3
import logging

logging = logging.basicConfig(level=logging.INFO)


def create_tables():
    try:
        with sqlite3.connect('example.db') as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS players(
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    phone TEXT NOT NULL,
                    car TEXT NOT NULL
                )
            ''')

            conn.commit()

    except sqlite3.Error as e:
        logging.error(f"Error creating tables: {e}")

def create_playing_table():
    try:
        with sqlite3.connect('example.db') as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS playing (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    car TEXT NOT NULL
                )
            ''')
            conn.commit()
    except sqlite3.DatabaseError as e:
        logging.error(f"Database error during table creation: {e}")
