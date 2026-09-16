import sqlite3

def get_connection(db_path: str):
    return sqlite3.connect(db_path)

def setup_db(db_path: str):
    with get_connection(db_path) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS game_states (
                app_id INTEGER PRIMARY KEY,
                last_notified_price REAL,
                rejected_price REAL
            )
        """)

def update_last_notified(db_path: str, app_id: int, price: float):
    with get_connection(db_path) as conn:
        conn.execute("""
            INSERT INTO game_states (app_id, last_notified_price)
            VALUES (?, ?)
            ON CONFLICT(app_id) DO UPDATE SET last_notified_price = ?
        """, (app_id, price, price))

def get_last_notified(db_path: str, app_id: int) -> float | None:
    with get_connection(db_path) as conn:
        cursor = conn.execute("SELECT last_notified_price FROM game_states WHERE app_id = ?", (app_id,))
        row = cursor.fetchone()
        return row[0] if row else None

def set_rejected_price(db_path: str, app_id: int, price: float):
    with get_connection(db_path) as conn:
        conn.execute("""
            INSERT INTO game_states (app_id, rejected_price)
            VALUES (?, ?)
            ON CONFLICT(app_id) DO UPDATE SET rejected_price = ?
        """, (app_id, price, price))

def get_rejected_price(db_path: str, app_id: int) -> float | None:
    with get_connection(db_path) as conn:
        cursor = conn.execute("SELECT rejected_price FROM game_states WHERE app_id = ?", (app_id,))
        row = cursor.fetchone()
        return row[0] if row else None

def clear_expired_sales(db_path: str, current_discounted_app_ids: list[int]):
    with get_connection(db_path) as conn:
        if not current_discounted_app_ids:
            conn.execute("UPDATE game_states SET last_notified_price = NULL")
        else:
            placeholders = ",".join("?" for _ in current_discounted_app_ids)
            conn.execute(f"UPDATE game_states SET last_notified_price = NULL WHERE app_id NOT IN ({placeholders})", current_discounted_app_ids)
