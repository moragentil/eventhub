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
    path("refund-request/", views.refund_requests, name="refund_requests"),
    path("refund-request/create/", views.refund_request_form, name="refund_request_form"),
    path("refund-request/<int:id>/edit/", views.refund_request_form, name="refund_request_edit"),
    path("refund-request/<int:id>/", views.refund_request_detail, name="refund_request_detail"),
    path("refund-request/<int:id>/delete/", views.refund_request_delete, name="refund_request_delete"),
]
