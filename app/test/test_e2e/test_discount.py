import datetime
import re

from django.utils import timezone
from playwright.sync_api import expect

from app.models import Category, Event, User, Venue, Discount
from app.test.test_e2e.base import BaseE2ETest

class DiscountE2ETest(BaseE2ETest):
    def setUp(self):
        super().setUp()

        self.user = User.objects.create_user(
            username="usuario",
            email="user@example.com",
            password="123",
            is_organizer=False,
        )

        self.category = Category.objects.create(name="Concierto", description="Música")
        self.venue = Venue.objects.create(
            name="Auditorio",
            address="Calle 1",
            city="Ciudad",
            capacity=200
        )
        self.discount = Discount.objects.create(
            code="DESCUENTO20",
            percentage=20
        )
        self.event = Event.objects.create(
            title="Festival",
            description="Evento musical",
            scheduled_at=timezone.make_aware(datetime.datetime(2025, 6, 10, 20, 0)),
            organizer=self.user,
            price_general=100.00,
            price_vip=150.00,
            category=self.category,
            venue=self.venue,
            discount=self.discount
        )

    def test_user_can_apply_discount_when_buying_ticket(self):
        self.login_user("usuario", "123")
        self.page.goto(f"{self.live_server_url}/events/{self.event.pk}/tickets/create/")
        self.page.wait_for_selector('input[name="quantity"]')
        self.page.fill('input[name="quantity"]', "1")
        self.page.select_option('select[name="type"]', "General")
        self.page.fill('input[name="discount_code"]', "DESCUENTO20")
        self.page.get_by_role("button", name="Comprar").click()
        expect(self.page.locator(".alert-success")).to_be_visible()
        expect(self.page.locator(".alert-success")).to_contain_text("¡Compra realizada!")
        expect(self.page.locator(".alert-success")).to_contain_text("Total pagado:")
        expect(self.page.locator(".alert-success")).to_contain_text(re.compile(r"\$80[,.]00"))


        
        