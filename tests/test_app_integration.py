def _read(path):
    with open(path) as f:
        return f.read()


def test_app_js_wires_decomposition():
    app = _read("frontend/src/App.js")
    # App is now a thin shell: it composes the per-tab components + hooks instead
    # of holding all state itself.
    for name in ["CollapsibleSidebar", "AirportsTab", "FlightsTab",
                 "TripsTab", "FavoriteTripPrices", "SettingsTab"]:
        assert f"import {name}" in app, f"App.js must import {name}"
    assert "from './hooks/useActiveTab'" in app
    assert "from './hooks/useAirports'" in app
    # Dead code from the refactor must stay out of App.
    assert "import Layout" not in app


def test_chartmodal_lives_with_favorites():
    # ChartModal moved into the Favorites tab component during the decomposition.
    fav = _read("frontend/src/components/FavoriteTripPrices.js")
    assert "import ChartModal" in fav
