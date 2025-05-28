from django.test import TestCase
from django.urls import reverse
from app.models import User, Event, Favorite, Venue
from django.utils import timezone
import datetime

class FavoriteViewTest(TestCase):
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

    def test_favorite_create(self):
        response = self.client.post(reverse("favorite_create", args=[self.event.id]))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Favorite.objects.filter(user=self.user, event=self.event).exists())