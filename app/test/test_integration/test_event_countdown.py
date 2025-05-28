from django.test import TestCase
from django.urls import reverse
from app.models import Event, User, Venue
from django.utils import timezone
import datetime

class CountdownViewTest(TestCase):
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
        self.client.login(username="testuser", password="12345")

    def test_event_detail_countdown(self):
        response = self.client.get(reverse("event_detail", args=[self.event.id]))
        self.assertEqual(response.status_code, 200)
        self.assertIn("countdown", response.context)