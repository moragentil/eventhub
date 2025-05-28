from django.test import TestCase
from decimal import Decimal
from app.models import Discount

class DiscountModelTest(TestCase):
    def test_create_discount_valid(self):
        discount = Discount.objects.create(code="PROMO10", percentage=10)
        self.assertEqual(discount.code, "PROMO10")
        self.assertEqual(discount.percentage, Decimal("10"))

    def test_discount_code_max_length(self):
        discount = Discount.objects.create(code="ABCDEFGHIJ", percentage=5)
        self.assertEqual(len(discount.code), 10)

    def test_discount_percentage_range(self):
        discount = Discount.objects.create(code="RANGE", percentage=100)
        self.assertEqual(discount.percentage, Decimal("100"))

    def test_discount_str(self):
        discount = Discount.objects.create(code="STRTEST", percentage=15)
        self.assertIn("STRTEST", str(discount))
        self.assertIn("15", str(discount))