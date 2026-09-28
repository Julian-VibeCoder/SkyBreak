"""Playwright-Test: Preis-Chart-Button auf Favorit in Preise-Seite öffnet Chart mit 3 Kurven."""
from playwright.sync_api import sync_playwright

def test_chart_button_opens_modal():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto("http://localhost:8088/")
        page.wait_for_selector("text=Prices", timeout=5000)
        try:
            page.click("text=Prices")
        except:
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
