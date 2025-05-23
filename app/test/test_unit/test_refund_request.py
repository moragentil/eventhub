from django.utils import timezone
from django.test import TestCase
from django.contrib.auth import get_user_model
from app.models import RefundRequest, Ticket, Event

User=get_user_model()

class RefundRequestUnitTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="pass")
        organizer = User.objects.create_user(username="org", password="pass")
        self.event = Event.objects.create(
            title="Test Event",
            description="Desc",
            scheduled_at=timezone.now(),
            organizer=organizer
        )
        self.event = Event.objects.get(pk=1)
        self.ticket1 = Ticket.objects.create(ticket_code="ABC123", user=self.user, event=self.event, used=False)
        self.ticket2 = Ticket.objects.create(ticket_code="DEF456", user=self.user, event=self.event, used=False)

    def test_user_cannot_have_multiple_pending_refunds(self):
        RefundRequest.objects.create(user=self.user, status='pendiente', ticket=self.ticket1, reason="Primera")

        refund, errors = RefundRequest.new(self.user, "pendiente", None, self.ticket2, "Segunda")

        self.assertIsNone(refund)
        if errors:
            self.assertIn("general", errors)
            self.assertEqual(errors["general"], "Ya tenés una solicitud de reembolso pendiente.")
        else:
            self.fail("Se esperaba un error de validación, pero no se devolvieron errores.")