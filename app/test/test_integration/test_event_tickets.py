from django.test import TestCase
from django.urls import reverse
from app.models import Event, Venue, Ticket, TicketType, User
from django.utils import timezone
from decimal import Decimal

class EventDetailIntegrationTest(TestCase):
    def setUp(self):
        self.organizer = User.objects.create_user(username="organizer", password="123", is_organizer=True)
        self.client.login(username="organizer", password="123")
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

    def test_event_detail_high_demand(self):
        Ticket.objects.create(event=self.event, quantity=95, type=TicketType.GENERAL, user=self.organizer)
        response = self.client.get(reverse("event_detail", args=[self.event.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "95 de 100")
        self.assertContains(response, "Alta demanda (más del 90% de la ocupación)")

    def test_event_detail_low_demand(self):
        Ticket.objects.create(event=self.event, quantity=5, type=TicketType.GENERAL, user=self.organizer)
        response = self.client.get(reverse("event_detail", args=[self.event.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "5 de 100")
        self.assertContains(response, "Baja demanda (menos del 10% de la ocupación)")