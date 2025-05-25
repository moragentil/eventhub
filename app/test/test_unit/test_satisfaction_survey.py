import datetime
from decimal import Decimal
from typing import cast

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from app.models import Category, Event, SatisfactionSurvey, Ticket, Venue

User = get_user_model()

class SatisfactionSurveyModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="12345", email="test@test.com")
        self.category = Category.objects.create(name="Concierto", description="Musical")
        self.venue = Venue.objects.create(
            name="Estadio",
            address="Av. Siempre Viva 123",
            city="Springfield",
            capacity=5000
        )
        self.event = Event.objects.create(
            title="Rock Fest",
            description="Festival de rock",
            scheduled_at=timezone.now() + datetime.timedelta(days=10),
            organizer=self.user,
            price_general=Decimal("100.00"),
            price_vip=Decimal("200.00"),
            venue=self.venue,
            category=self.category
        )
        self.ticket = Ticket.objects.create(
            user=self.user,
            event=self.event,
            quantity=1,
            type="General"
        )

    # Test para crear encuesta válida.
    def test_create_valid_survey(self):
        survey, errors = SatisfactionSurvey.new(
            ticket=self.ticket,
            comfort_rating="4",
            clarity_rating="5",
            satisfaction_rating="3",
            comment="Muy buena experiencia"
        )
        self.assertIsNotNone(survey)
        self.assertIsNone(errors)

    # Test que verifica que no se puedan crear encuestas duplicadas por ticket.
    def test_duplicate_survey_not_allowed(self):
        SatisfactionSurvey.objects.create(
            ticket=self.ticket,
            comfort_rating="4",
            clarity_rating="5",
            satisfaction_rating="3",
            comment=""
        )

        # Intentar crear otro para el mismo ticket
        survey, errors = SatisfactionSurvey.new(
            ticket=self.ticket,
            comfort_rating="5",
            clarity_rating="5",
            satisfaction_rating="5",
            comment="Excelente"
        )

        self.assertIsNone(survey)
        errors = cast(dict, errors)
        self.assertIn("duplicate", errors)
        
    # Test que verifica que las calificaciones estén dentro del rango permitido.
    def test_invalid_rating_out_of_range(self):
        survey, errors = SatisfactionSurvey.new(
            ticket=self.ticket,
            comfort_rating="6", 
            clarity_rating="0",  
            satisfaction_rating="-1", 
            comment=""
        )

        self.assertIsNone(survey)
        errors = cast(dict, errors)
        self.assertIn("comfort_rating", errors)
        self.assertIn("clarity_rating", errors)
        self.assertIn("satisfaction_rating", errors)

    # Test que verifica que no haya valores vacíos en los campos obligatorios.
    def test_missing_ticket(self):
        survey, errors = SatisfactionSurvey.new(
            ticket=None,
            comfort_rating="3",
            clarity_rating="3",
            satisfaction_rating="3",
            comment=""
        )
        self.assertIsNone(survey)
        errors = cast(dict, errors)
        self.assertIn("ticket", errors)
