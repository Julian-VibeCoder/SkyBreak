def test_fetch_flights():
    from skybreak.flight_scraper import fetch_flights
    result = fetch_flights("LHR")
    assert isinstance(result, (dict, list))
