from django.contrib.auth import get_user_model
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.urls import reverse
from playwright.sync_api import sync_playwright
from app.models import Event, Ticket, TicketType, Venue
from datetime import timedelta
from django.utils import timezone

User = get_user_model()

class TicketCapacityE2ETest(StaticLiveServerTestCase):
    def setUp(self):
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

        Ticket.objects.create(event=self.event, quantity=2, type=TicketType.GENERAL, user=self.user)
        Ticket.objects.create(event=self.event, quantity=1, type=TicketType.VIP, user=self.user)

        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=True)
        self.context = self.browser.new_context()
        self.page = self.context.new_page()

    def tearDown(self):
        self.context.close()
        self.browser.close()
        self.playwright.stop()

    def login(self):
        login_url = f"{self.live_server_url}/accounts/login/"
        self.page.goto(login_url)
        self.page.fill("input[name='username']", "testuser")
        self.page.fill("input[name='password']", "12345")
        self.page.click("button[type='submit']")
        self.page.wait_for_url(f"{self.live_server_url}/")

    def test_user_cannot_buy_ticket_when_event_is_full(self):
        self.login()

        url = self.live_server_url + reverse("ticket_create", args=[self.event.pk])
        self.page.goto(url)

        self.page.fill("input#quantity", "1")
        self.page.select_option("select#type", "General") 

        self.page.click("button:has-text('Comprar')")

        self.page.wait_for_selector("text=Ya se vendieron todas las entradas")

        assert self.page.locator("div.alert-danger").is_visible()
        assert self.page.locator("button:has-text('Comprar')").is_visible()
