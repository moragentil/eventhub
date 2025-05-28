from django.test import TestCase
from app.models import User, Event, Venue, Category, Rating
from django.utils import timezone
import datetime

class RatingModelTest(TestCase):
    def setUp(self):
        self.organizer = User.objects.create_user(username="organizador", email="org@example.com", password="password123", is_organizer=True)
        self.venue = Venue.objects.create(name="Lugar Test", address="Calle 123", city="Ciudad", capacity=100)
        self.category = Category.objects.create(name="Categoria Test", description="desc")
        self.event = Event.objects.create(
            title="Evento Test",
            description="desc",
            scheduled_at=timezone.now() + datetime.timedelta(days=1),
            organizer=self.organizer,
            price_general=100,
            price_vip=200,
            venue=self.venue,
            category=self.category
        )
        self.user = User.objects.create_user(username="usuario", email="user@example.com", password="password123")

    def test_rating_requires_title(self):
        rating = Rating(
            event=self.event,
            user=self.user,
            title="",
            text="Muy bueno",
            rating=8
        )
        with self.assertRaises(Exception):
            rating.save()