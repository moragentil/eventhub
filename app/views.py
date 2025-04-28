import datetime
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .models import Event, User, Ticket
from .decorators import organizer_required


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
def ticket_create(request, event_id):
    event = get_object_or_404(Event, pk=event_id)

    if request.method == "POST":
        quantity = request.POST.get("quantity")
        type = request.POST.get("type")

        success, result = Ticket.new(
            quantity=int(quantity),
            type=type,
            user=request.user,
            event=event,
        )

        if success:
            return redirect("event_detail", id=event.pk)
        else:
            return render(
                request,
                "app/ticket_form.html",
                {"errors": result, "event": event, "data": request.POST},
            )

    return render(request, "app/ticket_form.html", {"event": event})


@login_required
def ticket_delete(request, ticket_id):
    ticket = get_object_or_404(Ticket, pk=ticket_id)

    if request.method == "POST":
        ticket.delete()
        return redirect("event_detail", id=ticket.event.pk)

    return redirect("event_detail", id=ticket.event.pk)


@login_required
@organizer_required
def organizer_ticket_list(request):
    tickets = Ticket.objects.all()
    return render(request, "app/organizer_ticket_list.html", {"tickets": tickets})

@login_required
def ticket_detail(request, ticket_id):
    ticket = get_object_or_404(Ticket, pk=ticket_id)
    return render(request, "app/ticket_detail.html", {"ticket": ticket})


@login_required
def ticket_update(request, ticket_id):
    ticket = get_object_or_404(Ticket, pk=ticket_id)

    if request.method == "POST":
        quantity = request.POST.get("quantity")

        success, result = Ticket.update(ticket_id, quantity=int(quantity))

        if success:
            return redirect("ticket_detail", id=ticket.event.pk)
        else:
            return render(
                request,
                "app/ticket_update.html",
                {"errors": result, "ticket": ticket, "data": request.POST},
            )

    return render(request, "app/ticket_update.html", {
                                                    "ticket": ticket,
                                                    "event": ticket.event
                                                    })

@login_required
def user_ticket_list(request):
    tickets = Ticket.objects.filter(user=request.user)
    return render(request, "app/user_ticket_list.html", {"tickets": tickets})
