from playwright.sync_api import sync_playwright
import pytest

@pytest.mark.e2e
def test_event_list_hides_past_events():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto("http://localhost:8000/accounts/login/")
        page.fill("input[name='username']", "test")
        page.fill("input[name='password']", "1234")
        page.click("text=Ingresar")
        page.goto("http://localhost:8000/events/")
        assert "Evento Futuro" in page.content()
        assert "Evento Pasado" not in page.content()
        browser.close()
