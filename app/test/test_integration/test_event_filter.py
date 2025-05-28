from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone
from app.models import Event, User, Venue, Category
from datetime import timedelta

class EventIntegrationTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="test", password="1234")
        self.venue = Venue.objects.create(name="Test", address="Dir", city="C", capacity=100)
        self.category = Category.objects.create(name="Cat", description="Desc")

        self.future_event = Event.objects.create(
            title="Futuro",
            description="Futuro",
            scheduled_at=timezone.now() + timedelta(days=2),
            organizer=self.user,
            price_general=100,
            price_vip=200,
            venue=self.venue,
            category=self.category,
        )

        self.past_event = Event.objects.create(
            title="Pasado",
            description="Pasado",
            scheduled_at=timezone.now() - timedelta(days=2),
            organizer=self.user,
            price_general=100,
            price_vip=200,
            venue=self.venue,
            category=self.category,
        )

    def test_event_list_view_filters_past_events(self):
        self.client.login(username="test", password="1234")
        response = self.client.get(reverse("events"))
        self.assertContains(response, "Futuro")
        self.assertNotContains(response, "Pasado")
