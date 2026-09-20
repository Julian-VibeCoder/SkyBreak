def test_scrape_all_airports():
    from skybreak.scraper_job import scrape_all_airports
    # Sollte ohne Exception laufen
    scrape_all_airports()
