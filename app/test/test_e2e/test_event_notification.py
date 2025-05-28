import datetime
from django.utils import timezone
from app.models import Event, User, Venue, Category, Ticket, TicketType
from app.test.test_e2e.base import BaseE2ETest
from playwright.sync_api import expect

class EventNotificationE2ETest(BaseE2ETest):
    def setUp(self):
        super().setUp()
        self.organizer = User.objects.create_user(username="organizador_e2e", email="organizador_e2e@example.com", password="password123", is_organizer=True)
        self.regular_user = User.objects.create_user(username="usuario_e2e", email="usuario_e2e@example.com", password="password123", is_organizer=False)
        self.venue1 = Venue.objects.create(name="Venue E2E 1", address="Calle 1", city="Ciudad", capacity=100)
        self.venue2 = Venue.objects.create(name="Venue E2E 2", address="Calle 2", city="Ciudad", capacity=200)
        self.category = Category.objects.create(name="Categoria E2E", description="desc", is_active=True)
        self.event = Event.objects.create(
            title="Evento E2E",
            description="desc",
            scheduled_at=timezone.now() + datetime.timedelta(days=2),
            organizer=self.organizer,
            price_general=50,
            price_vip=100,
            venue=self.venue1,
            category=self.category,
        )
        Ticket.objects.create(event=self.event, quantity=1, type=TicketType.GENERAL, user=self.regular_user)

    def test_notification_on_event_edit(self):
        self.login_user("organizador_e2e", "password123")
        self.page.goto(f"{self.live_server_url}/events/{self.event.id}/edit/")
        new_date = (self.event.scheduled_at + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        new_time = (self.event.scheduled_at + datetime.timedelta(days=1)).strftime("%H:%M")
        self.page.get_by_label("Precio General").fill("50")
        self.page.get_by_label("Precio VIP").fill("100")
        self.page.get_by_label("Fecha").fill(new_date)
        self.page.get_by_label("Hora").fill(new_time)
        self.page.get_by_role("button", name="Actualizar Evento").click()
        expect(self.page).to_have_url(f"{self.live_server_url}/events/")

        self.page.get_by_role("button", name="Salir").click()
        self.login_user("usuario_e2e", "password123")
        self.page.goto(f"{self.live_server_url}/notifications/")

        expect(self.page.get_by_text("Evento E2E", exact=True)).to_be_visible()
        expect(self.page.get_by_text("Fecha antigua:")).to_be_visible()
        expect(self.page.get_by_text("Fecha actualizada:")).to_be_visible()