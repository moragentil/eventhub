import datetime
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from app.models import Category, Event, User


class EventModelTest(TestCase):
    def setUp(self):
        self.organizer = User.objects.create_user(
            username="organizador_test",
            email="organizador@example.com",
            password="password123",
            is_organizer=True,
        )
        self.category = Category.objects.create(name="Concierto")

    def test_event_creation(self):
        event = Event.objects.create(
            title="Evento de prueba",
            description="Descripción del evento de prueba",
            scheduled_at=timezone.now() + datetime.timedelta(days=1),
            organizer=self.organizer,
            price_general=Decimal("50.00"),
            price_vip=Decimal("100.00"),
            category=self.category,
            state = "activo",
        )
        self.assertEqual(event.title, "Evento de prueba")
        self.assertEqual(event.description, "Descripción del evento de prueba")
        self.assertEqual(event.organizer, self.organizer)
        self.assertIsNotNone(event.created_at)
        self.assertIsNotNone(event.updated_at)

    def test_event_validate_with_valid_data(self):
        scheduled_at = timezone.now() + datetime.timedelta(days=1)
        errors = Event.validate(
            "Título válido",
            "Descripción válida",
            scheduled_at,
            Decimal("50.00"),
            Decimal("100.00"),
            self.category,
            state = "activo"
        )
        self.assertEqual(errors, {})

    def test_event_validate_with_empty_title(self):
        scheduled_at = timezone.now() + datetime.timedelta(days=1)
        errors = Event.validate(
            "",
            "Descripción válida",
            scheduled_at,
            Decimal("50.00"),
            Decimal("100.00"),
            self.category,
            state = "activo",
        )
        self.assertIn("title", errors)
        self.assertEqual(errors["title"], "Por favor ingrese un titulo")

    def test_event_validate_with_empty_description(self):
        scheduled_at = timezone.now() + datetime.timedelta(days=1)
        errors = Event.validate(
            "Título válido",
            "",
            scheduled_at,
            Decimal("50.00"),
            Decimal("100.00"),
            self.category,
            state = "activo"
        )
        self.assertIn("description", errors)
        self.assertEqual(errors["description"], "Por favor ingrese una descripcion")

    def test_event_new_with_valid_data(self):
        scheduled_at = timezone.now() + datetime.timedelta(days=2)
        success, errors = Event.new(
            title="Nuevo evento",
            description="Descripción del nuevo evento",
            scheduled_at=scheduled_at,
            organizer=self.organizer,
            price_general=Decimal("60.00"),
            price_vip=Decimal("120.00"),
            venue=None,
            category=self.category,
            state = "activo",
        )

        self.assertTrue(success)
        self.assertEqual(errors, {})

        new_event = Event.objects.get(title="Nuevo evento")
        self.assertEqual(new_event.description, "Descripción del nuevo evento")
        self.assertEqual(new_event.organizer, self.organizer)

    def test_event_new_with_invalid_data(self):
        scheduled_at = timezone.now() + datetime.timedelta(days=2)
        initial_count = Event.objects.count()

        success, errors = Event.new(
            title="",
            description="Descripción del evento",
            scheduled_at=scheduled_at,
            organizer=self.organizer,
            price_general=Decimal("50.00"),
            price_vip=Decimal("100.00"),
            venue=None,
            category=self.category,
            state = "activo",
        )

        self.assertFalse(success)
        self.assertIn("title", errors)
        self.assertEqual(Event.objects.count(), initial_count)

    def test_event_update(self):
        new_title = "Título actualizado"
        new_description = "Descripción actualizada"
        new_scheduled_at = timezone.now() + datetime.timedelta(days=3)

        event = Event.objects.create(
            title="Evento de prueba",
            description="Descripción del evento de prueba",
            scheduled_at=timezone.now() + datetime.timedelta(days=1),
            organizer=self.organizer,
            price_general=Decimal("50.00"),
            price_vip=Decimal("100.00"),
            category=self.category,
            state = "activo",
        )

        event.update(
            title=new_title,
            description=new_description,
            scheduled_at=new_scheduled_at,
            organizer=self.organizer,
            price_general=Decimal("60.00"),
            price_vip=Decimal("120.00"),
            venue=None,
            category=self.category,
            state = "activo",
        )

        updated_event = Event.objects.get(pk=event.pk)
        self.assertEqual(updated_event.title, new_title)
        self.assertEqual(updated_event.description, new_description)
        self.assertEqual(updated_event.scheduled_at.time(), new_scheduled_at.time())

    def test_event_update_partial(self):
        event = Event.objects.create(
            title="Evento de prueba",
            description="Descripción del evento de prueba",
            scheduled_at=timezone.now() + datetime.timedelta(days=1),
            organizer=self.organizer,
            price_general=Decimal("50.00"),
            price_vip=Decimal("100.00"),
            category=self.category,
            state = "activo",
        )

        original_title = event.title
        original_scheduled_at = event.scheduled_at
        new_description = "Solo la descripción ha cambiado"

        event.update(
            title=None,
            description=new_description,
            scheduled_at=None,
            organizer=None,
            price_general=None,
            price_vip=None,
            venue=None,
            category=None,
            state=None
        )

        updated_event = Event.objects.get(pk=event.pk)
        self.assertEqual(updated_event.title, original_title)
        self.assertEqual(updated_event.description, new_description)
        self.assertEqual(updated_event.scheduled_at, original_scheduled_at)