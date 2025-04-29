import datetime
from datetime import datetime as dt
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .models import Event, User, RefundRequest


def register(request):
    if request.method == "POST":
        email = request.POST.get("email")
        username = request.POST.get("username")
        is_organizer = request.POST.get("is-organizer") is not None
        password = request.POST.get("password")
        password_confirm = request.POST.get("password-confirm")

        errors = User.validate_new_user(email, username, password, password_confirm)

        if len(errors) > 0:
            return render(
                request,
                "accounts/register.html",
                {
                    "errors": errors,
                    "data": request.POST,
                },
            )
        else:
            user = User.objects.create_user(
                email=email, username=username, password=password, is_organizer=is_organizer
            )
            login(request, user)
            return redirect("events")

    return render(request, "accounts/register.html", {})


def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is None:
            return render(
                request, "accounts/login.html", {"error": "Usuario o contraseña incorrectos"}
            )

        login(request, user)
        return redirect("events")

    return render(request, "accounts/login.html")


def home(request):
    return render(request, "home.html")


@login_required
def events(request):
    events = Event.objects.all().order_by("scheduled_at")
    return render(
        request,
        "app/events.html",
        {"events": events, "user_is_organizer": request.user.is_organizer},
    )


@login_required
def event_detail(request, id):
    event = get_object_or_404(Event, pk=id)
    return render(request, "app/event_detail.html", {"event": event})


@login_required
def event_delete(request, id):
    user = request.user
    if not user.is_organizer:
        return redirect("events")

    if request.method == "POST":
        event = get_object_or_404(Event, pk=id)
        event.delete()
        return redirect("events")

    return redirect("events")


@login_required
def event_form(request, id=None):
    user = request.user

    if not user.is_organizer:
        return redirect("events")

    if request.method == "POST":
        title = request.POST.get("title")
        description = request.POST.get("description")
        date = request.POST.get("date")
        time = request.POST.get("time")

        [year, month, day] = date.split("-")
        [hour, minutes] = time.split(":")

        scheduled_at = timezone.make_aware(
            datetime.datetime(int(year), int(month), int(day), int(hour), int(minutes))
        )

        if id is None:
            Event.new(title, description, scheduled_at, request.user)
        else:
            event = get_object_or_404(Event, pk=id)
            event.update(title, description, scheduled_at, request.user)

        return redirect("events")

    event = {}
    if id is not None:
        event = get_object_or_404(Event, pk=id)

    return render(
        request,
        "app/event_form.html",
        {"event": event, "user_is_organizer": request.user.is_organizer},
    )


@login_required
def refund_requests(request):
    refund_requests = RefundRequest.objects.filter(user=request.user).order_by("created_at")
    return render(
        request,
        "app/refund_request/refund_requests.html",
        {"refund_requests": refund_requests, "user_is_organizer": request.user.is_organizer},
    )

@login_required
def refund_request_form(request, id=None):
    user = request.user

    if not user.is_organizer:
        return redirect("events")
    
    refund_request = get_object_or_404(RefundRequest, pk=id) if id else None
    
    if request.method == "POST":

        approved = request.POST.get("approved") is not None
        ticket_code = request.POST.get("ticket_code")
        reason = request.POST.get("reason")
        approval_date_str = request.POST.get("approval_date")
        

        errors= []

        """
        Descomentar cuando se implemente el modelo de Ticket
        ticket = ...
        if ticket is None:
            errors.append("El ticket con el código ingresado no existe")
        elif timezone.now() - ticket.created_at > datetime.timedelta(days=30):
            errors.append("El ticket con el código ingresado no es válido para solicitar reembolso")
        
        """
        
        if approval_date_str:
            try:
                approval_date = dt.strptime(approval_date_str, "%Y-%m-%d").date()
            except ValueError:
                errors.append("Fecha inválida. Debe tener formato AAAA-MM-DD.")
        else:
            approval_date = None

        if len(reason.split()) < 1:
            errors.append("El motivo es requerido")
        
        if approved is False and approval_date is not None:
            errors.append("La fecha de aprobación no puede ser ingresada si la solicitud no fue aprobada")
        elif approved is True and approval_date is None:
            errors.append("La fecha de aprobación es requerida si la solicitud fue aprobada")

        if refund_request is None and RefundRequest.objects.filter(ticket_code=ticket_code).exists():
            errors.append("Ya se ha solicitado un reembolso para ese ticket.")
        
        if errors:
            for error in errors:
                messages.error(request, error)
            return render(
                request,
                "app/refund_request/refund_request_form.html",
                {"refund_request": refund_request}
            )

        if id is None:
            RefundRequest.new(user, approved, approval_date, ticket_code, reason)
        else:
            refund_request = get_object_or_404(RefundRequest, pk=id)
            refund_request.update(approved, approval_date, reason)

        return redirect("refund_requests")

    return render(
        request,
        "app/refund_request/refund_request_form.html",
        {"refund_request": refund_request},
    )

@login_required
def refund_request_delete(request, id):
    user = request.user
    if not user.is_organizer:
        return redirect("events")

    refund_request = get_object_or_404(RefundRequest, pk=id)
    if request.method == "POST":
        refund_request.delete()
    return redirect("refund_requests")

@login_required
def refund_request_detail(request, id):
    user = request.user
    if not user.is_organizer:
       return redirect("events")

    refund_request = get_object_or_404(RefundRequest, pk=id)
    return render(request, "app/refund_request/refund_request_detail.html", {"refund_request": refund_request})