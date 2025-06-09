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
        self.client.login(username="org", password="pass")
        response = self.client.post(
            reverse("event_form"),
            {
                "title": "Nuevo Evento",
                "description": "Desc",
                "date": self.scheduled_at.strftime("%Y-%m-%d"),
                "time": self.scheduled_at.strftime("%H:%M"),
                "organizer": self.organizer,
                "venue": self.venue.id,
                "category": self.category.id,
                "price_general": "100.00",
                "price_vip": "200.00",
            },
            follow=True,
        )
        self.assertContains(response, "Evento creado exitosamente", status_code=200)
        event = Event.objects.get(title="Nuevo Evento")
        self.assertEqual(event.state, "activo")

    def test_event_update_to_all_states(self):
        self.client.login(username="org", password="pass")
        for state, _ in Event.states:
            self.event.state = "activo"
            self.event.scheduled_at = self.scheduled_at
            self.event.save()
            self.event.refresh_from_db()
            original_date = self.event.scheduled_at.strftime("%Y-%m-%d")
            original_time = self.event.scheduled_at.strftime("%H:%M")
            response = self.client.post(
                reverse("event_edit", args=[self.event.id]),
                {
                    "title": self.event.title,
                    "description": self.event.description,
                    "date": original_date,
                    "time": original_time,
                    "organizer": self.event.organizer,
                    "venue": self.event.venue.id,
                    "category": self.event.category.id,
                    "price_general": str(self.event.price_general),
                    "price_vip": str(self.event.price_vip),
                    "state": state,
                    "original_date": original_date,
                    "original_time": original_time,
                },
                follow=True,
            )
            self.event.refresh_from_db()
            self.assertContains(response, "Evento actualizado exitosamente", status_code=200)
            self.assertEqual(self.event.state, state)

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
        self.client.login(username="org", password="pass")
        self.event.state = "finalizado"
        self.event.save()
        response = self.client.post(
            reverse("event_edit", args=[self.event.id]),
            {
                "title": "Evento Editado",
                "description": self.event.description,
                "date": self.event.scheduled_at.strftime("%Y-%m-%d"),
                "time": self.event.scheduled_at.strftime("%H:%M"),
                "organizer": self.event.organizer,
                "venue": self.event.venue.id,
                "category": self.event.category.id,
                "price_general": self.event.price_general,
                "price_vip": self.event.price_vip,
                "state": self.event.state,
            },
            follow=True,
        )
        self.assertRedirects(response, reverse("events"))
        self.assertContains(response, "No se pueden editar eventos finalizados", status_code=200)
        self.event.refresh_from_db()
        self.assertNotEqual(self.event.title, "Evento Editado")

    def test_no_edit_if_cancelled(self):
        self.client.login(username="org", password="pass")
        self.event.state = "cancelado"
        self.event.save()
        response = self.client.post(
            reverse("event_edit", args=[self.event.id]),
            {
                "title": "Evento Editado",
                "description": self.event.description,
                "date": self.event.scheduled_at.strftime("%Y-%m-%d"),
                "time": self.event.scheduled_at.strftime("%H:%M"),
                "organizer": self.event.organizer,
                "venue": self.event.venue.id,
                "category": self.event.category.id,
                "price_general": self.event.price_general,
                "price_vip": self.event.price_vip,
                "state": self.event.state,
            },
            follow=True,
        )
        self.assertRedirects(response, reverse("events"))
        self.assertContains(response, "No se pueden editar eventos cancelados", status_code=200)
        self.event.refresh_from_db()
        self.assertNotEqual(self.event.title, "Evento Editado")
