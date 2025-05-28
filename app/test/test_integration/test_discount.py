from django.test import TestCase
from decimal import Decimal
import datetime
from django.utils import timezone
from app.models import User, Venue, Category, Event, Ticket, Discount

class TicketDiscountIntegrationTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="1234")
        self.venue = Venue.objects.create(name="Estadio", address="Calle 123", city="La Plata", capacity=1000)
        self.category = Category.objects.create(name="Concierto", description="Conciertos en vivo")
        self.discount = Discount.objects.create(code="SALE10", percentage=10)
        self.event = Event.objects.create(
            title="Rock Nacional",
            description="Festival de Rock",
            scheduled_at=timezone.make_aware(datetime.datetime(2030, 1, 1, 20, 0)),
            organizer=self.user,
            price_general=Decimal("100.00"),
            price_vip=Decimal("200.00"),
            venue=self.venue,
            category=self.category,
            discount=self.discount
        )

    def test_ticket_creation_with_discount(self):
        ticket, errors = Ticket.new(quantity=1, type="General", user=self.user, event=self.event)
        self.assertIsNotNone(ticket)
        self.assertEqual(errors, {})
        self.assertEqual(ticket.quantity, 1)
        self.assertEqual(ticket.event.discount.code, "SALE10")
