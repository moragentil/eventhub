from django.test import TestCase, Client
from django.urls import reverse
from app.models import User, Event, Venue, Category, Rating
from django.utils import timezone
import datetime

class RatingIntegrationTest(TestCase):
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
        self.client = Client()
        self.client.login(username="usuario", password="password123")

    def test_user_can_submit_rating(self):
        from app.models import Ticket
        Ticket.objects.create(
            user=self.user,
            event=self.event,
            quantity=1,
            type="General"
        )
        response = self.client.post(
            reverse("rating_create", args=[self.event.id]),
            {
                "title": "Excelente",
                "text": "Muy buen evento",
                "rating": 10
            },
            follow=True
        )
        self.assertContains(response, "Excelente")
        self.assertTrue(Rating.objects.filter(event=self.event, user=self.user, title="Excelente").exists())