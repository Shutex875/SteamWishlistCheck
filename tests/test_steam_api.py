import requests
from unittest.mock import patch
from src.steam_api import DEFAULT_TIMEOUT, fetch_wishlist, fetch_owned_games


@patch('src.steam_api.requests.get')
def test_fetch_owned_games_success(mock_get):
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {"response": {"games": [{"appid": 10}, {"appid": 20}]}}
    assert fetch_owned_games("123", "dummy_api_key") == {10, 20}
    mock_get.assert_called_once_with(
        "http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key=dummy_api_key&steamid=123&format=json",
        timeout=DEFAULT_TIMEOUT,
    )


@patch('src.steam_api.requests.get')
def test_fetch_owned_games_private(mock_get):
    mock_get.return_value.status_code = 403  # Private profile simulation
    mock_get.return_value.raise_for_status.side_effect = requests.HTTPError("403 Forbidden")
    assert fetch_owned_games("private_id", "dummy_api_key") == set()
    mock_get.assert_called_once_with(
        "http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key=dummy_api_key&steamid=private_id&format=json",
        timeout=DEFAULT_TIMEOUT,
    )


@patch('src.steam_api.requests.get')
def test_fetch_owned_games_exception(mock_get):
    mock_get.side_effect = requests.RequestException("Connection error")
    assert fetch_owned_games("123", "dummy_api_key") == set()
    mock_get.assert_called_once_with(
        "http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key=dummy_api_key&steamid=123&format=json",
        timeout=DEFAULT_TIMEOUT,
    )


@patch('src.steam_api.requests.get')
def test_fetch_owned_games_invalid_json(mock_get):
    mock_get.return_value.json.side_effect = ValueError("Invalid JSON")
    assert fetch_owned_games("123", "dummy_api_key") == set()
    mock_get.assert_called_once()


@patch('src.steam_api.requests.get')
def test_fetch_owned_games_empty_response(mock_get):
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {"response": {}}
    assert fetch_owned_games("123", "dummy_api_key") == set()
    mock_get.assert_called_once_with(
        "http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key=dummy_api_key&steamid=123&format=json",
        timeout=DEFAULT_TIMEOUT,
    )


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
    mock_get.assert_called_once_with(
        "https://store.steampowered.com/wishlist/profiles/123/wishlistdata/?p=0",
        timeout=DEFAULT_TIMEOUT,
    )


@patch('src.steam_api.requests.get')
def test_fetch_wishlist_private_or_error(mock_get):
    mock_get.return_value.status_code = 403
    mock_get.return_value.raise_for_status.side_effect = requests.HTTPError("403 Forbidden")
    assert fetch_wishlist("private_id") == []
    mock_get.assert_called_once_with(
        "https://store.steampowered.com/wishlist/profiles/private_id/wishlistdata/?p=0",
        timeout=DEFAULT_TIMEOUT,
    )


@patch('src.steam_api.requests.get')
def test_fetch_wishlist_network_exception(mock_get):
    mock_get.side_effect = requests.RequestException("Timeout")
    assert fetch_wishlist("123") == []
    mock_get.assert_called_once_with(
        "https://store.steampowered.com/wishlist/profiles/123/wishlistdata/?p=0",
        timeout=DEFAULT_TIMEOUT,
    )


@patch('src.steam_api.requests.get')
def test_fetch_wishlist_invalid_json(mock_get):
    mock_get.return_value.json.side_effect = ValueError("Invalid JSON")
    assert fetch_wishlist("123") == []
    mock_get.assert_called_once()


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
    mock_get.assert_called_once_with(
        "https://store.steampowered.com/wishlist/profiles/123/wishlistdata/?p=0",
        timeout=DEFAULT_TIMEOUT,
    )
