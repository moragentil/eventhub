import datetime
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .models import Event, User, Notification


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
def notifications(request):
    notifications = Notification.objects.filter(user=request.user).order_by("-created_at")
    return render(
        request,
        "app/notifications.html",
        {
            "notifications": notifications, "user_is_organizer": request.user.is_organizer,
        }
        )

@login_required
def notification_detail(request, id):
    notification = get_object_or_404(Notification, pk=id)
    return render(request, "app/notification_detail.html", {"notification": notification})

@login_required
def notification_delete(request, id):
    user = request.user
    if not user.is_organizer:
        return redirect("notifications")
    
    if request.method == "POST":
        notification = get_object_or_404(Notification, pk=id)
        notification.delete()
        return redirect("notifications")
    
    return redirect("notifications")

@login_required
def notification_form(request, id=None):
    user = request.user

    if not user.is_organizer:
        return redirect("notifications")
    
    errors = {}
    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        message = request.POST.get("message", "").strip()
        priority = request.POST.get("priority")
        user_ids = request.POST.getlist("user_ids")

        if title == "":
            errors["title"] = "Por favor ingrese un titulo"
        elif len(title) > 100:
            errors["title"] = "El titulo no puede tener mas de 100 caracteres"
        
        if message == "":
            errors["message"] = "Por favor ingrese un mensaje"
        elif len(message) > 500:
            errors["message"] = "El mensaje no puede tener mas de 500 caracteres"
        
        if not user_ids:
            errors["user_ids"] = "Por favor seleccione al menos un usuario"

        if errors:
            notification = {}
            if id:
                notification = get_object_or_404(Notification, pk=id)
            return render(
                request,
                "app/notification_form.html",
                {
                    "notification": notification,
                    "priorities": Notification.PRIORITY_CHOICES,
                    "user_is_organizer": request.user.is_organizer,
                    "users": User.objects.all(),
                    "errors": errors,
                },
            )

        if id is None:
            users_ids = request.POST.getlist("user_ids")
            users = User.objects.filter(id__in=users_ids)

            success, result = Notification.new(users, title, message, priority)
            if not success:
                return render(
                    request,
                    "app/notification_form.html",
                    {
                        "notification": {},
                        "priorities": Notification.PRIORITY_CHOICES,
                        "user_is_organizer": request.user.is_organizer,
                        "errors": result,
                    },
                )
            notification = result
        else:
            notification = get_object_or_404(Notification, pk=id)
            notification.update(title, message, priority)
            notification.users.set(user_ids)
            notification.save()

            user_ids = request.POST.getlist("user_ids")
            notification.users.set(user_ids)
            notification.save()

        return redirect("notifications")
    
    users = User.objects.all()
    notification = {}
    if id is not None:
        notification = get_object_or_404(Notification, pk=id)

    return render(
        request,
        "app/notification_form.html",
        {
            "notification": notification,
            "users": users,
            "priorities": Notification.PRIORITY_CHOICES,
            "user_is_organizer": request.user.is_organizer,
        }
    )

@login_required
def mark_notification_as_read(request, id):
    notification = get_object_or_404(Notification, pk=id)
    notification.is_read = True
    notification.save()
    return redirect("notifications")

@login_required
def mark_all_notifications_as_read(request):
    notifications = Notification.objects.filter(user=request.user, is_read=False)
    for notification in notifications:
        notification.is_read = True
        notification.save()
    return redirect("notifications")
