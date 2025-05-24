from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from app.models import Event, Ticket, RefundRequest

User = get_user_model()

class RefundRequestIntegrationTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="pass")
        self.client.login(username="testuser", password="pass")
        organizer = User.objects.create_user(username="org", password="pass")
        self.event = Event.objects.create(
            title="Test Event",
            description="Desc",
            scheduled_at=timezone.now(),
            organizer=organizer
        )
        self.ticket1 = Ticket.objects.create(ticket_code="TICKET1", user=self.user, event=self.event, used=False)
        self.ticket2 = Ticket.objects.create(ticket_code="TICKET2", user=self.user, event=self.event, used=False)
        RefundRequest.objects.create(user=self.user, status='pendiente', ticket=self.ticket1, reason="Primera solicitud")

    def test_user_cannot_create_duplicate_pending_refund(self):
        response = self.client.post(reverse('refund_request_form'), {
            "ticket_code": self.ticket2.ticket_code,
            "reason": "Intento duplicado"
        }, follow=True)
        self.assertContains(response, "Ya tenés una solicitud de reembolso pendiente.")
