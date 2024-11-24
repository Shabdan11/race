import sqlite3
import logging

def create_states():
    try:
        with sqlite3.connect('example.db') as conn:
            cursor = conn.cursor()
            cursor.execute('''CREATE TABLE IF NOT EXISTS user_states(
                                user_id INTEGER PRIMARY KEY,
                                state TEXT NOT NULL,
                                role
                              );''')
            conn.commit()

    except sqlite3.DatabaseError as e:
        logging.error(f"Database error: {e}")




