from django.test import TestCase
from django.contrib.auth import get_user_model
from app.models import Event, Ticket, Venue, TicketType
from datetime import timedelta
from django.utils import timezone

User = get_user_model()

class TicketCapacityUnitTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='12345')
        
        self.venue = Venue.objects.create(name="Test Venue", capacity=100)
        
        self.event = Event.objects.create(
            title="Test Event",
            venue=self.venue,
            scheduled_at=timezone.now() + timedelta(days=10),  
            organizer=self.user  
        )

    def test_no_ticket_created_when_event_is_full(self):
        Ticket.objects.create(user=self.user, event=self.event, quantity=100)

        ticket, errors = Ticket.new(
            user=self.user,
            event=self.event,
            type=TicketType.GENERAL,
            quantity=1
        )

        self.assertIsNone(ticket)
        self.assertIsNotNone(errors)
        self.assertIn("general", errors)
        self.assertEqual(errors["general"], "Ya se vendieron todas las entradas para este evento.")


class TicketLimitPerUserUnitTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.venue = Venue.objects.create(name="Test Venue", capacity=100)
        self.event = Event.objects.create(
            title="Evento con límite por usuario",
            venue=self.venue,
            scheduled_at=timezone.now() + timedelta(days=10),
            organizer=self.user
        )

        Ticket.objects.create(user=self.user, event=self.event, quantity=4, type=TicketType.GENERAL)

    def test_user_cannot_exceed_ticket_limit_per_event(self):
        ticket, errors = Ticket.new(
            user=self.user,
            event=self.event,
            type=TicketType.GENERAL,
            quantity=1
        )

        self.assertIsNone(ticket)
        self.assertIsNotNone(errors)
        self.assertIn("quantity", errors)
        self.assertEqual(errors["quantity"], "No puedes comprar más de 4 entradas para este evento.")

