from django.test import TestCase
from app.models import User, Event, Favorite, Venue
from django.utils import timezone
import datetime

class FavoriteModelTest(TestCase):
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

    def test_add_favorite(self):
        favorite = Favorite.objects.create(user=self.user, event=self.event)
        self.assertTrue(Favorite.objects.filter(user=self.user, event=self.event).exists())

    def test_remove_favorite(self):
        favorite = Favorite.objects.create(user=self.user, event=self.event)
        favorite.delete()
        self.assertFalse(Favorite.objects.filter(user=self.user, event=self.event).exists())