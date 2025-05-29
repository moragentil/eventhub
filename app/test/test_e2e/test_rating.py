import datetime
from django.utils import timezone
from django.urls import reverse
from playwright.sync_api import expect
from decimal import Decimal
import re

from app.models import User, Event, Venue, Category, Rating
from app.test.test_e2e.base import BaseE2ETest

class EventRatingE2ETest(BaseE2ETest):
    def setUp(self):
        super().setUp()

        self.rater1 = User.objects.create_user(
            username="rater1_rating_test",
            email="rater1_rating@example.com",
            password="password123",
            is_organizer=True,
        )
        self.rater2 = User.objects.create_user(
            username="rater2_rating_test",
            email="rater2_rating@example.com",
            password="password123",
        )
        self.rater3 = User.objects.create_user(
            username="rater3_rating_test",
            email="rater3_rating@example.com",
            password="password123",
        )

        self.venue = Venue.objects.create(
            name="Rating Test Venue",
            address="123 Test St",
            city="Testville",
            capacity=100
        )
        self.category = Category.objects.create(
            name="Rating Test Category",
            description="Category for rating tests"
        )
        self.event = Event.objects.create(
            title="Event For Rating Average Test",
            description="An event to test average rating display.",
            scheduled_at=timezone.now() + datetime.timedelta(days=5),
            organizer=self.rater1,
            price_general=Decimal("50.00"),
            price_vip=Decimal("100.00"),
            venue=self.venue,
            category=self.category,
        )

        Rating.objects.create(
            event=self.event,
            user=self.rater1,
            title="Good", 
            text="Decent event",
            rating=7,  
            created_at=timezone.now()
        )
        Rating.objects.create(
            event=self.event,
            user=self.rater2,
            title="Great", 
            text="Enjoyed it",
            rating=8,  
            created_at=timezone.now()
        )
        Rating.objects.create(
            event=self.event,
            user=self.rater3,
            title="Excellent", 
            text="Loved it!",
            rating=9,  
            created_at=timezone.now()
        )

    def test_average_rating_and_count_display_on_event_detail(self):
        self.login_user(self.rater1.username, "password123")

        event_detail_url = self.live_server_url + reverse("event_detail", args=[self.event.pk])
        self.page.goto(event_detail_url)

        rating_badge_locator = self.page.locator("h4:has-text('Calificaciones y Reseñas') span.badge")

        expect(rating_badge_locator).to_be_visible()

        avg_rating_element = rating_badge_locator.locator("strong")
        expect(avg_rating_element).to_be_visible()
        expect(avg_rating_element).to_have_text(re.compile(r"4[,.]0"))

        rating_count_element = rating_badge_locator.locator("span").filter(has_text=re.compile(r"\(\d+ Reseñas\)"))
        
        expect(rating_count_element).to_be_visible()
        expect(rating_count_element).to_contain_text("(3 Reseñas)")

    def tearDown(self):
        super().tearDown()