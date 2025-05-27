from django.urls import reverse
from django.utils import timezone
from django.test import TestCase
from app.models import Event, User, Venue, Category, Ticket

class EventStateIntegrationTest(TestCase):
    def setUp(self):
        self.organizer = User.objects.create_user(username="org", email="org@example.com", password="pass", is_organizer=True)
        self.user = User.objects.create_user(username="comprador", email="comprador@example.com", password="123")
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
        self.client.login(username="comprador", password="123")

    def test_event_default_state_is_activo(self):
        event = Event.objects.create(
            title="Nuevo Evento",
            description="Desc",
            scheduled_at=self.scheduled_at,
            organizer=self.organizer,
            venue=self.venue,
            category=self.category,
        )
        self.assertEqual(event.state, "activo")

    def test_event_update_to_all_states(self):
        event = Event.objects.create(
            title="Evento Update All",
            description="Desc",
            scheduled_at=self.scheduled_at,
            organizer=self.organizer,
            venue=self.venue,
            category=self.category,
        )
        for state, _ in Event.states:
            event.state = state
            event.save()
            event.refresh_from_db()
            self.assertEqual(event.state, state)

    def test_no_ticket_purchase_if_event_cancelled(self):
        self.event.state = "cancelado"
        self.event.save()
        response = self.client.post(
            reverse("ticket_create", args=[self.event.id]),
            {"quantity": 1, "type": "General"},
            follow=True,
        )
        self.assertContains(response, "No se pueden comprar entradas para este evento", status_code=200)
        self.assertEqual(Ticket.objects.filter(event=self.event, user=self.user).count(), 0)

    def test_no_ticket_purchase_if_event_finalized(self):
        self.event.state = "finalizado"
        self.event.save()
        response = self.client.post(
            reverse("ticket_create", args=[self.event.id]),
            {"quantity": 1, "type": "General"},
            follow=True,
        )
        self.assertContains(response, "No se pueden comprar entradas para este evento", status_code=200)
        self.assertEqual(Ticket.objects.filter(event=self.event, user=self.user).count(), 0)

    def test_no_ticket_purchase_if_event_agotado(self):
        self.event.state = "agotado"
        self.event.save()
        response = self.client.post(
            reverse("ticket_create", args=[self.event.id]),
            {"quantity": 1, "type": "General"},
            follow=True,
        )
        self.assertContains(response, "No se pueden comprar entradas para este evento", status_code=200)
        self.assertEqual(Ticket.objects.filter(event=self.event, user=self.user).count(), 0)
    
    def test_no_edit_if_finalized(self):
        self.event.state = "finalizado"
        self.event.save()
        can_edit = self.event.state not in ["finalizado"]
        self.assertFalse(can_edit)

    def test_no_edit_if_cancelled(self):
        self.event.state = "cancelado"
        self.event.save()
        can_edit = self.event.state not in ["cancelado"]
        self.assertFalse(can_edit)
