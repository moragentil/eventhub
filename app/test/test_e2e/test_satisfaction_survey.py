import datetime

from django.utils import timezone
from playwright.sync_api import expect

from app.models import Category, Event, User, Venue
from app.test.test_e2e.base import BaseE2ETest


class SatisfactionSurveyE2ETest(BaseE2ETest):
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
        self.event = Event.objects.create(
            title="Festival",
            description="Evento musical",
            scheduled_at=timezone.make_aware(datetime.datetime(2025, 6, 10, 20, 0)),
            organizer=self.user,
            price_general=100.00,
            price_vip=150.00,
            category=self.category,
            venue=self.venue
        )

    def test_user_can_submit_survey_after_ticket_purchase(self):
        self.login_user("usuario", "123")
        self.page.goto(f"{self.live_server_url}/events/{self.event.pk}/tickets/create/")
        self.page.wait_for_selector('input[name="quantity"]')
        self.page.fill('input[name="quantity"]', "1")
        self.page.select_option('select[name="type"]', "General")
        self.page.get_by_role("button", name="Comprar").click()
        expect(self.page.locator("#surveyPromptModal")).to_be_visible()
        self.page.get_by_role("link", name="Sí, completar encuesta").click()
        form = self.page.locator("form:has-text('¿Qué tan cómodo fue el proceso de compra?')")
        expect(form).to_be_visible()
        self.page.click("label[for='comfort_5']")
        self.page.click("label[for='clarity_5']")
        self.page.click("label[for='satisfaction_5']")
        self.page.fill('textarea[name="comment"]', "Excelente todo")
        self.page.get_by_role("button", name="Enviar").click()
        expect(self.page).to_have_url(f"{self.live_server_url}/events/")