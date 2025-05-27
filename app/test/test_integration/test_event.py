import datetime
from decimal import Decimal

from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from app.models import Category, Event, User


class BaseEventTestCase(TestCase):
    def setUp(self):
        self.organizer = User.objects.create_user(
            username="organizador",
            email="organizador@test.com",
            password="password123",
            is_organizer=True,
        )

        self.regular_user = User.objects.create_user(
            username="regular",
            email="regular@test.com",
            password="password123",
            is_organizer=False,
        )

        self.category = Category.objects.create(
            name="Categoría Test",
            description="Descripción de categoría test"
        )

        self.event1 = Event.objects.create(
            title="Evento 1",
            description="Descripción del evento 1",
            scheduled_at=timezone.now() + datetime.timedelta(days=1),
            organizer=self.organizer,
            price_general=Decimal("50.00"),
            price_vip=Decimal("100.00"),
            category=self.category
        )

        self.event2 = Event.objects.create(
            title="Evento 2",
            description="Descripción del evento 2",
            scheduled_at=timezone.now() + datetime.timedelta(days=2),
            organizer=self.organizer,
            price_general=Decimal("60.00"),
            price_vip=Decimal("120.00"),
            category=self.category
        )

        self.client = Client()


class EventsListViewTest(BaseEventTestCase):
    def test_events_view_with_login(self):
        self.client.login(username="regular", password="password123")
        response = self.client.get(reverse("events"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "app/event/events.html")
        self.assertIn("events", response.context)
        self.assertIn("user_is_organizer", response.context)
        self.assertEqual(len(response.context["events"]), 2)
        self.assertFalse(response.context["user_is_organizer"])
        events = list(response.context["events"])
        self.assertEqual(events[0].pk, self.event1.pk)
        self.assertEqual(events[1].pk, self.event2.pk)

    def test_events_view_with_organizer_login(self):
        self.client.login(username="organizador", password="password123")
        response = self.client.get(reverse("events"))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["user_is_organizer"])

    def test_events_view_without_login(self):
        response = self.client.get(reverse("events"))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/accounts/login/")) # type: ignore[attr-defined]


class EventDetailViewTest(BaseEventTestCase):
    def test_event_detail_view_with_login(self):
        self.client.login(username="regular", password="password123")
        response = self.client.get(reverse("event_detail", args=[self.event1.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "app/event/event_detail.html")
        self.assertIn("event", response.context)
        self.assertEqual(response.context["event"].pk, self.event1.pk)

    def test_event_detail_view_without_login(self):
        response = self.client.get(reverse("event_detail", args=[self.event1.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/accounts/login/")) # type: ignore[attr-defined]

    def test_event_detail_view_with_invalid_id(self):
        self.client.login(username="regular", password="password123")
        response = self.client.get(reverse("event_detail", args=[999]))
        self.assertEqual(response.status_code, 404)


class EventFormViewTest(BaseEventTestCase):
    def test_event_form_view_with_organizer(self):
        self.client.login(username="organizador", password="password123")
        response = self.client.get(reverse("event_form"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "app/event/event_form.html")
        self.assertIn("event", response.context)
        self.assertTrue(response.context["user_is_organizer"])

    def test_event_form_view_with_regular_user(self):
        self.client.login(username="regular", password="password123")
        response = self.client.get(reverse("event_form"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("events")) # type: ignore[attr-defined]

    def test_event_form_view_without_login(self):
        response = self.client.get(reverse("event_form"))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/accounts/login/")) # type: ignore[attr-defined]

    def test_event_form_edit_existing(self):
        self.client.login(username="organizador", password="password123")
        response = self.client.get(reverse("event_edit", args=[self.event1.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "app/event/event_form.html")
        self.assertEqual(response.context["event"].pk, self.event1.pk)


class EventFormSubmissionTest(BaseEventTestCase):
    def test_event_form_post_create(self):
        self.client.login(username="organizador", password="password123")
        event_data = {
            "title": "Nuevo Evento",
            "description": "Descripción del nuevo evento",
            "date": "2025-05-01",
            "time": "14:30",
            "price_general": "70.00",
            "price_vip": "130.00",
            "venue": "",
            "category": str(self.category.pk),
        }
        # Crear un venue dummy para test
        from app.models import Venue
        venue = Venue.objects.create(name="Test Venue", address="123 Fake St", capacity=100)
        event_data["venue"] = str(venue.pk)
        response = self.client.post(reverse("event_form"), data=event_data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("events")) # type: ignore[attr-defined]
        self.assertTrue(Event.objects.filter(title="Nuevo Evento").exists())

    def test_event_form_post_edit(self):
        self.client.login(username="organizador", password="password123")
        from app.models import Venue
        venue = Venue.objects.create(name="Otro Venue", address="456 Example Ave", capacity=200)
        updated_data = {
            "title": "Evento 1 Actualizado",
            "description": "Nueva descripción actualizada",
            "date": "2025-06-15",
            "time": "16:45",
            "price_general": "80.00",
            "price_vip": "150.00",
            "venue": str(venue.pk),
            "category": str(self.category.pk),
        }
        response = self.client.post(reverse("event_edit", args=[self.event1.pk]), updated_data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("events")) # type: ignore[attr-defined]
        self.event1.refresh_from_db()
        self.assertEqual(self.event1.title, "Evento 1 Actualizado")
        self.assertEqual(self.event1.description, "Nueva descripción actualizada")



class EventDeleteViewTest(BaseEventTestCase):
    def test_event_delete_with_organizer(self):
        self.client.login(username="organizador", password="password123")
        self.assertTrue(Event.objects.filter(pk=self.event1.pk).exists())
        response = self.client.post(reverse("event_delete", args=[self.event1.pk]))
        self.assertRedirects(response, reverse("events"))
        self.assertFalse(Event.objects.filter(pk=self.event1.pk).exists())

    def test_event_delete_with_regular_user(self):
        self.client.login(username="regular", password="password123")
        self.assertTrue(Event.objects.filter(pk=self.event1.pk).exists())
        response = self.client.post(reverse("event_delete", args=[self.event1.pk]))
        self.assertRedirects(response, reverse("events"))
        self.assertTrue(Event.objects.filter(pk=self.event1.pk).exists())

    def test_event_delete_with_get_request(self):
        self.client.login(username="organizador", password="password123")
        response = self.client.get(reverse("event_delete", args=[self.event1.pk]))
        self.assertRedirects(response, reverse("events"))
        self.assertTrue(Event.objects.filter(pk=self.event1.pk).exists())

    def test_event_delete_nonexistent_event(self):
        self.client.login(username="organizador", password="password123")
        nonexistent_id = 9999
        self.assertFalse(Event.objects.filter(pk=nonexistent_id).exists())
        response = self.client.post(reverse("event_delete", args=[nonexistent_id]))
        self.assertEqual(response.status_code, 404)

    def test_event_delete_without_login(self):
        self.assertTrue(Event.objects.filter(pk=self.event1.pk).exists())
        response = self.client.post(reverse("event_delete", args=[self.event1.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/accounts/login/")) # type: ignore[attr-defined]
        self.assertTrue(Event.objects.filter(pk=self.event1.pk).exists())
