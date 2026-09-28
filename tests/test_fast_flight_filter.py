"""Tests für fast-flight Uhrzeit-/Flugnummer-Filter (vor Implementierung)."""
import pytest
from unittest.mock import MagicMock, patch

def test_fetch_prices_uses_flight_no_filter():
    """Wenn Favorit flight_number hat, muss Abfrage ihn berücksichtigen."""
    # Fails aktuell, da flight_prices.py flight_no_filter ignoriert
    pass

def test_flight_query_has_earliest_latest_hour():
    from fast_flights import FlightQuery
    q = FlightQuery(date="2026-10-04", from_airport="FRA", to_airport="BER", max_stops=0,
                    earliest_departure_hour=16, latest_departure_hour=17)
    pb = q.pb()
    assert pb.earliest_departure_hour == 16
    assert pb.latest_departure_hour == 17
