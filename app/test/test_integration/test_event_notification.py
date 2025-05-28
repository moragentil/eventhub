from django.urls import reverse
from django.utils import timezone
from django.test import TestCase
from app.models import Event, User, Venue, Category, Notification, Ticket, TicketType

class EventNotificationIntegrationTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="pass")
        self.organizer = User.objects.create_user(username="organizer", password="pass", is_organizer=True)
        self.venue1 = Venue.objects.create(name="Venue 1", address="Calle 1", city="Ciudad", capacity=100)
        self.venue2 = Venue.objects.create(name="Venue 2", address="Calle 2", city="Ciudad", capacity=200)
        self.category = Category.objects.create(name="Categoria", description="desc", is_active=True)
        self.event = Event.objects.create(
            title="Evento Test",
            description="desc",
            scheduled_at=timezone.now() + timezone.timedelta(days=2),
            organizer=self.organizer,
            price_general=50,
            price_vip=100,
            venue=self.venue1,
            category=self.category,
        )
        Ticket.objects.create(event=self.event, quantity=1, type=TicketType.GENERAL, user=self.user)

    def test_notification_created_on_event_date_change(self):
        self.client.login(username="organizer", password="pass")
        new_date = self.event.scheduled_at + timezone.timedelta(days=1)
        response = self.client.post(
            reverse("event_edit", args=[self.event.id]),
            {
                "title": self.event.title,
                "description": self.event.description,
                "date": new_date.strftime("%Y-%m-%d"),
                "time": new_date.strftime("%H:%M"),
                "price_general": self.event.price_general,
                "price_vip": self.event.price_vip,
                "venue": self.venue1.id,
                "category": self.category.id,
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        notif = Notification.objects.filter(user=self.user, title=self.event.title).last()
        self.assertIsNotNone(notif)
        self.assertIn("Fecha actualizada:", notif.message)

    def test_notification_created_on_event_venue_change(self):
        self.client.login(username="organizer", password="pass")
        response = self.client.post(
            reverse("event_edit", args=[self.event.id]),
            {
                "title": self.event.title,
                "description": self.event.description,
                "date": self.event.scheduled_at.strftime("%Y-%m-%d"),
                "time": self.event.scheduled_at.strftime("%H:%M"),
                "price_general": self.event.price_general,
                "price_vip": self.event.price_vip,
                "venue": self.venue2.id,
                "category": self.category.id,
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        notif = Notification.objects.filter(user=self.user, title=self.event.title).last()
        self.assertIsNotNone(notif)
        self.assertIn("Lugar antiguo", notif.message)
        self.assertIn("Nuevo lugar", notif.message)