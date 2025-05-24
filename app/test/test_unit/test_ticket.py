from django.test import TestCase
from django.contrib.auth import get_user_model
from app.models import Event, Ticket, Venue, TicketType
from datetime import timedelta
from django.utils import timezone

User = get_user_model()

class TicketTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='12345')
        
        self.venue = Venue.objects.create(name="Test Venue", capacity=100)
        
        self.event = Event.objects.create(
            title="Test Event",
            venue=self.venue,
            scheduled_at=timezone.now() + timedelta(days=10),  
            organizer=self.user  
        )

    def test_cannot_sell_more_tickets_than_capacity(self):
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
