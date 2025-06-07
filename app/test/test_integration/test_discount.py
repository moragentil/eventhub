from django.test import TestCase
from django.urls import reverse
from decimal import Decimal
from django.utils import timezone
from app.models import User, Venue, Category, Event, Discount, Ticket

class TicketDiscountIntegrationTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="1234")
        self.venue = Venue.objects.create(name="Estadio", address="Calle 123", city="La Plata", capacity=1000)
        self.category = Category.objects.create(name="Concierto", description="Conciertos en vivo")
        self.discount = Discount.objects.create(code="SALE10", percentage=10)
        self.event = Event.objects.create(
            title="Rock Nacional",
            description="Festival de Rock",
            scheduled_at=timezone.now() + timezone.timedelta(days=10),
            organizer=self.user,
            price_general=Decimal("100.00"),
            price_vip=Decimal("200.00"),
            venue=self.venue,
            category=self.category,
            discount=self.discount
        )
        self.client.login(username="testuser", password="1234")

    def test_ticket_purchase_with_discount(self):
        url = reverse("ticket_create", args=[self.event.pk])
        response = self.client.post(url, {
            "quantity": 2,
            "type": "General",
            "discount_code": "SALE10"
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "¡Compra realizada!")
        self.assertContains(response, "Total pagado:")
        self.assertContains(response, "$180,00")
        self.assertTrue(Ticket.objects.filter(event=self.event, user=self.user).exists())
