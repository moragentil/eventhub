from django.utils import timezone
from django.test import TestCase
from app.models import Event, User, Venue, Notification, Category

class EventNotificationTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="pass")
        self.organizer = User.objects.create_user(username="organizer", password="pass", is_organizer=True)
        self.venue1 = Venue.objects.create(name="Venue 1", address="1", city="Ciudad1", capacity=100)
        self.venue2 = Venue.objects.create(name="Venue 2", address="2", city="Ciudad2", capacity=200)
        self.category = Category.objects.create(name="Test Category", is_active=True)
        self.state = "activo"
        self.event = Event.objects.create(
            title="Test Event",
            description="A test event",
            scheduled_at=timezone.now(),
            organizer=self.organizer,
            venue=self.venue1,
            category=self.category,
            state=self.state,
        )
        self.user.tickets.create(event=self.event, quantity=2)

    def test_notification_created_on_date_change(self):
        old_date = self.event.scheduled_at
        new_date = old_date + timezone.timedelta(days=1)
        success, errors = self.event.update(
            title=None,
            description=None,
            scheduled_at=new_date,
            organizer=None,
            price_general=None,
            price_vip=None,
            venue=None,
            category=None,
            state=None,
        )
        self.assertTrue(success, f"Errores inesperados: {errors}")
        notif = Notification.objects.filter(user=self.user, title=self.event.title).last()
        self.assertIsNotNone(notif)
        self.assertIn("Fecha antigua", notif.message)
        self.assertIn("Fecha actualizada", notif.message)

    def test_notification_created_on_venue_change(self):
        success, errors = self.event.update(
            title=None,
            description=None,
            scheduled_at=None,
            organizer=None,
            price_general=None,
            price_vip=None,
            venue=self.venue2,
            category=None,
            state=None,
        )
        self.assertTrue(success, f"Errores inesperados: {errors}")
        notif = Notification.objects.filter(user=self.user, title=self.event.title).last()
        self.assertIsNotNone(notif)
        self.assertIn("Lugar antiguo", notif.message)
        self.assertIn("Nuevo lugar", notif.message)