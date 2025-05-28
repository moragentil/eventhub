from django.test import TestCase
from app.models import Event, User, Venue
from django.utils import timezone
import datetime

class CountdownTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="12345")
        self.venue = Venue.objects.create(name="Test Venue", capacity=100)
        self.event = Event.objects.create(
            title="Test Event",
            description="Test Description",
            scheduled_at=timezone.now() + datetime.timedelta(days=5),
            organizer=self.user,
            venue=self.venue,
        )

    def test_countdown_calculation(self):
        now = timezone.now()
        delta = self.event.scheduled_at - now
        self.assertGreater(delta.total_seconds(), 0)