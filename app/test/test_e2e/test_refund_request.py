import datetime
import re
from django.utils import timezone
from playwright.sync_api import expect
from app.models import Event, Ticket, User
from app.test.test_e2e.base import BaseE2ETest


class RefundRequestBaseTest(BaseE2ETest):
    def setUp(self):
        super().setUp()

        # Creo usuario organizador y usuario regular
        self.organizer = User.objects.create_user(
            username="organizador",
            email="org@example.com",
            password="password123",
            is_organizer=True,
        )
        self.user = User.objects.create_user(
            username="usuario",
            email="user@example.com",
            password="123",  # Confirmado por vos
            is_organizer=False,
        )

        # Creo evento
        event_date = timezone.make_aware(datetime.datetime(2025, 6, 10, 20, 0))
        self.event = Event.objects.create(
            title="Evento E2E",
            description="Evento para prueba E2E",
            scheduled_at=event_date,
            organizer=self.organizer,
        )

        # Creo dos tickets para el usuario
        self.ticket1 = Ticket.objects.create(
            ticket_code="REFUND1", user=self.user, event=self.event, used=False
        )
        self.ticket2 = Ticket.objects.create(
            ticket_code="REFUND2", user=self.user, event=self.event, used=False
        )


class RefundRequestE2ETest(RefundRequestBaseTest):
    def test_user_cannot_create_duplicate_pending_refund(self):
        # Inicio sesión como usuario
        self.login_user("usuario", "123")

        # Relleno y envío primer formulario de reembolso
        self.page.goto(f"{self.live_server_url}/refund-request/create/?ticket_code={self.ticket1.ticket_code}")
        campo = self.page.locator("textarea[name='reason']")
        expect(campo).to_be_visible()
        campo.fill("Quiero reembolso del primer ticket")
        self.page.get_by_role("button", name="Crear Solicitud").click()

        # Relleno y envío segundo formulario de reembolso
        self.page.goto(f"{self.live_server_url}/refund-request/create/?ticket_code={self.ticket2.ticket_code}")
        campo2 = self.page.locator("textarea[name='reason']")
        expect(campo2).to_be_visible()
        campo2.fill("Quiero reembolso del segundo ticket")
        self.page.get_by_role("button", name="Crear Solicitud").click()

        # Verifico que se muestre el mensaje de error
        error_message = self.page.locator("text=Ya tenés una solicitud de reembolso pendiente.")
        expect(error_message).to_be_visible()

