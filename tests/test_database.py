import sqlite3
import os
from src.database import setup_db, update_last_notified, get_last_notified, set_rejected_price, get_rejected_price, clear_expired_sales

def test_database_operations(tmp_path):
    db_path = str(tmp_path / "test.db")
    setup_db(db_path)
    
    # Test last_notified
    update_last_notified(db_path, 123, 4.99)
    assert get_last_notified(db_path, 123) == 4.99
    
    # Test rejected_price
    set_rejected_price(db_path, 123, 4.99)
    assert get_rejected_price(db_path, 123) == 4.99
    
    # Test clear expired sales
    clear_expired_sales(db_path, [456]) # 123 is no longer discounted
    assert get_last_notified(db_path, 123) is None
    # rejected_price should NOT be cleared by clear_expired_sales!
    assert get_rejected_price(db_path, 123) == 4.99


def test_clear_expired_sales_empty_list(tmp_path):
    db_path = str(tmp_path / "test.db")
    setup_db(db_path)
    
    update_last_notified(db_path, 100, 9.99)
    update_last_notified(db_path, 200, 19.99)
    set_rejected_price(db_path, 100, 9.99)
    
    clear_expired_sales(db_path, [])
    assert get_last_notified(db_path, 100) is None
    assert get_last_notified(db_path, 200) is None
    assert get_rejected_price(db_path, 100) == 9.99


def test_non_existent_app_id(tmp_path):
    db_path = str(tmp_path / "test.db")
    setup_db(db_path)
    
    assert get_last_notified(db_path, 999) is None
    assert get_rejected_price(db_path, 999) is None
