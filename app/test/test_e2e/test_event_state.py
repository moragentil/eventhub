import datetime
from django.urls import reverse
from django.utils import timezone
from playwright.sync_api import expect

from app.models import User, Event, Venue, Category, Ticket, TicketType
from app.test.test_e2e.base import BaseE2ETest

class EventStateE2ETest(BaseE2ETest):
    def setUp(self):
        super().setUp()
        self.organizer = User.objects.create_user(username="event_state_org", email="event_state_org@example.com", password="password123", is_organizer=True,)
        self.user = User.objects.create_user(username="event_state_user", email="event_state_user@example.com", password="password123", is_organizer=False,)
        self.venue = Venue.objects.create(name="Event State Venue", address="123 Main St", city="Testville", capacity=100)
        self.category = Category.objects.create(name="Event State Category", is_active=True)
        
        self.event = Event.objects.create(
            title="Event State Test Event",
            description="An event to test states.",
            scheduled_at=timezone.now() + datetime.timedelta(days=7),
            organizer=self.organizer,
            venue=self.venue,
            category=self.category,
            price_general=10,
        )

    def test_user_cannot_buy_ticket_for_cancelled_event(self):
        self.event.state = "cancelado"
        self.event.save()

        self.login_user(self.user.username, "password123")
        
        ticket_create_url = self.live_server_url + reverse("ticket_create", args=[self.event.pk])
        self.page.goto(ticket_create_url)
        
        error_message_area = self.page.locator("div.alert.alert-error")
        expect(error_message_area).to_be_visible(timeout=5000)
        expect(error_message_area).to_contain_text("No se pueden comprar entradas para este evento porque esta cancelado.")
        
        self.assertEqual(Ticket.objects.filter(event=self.event, user=self.user).count(), 0)

    def test_user_cannot_buy_ticket_for_finalized_event(self):
        self.event.state = "finalizado"
        self.event.save()

        self.login_user(self.user.username, "password123")
        
        ticket_create_url = self.live_server_url + reverse("ticket_create", args=[self.event.pk])
        self.page.goto(ticket_create_url)
        
        error_message_area = self.page.locator("div.alert.alert-error")
        expect(error_message_area).to_be_visible(timeout=5000)
        expect(error_message_area).to_contain_text("No se pueden comprar entradas para este evento porque esta finalizado.")
        
        self.assertEqual(Ticket.objects.filter(event=self.event, user=self.user).count(), 0)

    def test_user_cannot_buy_ticket_for_sold_out_event(self):
        sold_out_venue = Venue.objects.create(name="Sold Out Venue E2E", capacity=1)
        sold_out_event = Event.objects.create(
            title="Sold Out Event E2E",
            description="This event will be sold out for E2E test.",
            scheduled_at=timezone.now() + datetime.timedelta(days=3),
            organizer=self.organizer,
            venue=sold_out_venue,
            category=self.category,
            price_general=5,
        )
        buyer = User.objects.create_user(username="ticketbuyer_e2e", email="tb_e2e@example.com", password="password123")
        Ticket.objects.create(event=sold_out_event, user=buyer, quantity=1, type=TicketType.GENERAL)
        sold_out_event.state = "agotado" 
        sold_out_event.save()

        self.login_user(self.user.username, "password123")
        
        ticket_create_url = self.live_server_url + reverse("ticket_create", args=[sold_out_event.pk])
        self.page.goto(ticket_create_url)
        
        error_message_area = self.page.locator("div.alert.alert-error")
        expect(error_message_area).to_be_visible(timeout=5000)
        expect(error_message_area).to_contain_text("No se pueden comprar entradas para este evento porque esta agotado.")
        
        self.assertEqual(Ticket.objects.filter(event=sold_out_event, user=self.user).count(), 0)

    def test_organizer_cannot_edit_cancelled_event(self):
        self.event.state = "cancelado"
        self.event.save()

        self.login_user(self.organizer.username, "password123")

        event_edit_url = self.live_server_url + reverse("event_edit", args=[self.event.pk])
        self.page.goto(event_edit_url)

        expect(self.page).to_have_url(self.live_server_url + reverse("events"), timeout=5000)
        django_message = self.page.locator("div.alert.alert-error")
        expect(django_message).to_be_visible(timeout=5000)
        expect(django_message).to_contain_text("cancelado") 
        expect(django_message).to_contain_text("No se pueden editar eventos cancelados.")

    def test_organizer_cannot_edit_finalized_event(self):
        self.event.state = "finalizado"
        self.event.save()

        self.login_user(self.organizer.username, "password123")

        event_edit_url = self.live_server_url + reverse("event_edit", args=[self.event.pk])
        self.page.goto(event_edit_url)
        
        expect(self.page).to_have_url(self.live_server_url + reverse("events"), timeout=5000)
        
        django_message = self.page.locator("div.alert.alert-error")
        expect(django_message).to_be_visible(timeout=5000)
        expect(django_message).to_contain_text("finalizado")
        expect(django_message).to_contain_text("No se pueden editar eventos finalizados.")