import datetime
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from app.models import Category, Event, SatisfactionSurvey, Ticket, Venue

User = get_user_model()

class SatisfactionSurveyIntegrationTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="user1", password="testpass")
        self.other_user = User.objects.create_user(username="user2", password="testpass")

        self.category = Category.objects.create(name="Teatro", description="Teatro clásico")
        self.venue = Venue.objects.create(name="Sala A", address="Calle Falsa 123", city="Springfield", capacity=100)

        self.event = Event.objects.create(
            title="Obra de teatro",
            description="Una obra emocionante",
            scheduled_at=timezone.now() + datetime.timedelta(days=10),
            organizer=self.user,
            price_general=Decimal("50.00"),
            price_vip=Decimal("80.00"),
            venue=self.venue,
            category=self.category
        )

        self.ticket = Ticket.objects.create(user=self.user, event=self.event, quantity=1, type="General")

    def test_get_survey_form_success(self):
        self.client.login(username="user1", password="testpass")
        response = self.client.get(reverse("submit_survey", args=[self.ticket.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Encuesta de satisfacción")

    def test_submit_valid_survey(self):
        self.client.login(username="user1", password="testpass")
        response = self.client.post(reverse("submit_survey", args=[self.ticket.pk]), {
            "comfort_rating": "5",
            "clarity_rating": "4",
            "satisfaction_rating": "5",
            "comment": "Excelente experiencia"
        })
        self.assertEqual(response.status_code, 302)  # Redirige tras éxito
        self.assertTrue(SatisfactionSurvey.objects.filter(ticket=self.ticket).exists())

    def test_duplicate_survey_rejected(self):
        SatisfactionSurvey.objects.create(
            ticket=self.ticket,
            comfort_rating="4",
            clarity_rating="4",
            satisfaction_rating="4",
            comment=""
        )

        self.client.login(username="user1", password="testpass")
        response = self.client.get(reverse("submit_survey", args=[self.ticket.pk]))
        self.assertEqual(response.status_code, 302)  # Redirige si ya existe

    def test_user_cannot_access_other_users_ticket(self):
        self.client.login(username="user2", password="testpass")
        response = self.client.get(reverse("submit_survey", args=[self.ticket.pk]))
        self.assertEqual(response.status_code, 404)
