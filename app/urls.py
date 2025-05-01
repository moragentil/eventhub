from django.contrib.auth.views import LogoutView
from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("accounts/register/", views.register, name="register"),
    path("accounts/logout/", LogoutView.as_view(), name="logout"),
    path("accounts/login/", views.login_view, name="login"),
    path("events/", views.events, name="events"),
    path("events/create/", views.event_form, name="event_form"),
    path("events/<int:id>/edit/", views.event_form, name="event_edit"),
    path("events/<int:id>/", views.event_detail, name="event_detail"),
    path("events/<int:id>/delete/", views.event_delete, name="event_delete"),
    path("events/<int:event_id>/tickets/create/", views.ticket_create, name="ticket_create"),
    path("tickets/", views.organizer_ticket_list, name="organizer_ticket_list"),
    path("my-tickets/", views.user_ticket_list, name="user_ticket_list"),
    path('tickets/<int:ticket_id>/', views.ticket_detail, name='ticket_detail'),
    path("tickets/<int:ticket_id>/update/", views.ticket_update, name="ticket_update"),
    path("tickets/<int:ticket_id>/delete/", views.ticket_delete, name="ticket_delete"),
    path("refund-request/", views.refund_requests, name="refund_requests"),
    path("refunds/<int:refund_id>/approve/", views.approve_refund_request, name="refund_request_approve"),
    path("refunds/<int:refund_id>/reject/", views.reject_refund_request, name="refund_request_reject"),
    path("my_refunds/", views.user_refund_requests, name="user_refund_requests"),
    path("refund-request/create/", views.refund_request_form, name="refund_request_form"),
    path("refund-request/<int:id>/edit/", views.refund_request_form, name="refund_request_edit"),
    path("refund-request/<int:id>/", views.refund_request_detail, name="refund_request_detail"),
    path("refund-request/<int:id>/delete/", views.refund_request_delete, name="refund_request_delete"),
    path("venue/", views.venue, name="venue"),
    path("venue/create/", views.venue_form, name="venue_form"),
    path("venue/<int:id>/edit/", views.venue_form, name="venue_edit"),
    path("venue/<int:id>/", views.venue_detail, name="venue_detail"),
    path("venue/<int:id>/delete/", views.venue_delete, name="venue_delete"),
    path("ratings/create/<int:event_id>/", views.rating_create, name="rating_create"),
    path("ratings/<int:rating_id>/delete/", views.rating_delete, name="rating_delete"),
    path("ratings/", views.user_rating_list, name="user_rating_list")
]
