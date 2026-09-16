import requests
from unittest.mock import patch
from src.steam_api import fetch_wishlist, fetch_owned_games


@patch('src.steam_api.requests.get')
def test_fetch_owned_games_success(mock_get):
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {"response": {"games": [{"appid": 10}, {"appid": 20}]}}
    assert fetch_owned_games("123", "dummy_api_key") == {10, 20}


@patch('src.steam_api.requests.get')
def test_fetch_owned_games_private(mock_get):
    mock_get.return_value.status_code = 403  # Private profile simulation
    assert fetch_owned_games("private_id", "dummy_api_key") == set()


@patch('src.steam_api.requests.get')
def test_fetch_owned_games_exception(mock_get):
    mock_get.side_effect = requests.RequestException("Connection error")
    assert fetch_owned_games("123", "dummy_api_key") == set()


@patch('src.steam_api.requests.get')
def test_fetch_owned_games_empty_response(mock_get):
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {"response": {}}
    assert fetch_owned_games("123", "dummy_api_key") == set()


@patch('src.steam_api.requests.get')
def test_fetch_wishlist(mock_get):
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {
        "10": {"name": "Game A", "is_discounted": True, "subs": [{"discount_pct": 50, "price": 499}]}
    }
    wishlist = fetch_wishlist("123")
    assert len(wishlist) == 1
    assert wishlist[0]['appid'] == 10
    assert wishlist[0]['price_usd'] == 4.99
    assert wishlist[0]['discount_pct'] == 50
    assert wishlist[0]['name'] == "Game A"


@patch('src.steam_api.requests.get')
def test_fetch_wishlist_private_or_error(mock_get):
    mock_get.return_value.status_code = 403
    assert fetch_wishlist("private_id") == []


@patch('src.steam_api.requests.get')
def test_fetch_wishlist_network_exception(mock_get):
    mock_get.side_effect = requests.RequestException("Timeout")
    assert fetch_wishlist("123") == []


@patch('src.steam_api.requests.get')
def test_fetch_wishlist_skips_invalid_entries(mock_get):
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {
        "invalid_id": {"name": "Bad ID", "subs": [{"discount_pct": 10, "price": 1000}]},
        "20": {"name": "No Subs Game", "subs": []},
        "30": "not a dict",
        "40": {"name": "Valid Game", "subs": [{"discount_pct": 20, "price": 1999}]}
    }
    wishlist = fetch_wishlist("123")
    assert len(wishlist) == 1
    assert wishlist[0]['appid'] == 40
    assert wishlist[0]['name'] == "Valid Game"
    assert wishlist[0]['discount_pct'] == 20
    assert wishlist[0]['price_usd'] == 19.99
