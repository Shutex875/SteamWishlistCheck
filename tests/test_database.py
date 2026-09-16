import os
import pytest
from src.database import (
    setup_db,
    update_last_notified,
    get_last_notified,
    set_rejected_price,
    get_rejected_price,
    clear_expired_sales,
    get_all_game_states,
)


@pytest.fixture
def db_path(tmp_path):
    path = str(tmp_path / "test.db")
    setup_db(path)
    return path


def test_database_operations(db_path):
    # Test last_notified
    update_last_notified(db_path, 123, 4.99)
    assert get_last_notified(db_path, 123) == 4.99

    # Test rejected_price
    set_rejected_price(db_path, 123, 4.99)
    assert get_rejected_price(db_path, 123) == 4.99

    # Test clear expired sales
    clear_expired_sales(db_path, [456])  # 123 is no longer discounted
    assert get_last_notified(db_path, 123) is None
    # rejected_price should NOT be cleared by clear_expired_sales!
    assert get_rejected_price(db_path, 123) == 4.99


def test_clear_expired_sales_empty_list(db_path):
    update_last_notified(db_path, 100, 9.99)
    update_last_notified(db_path, 200, 19.99)
    set_rejected_price(db_path, 100, 9.99)

    clear_expired_sales(db_path, [])
    assert get_last_notified(db_path, 100) is None
    assert get_last_notified(db_path, 200) is None
    assert get_rejected_price(db_path, 100) == 9.99


def test_non_existent_app_id(db_path):
    assert get_last_notified(db_path, 999) is None
    assert get_rejected_price(db_path, 999) is None


def test_connection_closed_allows_file_removal(tmp_path):
    # On Windows, open SQLite handles lock the file and prevent deletion
    path = str(tmp_path / "lock_test.db")
    setup_db(path)
    update_last_notified(path, 1, 9.99)
    get_last_notified(path, 1)
    set_rejected_price(path, 1, 9.99)
    get_rejected_price(path, 1)
    clear_expired_sales(path, [1])
    
    # Should not raise PermissionError
    os.remove(path)
    assert not os.path.exists(path)


def test_get_all_game_states(db_path):
    # Empty initially
    assert get_all_game_states(db_path) == {}

    update_last_notified(db_path, 1, 4.99)
    set_rejected_price(db_path, 2, 9.99)
    update_last_notified(db_path, 3, 2.99)
    set_rejected_price(db_path, 3, 5.99)

    states = get_all_game_states(db_path)
    assert states == {
        1: {'last_notified_price': 4.99, 'rejected_price': None},
        2: {'last_notified_price': None, 'rejected_price': 9.99},
        3: {'last_notified_price': 2.99, 'rejected_price': 5.99},
    }

