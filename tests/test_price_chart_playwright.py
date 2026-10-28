"""Playwright-Test: Preis-Chart-Button auf Favorit in Preise-Seite öffnet Chart mit 3 Kurven."""
import pytest

# Guard: if playwright is not installed, skip the whole file.
playwright = None
try:
    from playwright.sync_api import sync_playwright as _sp
    playwright = _sp
except ImportError:
    pass


pytestmark = pytest.mark.skipif(
    playwright is None,
    reason="Playwright not installed — install with `pip install playwright` and `playwright install`",
)


def _server_is_running(timeout: float = 1.0) -> bool:
    """Return True only if Flask (port 8088) is up."""
    import socket
    s = socket.socket()
    s.settimeout(timeout)
    try:
        s.connect(("localhost", 8088))
        return True
    except (ConnectionRefusedError, OSError):
        return False
    finally:
        s.close()


@pytest.mark.skipif(
    not _server_is_running(),
    reason="Flask server not running at localhost:8088",
)
def test_chart_button_opens_modal():
    with playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto("http://localhost:8088/", timeout=15_000)
        page.wait_for_selector("text=Prices", timeout=5000)
        try:
            page.click("text=Prices")
        except Exception:
            pass
        page.wait_for_selector("button:has-text('Chart')", timeout=8000)
        btn = page.locator("button:has-text('Chart')").first
        btn.click()
        overlay = page.locator("text=Preisverlauf")
        assert overlay.is_visible()
        svg = page.locator("svg")
        assert svg.count() > 0
        polylines = page.locator("polyline")
        assert polylines.count() >= 3
        browser.close()
