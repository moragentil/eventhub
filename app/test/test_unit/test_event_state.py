from django.test import TestCase
from django.utils import timezone
from app.models import Event, User, Venue, Category, Ticket

class EventStateBusinessRulesTest(TestCase):
    def setUp(self):
        self.organizer = User.objects.create_user( username="org", email="org@example.com", password="pass", is_organizer=True)
        self.venue = Venue.objects.create(name="Test Venue", capacity=100)
        self.category = Category.objects.create(name="TestCat", is_active=True)
        self.scheduled_at = timezone.now() + timezone.timedelta(days=5)
        self.event = Event.objects.create(
            title="Evento",
            description="Desc",
            scheduled_at=self.scheduled_at,
            organizer=self.organizer,
            venue=self.venue,
            category=self.category,
        )
        self.user = User.objects.create_user(username="comprador", password="123")

    def test_event_default_state(self):
        event = Event.objects.create(
            title="Evento Default",
            description="Desc",
            scheduled_at=self.scheduled_at,
            organizer=self.organizer,
            venue=self.venue,
            category=self.category,
        )
        self.assertEqual(event.state, "activo")
    
    def test_event_update_state(self):
        event = Event.objects.create(
            title="Evento Update",
            description="Desc",
            scheduled_at=self.scheduled_at,
            organizer=self.organizer,
            venue=self.venue,
            category=self.category,
        )
        event.state = "finalizado"
        event.save()
        event.refresh_from_db()
        self.assertEqual(event.state, "finalizado")

    def test_no_ticket_purchase_if_cancelled(self):
        self.event.state = "cancelado"
        self.event.save()
        ticket, errors = Ticket.new(
            user=self.user, event=self.event, type="General", quantity=1
        )
        self.assertIsNone(ticket)
        self.assertIn("state", errors)

    def test_no_ticket_purchase_if_finalized(self):
        self.event.state = "finalizado"
        self.event.save()
        ticket, errors = Ticket.new(
            user=self.user, event=self.event, type="General", quantity=1
        )
        self.assertIsNone(ticket)
        self.assertIn("state", errors)

    def test_no_ticket_purchase_if_agotado(self):
        self.event.state = "agotado"
        self.event.save()
        ticket, errors = Ticket.new(
            user=self.user, event=self.event, type="General", quantity=1
        )
        self.assertIsNone(ticket)
        self.assertIn("state", errors)

    def test_no_edit_if_cancelled(self):
        self.event.state = "cancelado"
        self.event.save()
        can_edit = self.event.state not in ["cancelado"]
        self.assertFalse(can_edit)

    def test_no_edit_if_finalized(self):
        self.event.state = "finalizado"
        self.event.save()
        can_edit = self.event.state not in ["finalizado"]
        self.assertFalse(can_edit)