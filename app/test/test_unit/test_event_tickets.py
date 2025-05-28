from django.test import TestCase
from app.models import Event, Venue, Ticket, TicketType, User
from django.utils import timezone
from decimal import Decimal
from django.db.models import Sum

class EventDetailLogicTest(TestCase):
    def setUp(self):
        self.organizer = User.objects.create_user(username="organizer", password="123", is_organizer=True)
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

    def test_no_tickets_sold(self):
        tickets_sold = Ticket.objects.filter(event=self.event).aggregate(total=Sum("quantity"))["total"] or 0
        self.assertEqual(tickets_sold, 0)

    def test_high_demand_message(self):
        Ticket.objects.create(event=self.event, quantity=95, type=TicketType.GENERAL, user=self.organizer)
        tickets_sold = Ticket.objects.filter(event=self.event).aggregate(total=Sum("quantity"))["total"] or 0
        occupancy_rate = (tickets_sold / self.venue.capacity) * 100
        self.assertGreater(occupancy_rate, 90)

    def test_low_demand_message(self):
        Ticket.objects.create(event=self.event, quantity=5, type=TicketType.GENERAL, user=self.organizer)
        tickets_sold = Ticket.objects.filter(event=self.event).aggregate(total=Sum("quantity"))["total"] or 0
        occupancy_rate = (tickets_sold / self.venue.capacity) * 100
        self.assertLess(occupancy_rate, 10)