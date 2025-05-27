from django.test import TestCase
from django.utils import timezone
from app.models import Event, User, Venue, Category
from datetime import timedelta

class EventFilterUnitTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="user", password="1234")
        self.venue = Venue.objects.create(name="Lugar", address="Dir", city="City", capacity=100)
        self.category = Category.objects.create(name="Concierto", description="Musica")

        # Evento futuro
        Event.objects.create(
            title="Evento Futuro",
            description="Desc",
            scheduled_at=timezone.now() + timedelta(days=1),
            organizer=self.user,
            price_general=100,
            price_vip=200,
            venue=self.venue,
            category=self.category,
        )

        # Evento pasado
        Event.objects.create(
            title="Evento Pasado",
            description="Desc",
            scheduled_at=timezone.now() - timedelta(days=1),
            organizer=self.user,
            price_general=100,
            price_vip=200,
            venue=self.venue,
            category=self.category,
        )

    def test_default_filter_excludes_past_events(self):
        events = Event.objects.filter(scheduled_at__gte=timezone.now())
        self.assertEqual(events.count(), 1)
        self.assertEqual(events.first().title, "Evento Futuro")
