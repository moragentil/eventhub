import datetime
from django.utils import timezone
from playwright.sync_api import expect
from app.models import Event, User
from app.test.test_e2e.base import BaseE2ETest

class EventFilterE2ETest(BaseE2ETest):
    def setUp(self):
        super().setUp()
        # Crear usuario de prueba
        self.user = self.create_test_user()
        # Crear evento pasado
        past_date = timezone.make_aware(datetime.datetime(2020, 1, 1, 20, 0))
        self.past_event = Event.objects.create(
            title="Evento Pasado",
            description="Un evento que ya ocurrió",
            scheduled_at=past_date,
            organizer=self.user,
        )
        # Crear evento futuro
        future_date = timezone.make_aware(datetime.datetime(2030, 1, 1, 20, 0))
        self.future_event = Event.objects.create(
            title="Evento Futuro",
            description="Un evento que ocurrirá",
            scheduled_at=future_date,
            organizer=self.user,
        )

    def test_event_list_hides_past_events(self):
        # Login usando el método auxiliar
        self.login_user(self.user.username, "password123")
        self.page.goto(f"{self.live_server_url}/events/")
        self.page.screenshot(path="test_event_filter.png", full_page=True)
        # Verifica que el evento futuro aparece
        expect(self.page.get_by_text("Evento Futuro")).to_be_visible()
        # Verifica que el evento pasado NO aparece
        self.page.screenshot(path="test_event_filter.png", full_page=True)
        expect(self.page.get_by_text("Evento Pasado")).to_have_count(0)
