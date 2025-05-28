from playwright.sync_api import expect
from app.models import Event, Venue, Ticket, TicketType, User
from app.test.test_e2e.base import BaseE2ETest
from django.utils import timezone
from decimal import Decimal

class EventDetailE2ETest(BaseE2ETest):
    def setUp(self):
        super().setUp()
        self.organizer = User.objects.create_user(username="organizer", password="123", is_organizer=True)
        self.venue = Venue.objects.create(name="Test Venue", capacity=100)
        self.event = Event.objects.create(
            title="Test Event",
            description="Test Description",
            scheduled_at=timezone.now() + timezone.timedelta(days=1),
            organizer=self.organizer,
            venue=self.venue,
            price_general=Decimal("50.00"),
            price_vip=Decimal("100.00"),
        )
        Ticket.objects.create(event=self.event, quantity=95, type=TicketType.GENERAL, user=self.organizer)

    def test_event_detail_high_demand(self):
        self.login_user("organizer", "123")
        self.page.goto(f"{self.live_server_url}/events/{self.event.id}/")
        expect(self.page.get_by_text("95 de 100")).to_be_visible()
        expect(self.page.get_by_text("Alta demanda (más del 90% de la ocupación)")).to_be_visible()