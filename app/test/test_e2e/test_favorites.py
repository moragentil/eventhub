import re
from playwright.sync_api import expect
from app.test.test_e2e.base import BaseE2ETest
from django.contrib.auth import get_user_model
from app.models import Event, Venue
from datetime import timedelta
from django.utils import timezone

User = get_user_model()

class FavoriteE2ETest(BaseE2ETest):
    def setUp(self):
        super().setUp()
        self.user = User.objects.create_user(username="testuser", password="12345")
        self.venue = Venue.objects.create(name="Evento lleno", capacity=3)
        self.event = Event.objects.create(
            title="Evento lleno",
            description="Un evento de prueba",
            scheduled_at=timezone.now() + timedelta(days=5),
            organizer=self.user,
            price_general=50,
            price_vip=100,
            venue=self.venue
        )

    def test_mark_and_dismark_event_as_favorite(self):
        self.login_user("testuser", "12345")
        self.page.goto(f"{self.live_server_url}/events/")
        self.page.wait_for_selector("button.favorite-btn")
        favorite_button = self.page.locator("button.favorite-btn").first
        expect(favorite_button).to_have_class(re.compile(".*text-secondary.*"))
        favorite_button.click()
        expect(favorite_button).to_have_class(re.compile(".*text-primary.*"))
        favorite_button.click()
        expect(favorite_button).to_have_class(re.compile(".*text-secondary.*"))
