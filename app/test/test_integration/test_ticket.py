from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from app.models import Event, Ticket, TicketType, Venue
from datetime import timedelta
from django.utils import timezone

User = get_user_model()

class TicketCapacityIntegrationTest(TestCase):
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

    def test_no_ticket_created_when_event_is_full(self):
        self.client.login(username="testuser", password="12345")
        response = self.client.post(
            reverse("ticket_create", args=[self.event.pk]),
            {
                "quantity": 1,
                "type": TicketType.GENERAL
            },
            follow=True,
        )

        self.assertContains(response, "Ya se vendieron todas las entradas para este evento.")
        self.assertEqual(Ticket.objects.filter(event=self.event).count(), 2)  
        self.assertEqual(
            sum(t.quantity for t in Ticket.objects.filter(event=self.event)),
            self.venue.capacity
        )


class TicketLimitPerUserIntegrationTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="12345")
        self.venue = Venue.objects.create(name="Venue", capacity=100)
        self.event = Event.objects.create(
            title="Evento con límite por usuario",
            description="Un evento de prueba",
            scheduled_at=timezone.now() + timedelta(days=5),
            organizer=self.user,
            price_general=50,
            price_vip=100,
            venue=self.venue
        )

        Ticket.objects.create(event=self.event, quantity=2, type=TicketType.GENERAL, user=self.user)
        Ticket.objects.create(event=self.event, quantity=2, type=TicketType.VIP, user=self.user)

    def test_user_cannot_exceed_ticket_limit_per_event(self):
        self.client.login(username="testuser", password="12345")

        response = self.client.post(
            reverse("ticket_create", args=[self.event.pk]),
            {
                "quantity": 1,
                "type": TicketType.GENERAL
            },
            follow=True,
        )

        self.assertContains(response, "No puedes comprar más de 4 entradas para este evento.")
        self.assertEqual(Ticket.objects.filter(event=self.event, user=self.user).count(), 2)
        self.assertEqual(
            sum(t.quantity for t in Ticket.objects.filter(event=self.event, user=self.user)), 4)