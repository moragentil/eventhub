import datetime
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.db.models import Count

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
    user = request.user
    search_query = request.GET.get('search', '')
    priority_filter = request.GET.get('priority', '')

    notifications_queryset = None
    non_organizer_users = None

    if user.is_organizer:
        notifications_queryset = Notification.objects.all().order_by("-created_at")
        non_organizer_users = User.objects.filter(is_organizer=False).count()

        if search_query:
            notifications_queryset = notifications_queryset.filter(title__icontains=search_query)
        if priority_filter:
            notifications_queryset = notifications_queryset.filter(priority=priority_filter)

    else:
        unread_count = Notification.objects.filter(user=user, is_read=False).count()
        notifications_queryset = user.notifications.order_by("-created_at")

    context = {
        "notifications": notifications_queryset,
        "user_is_organizer": user.is_organizer,
        "non_organizer_users": non_organizer_users if user.is_organizer else None,
        "unread_count": unread_count if not user.is_organizer else None,
        "search_query": search_query if user.is_organizer else "",
        "priority_filter": priority_filter if user.is_organizer else "",
        "priorities": Notification.PRIORITY_CHOICES if user.is_organizer else [],
    }
    return render(request, "app/notification/notifications.html", context)

@login_required
def notification_detail(request, id):
    notification = get_object_or_404(Notification, pk=id)
    return render(request, "app/notification/notification_detail.html", {"notification": notification})

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
    
    notification_instance = None
    if id:
        notification_instance = get_object_or_404(Notification, pk=id)

    errors = {}
    users_for_dropdown = User.objects.filter(is_organizer=False)

    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        message_content = request.POST.get("message", "").strip()
        priority = request.POST.get("priority")
        recipient_type = request.POST.get("recipient_type")
        specific_user_id = request.POST.get("specific_user")

        if not title:
            errors["title"] = "Por favor ingrese un titulo"
        elif len(title) > 50: 
            errors["title"] = "El titulo no puede tener mas de 50 caracteres"
        
        if not message_content:
            errors["message"] = "Por favor ingrese un mensaje"
        elif len(message_content) > 500: 
            errors["message"] = "El mensaje no puede tener mas de 500 caracteres"
        
        target_users_queryset = None
        if recipient_type == "all":
            target_users_queryset = User.objects.filter(is_organizer=False)
            if not target_users_queryset.exists():
                errors["recipient_type"] = "No hay usuarios disponibles para enviar la notificación"
        elif recipient_type == "specific":
            if not specific_user_id:
                errors["recipient_type"] = "Por favor seleccione un usuario específico"
            else:
                try:
                    selected_user = User.objects.get(pk=int(specific_user_id), is_organizer=False)
                    target_users_queryset = User.objects.filter(pk=selected_user.pk)
                except (User.DoesNotExist):
                    errors["recipient_type"] = "El usuario seleccionado no existe o no es válido"
                except (ValueError, TypeError):
                    errors["recipient_type"] = "El ID de usuario seleccionado no es válido"
        else:
            errors["recipient_type"] = "Por favor seleccione un tipo de destinatario válido"

        if not errors:
            if id is None:
                success, result = Notification.new(target_users_queryset, title, message_content, priority)
                if not success:
                    errors = result
                else:
                    return redirect("notifications")
            else:
                notification_instance.title = title
                notification_instance.message = message_content
                notification_instance.priority = priority
                notification_instance.save() 
                if target_users_queryset is not None:
                    notification_instance.user.set(target_users_queryset)
                return redirect("notifications")

        context = {
            "notification": notification_instance if id else request.POST, 
            "users": users_for_dropdown,
            "priorities": Notification.PRIORITY_CHOICES,
            "user_is_organizer": request.user.is_organizer,
            "errors": errors,
            "selected_priority": priority,
            "selected_recipient_type": recipient_type,
            "selected_specific_user_id": specific_user_id,
        }
        return render(request, "app/notification/notification_form.html", context)

    context = {
        "notification": notification_instance if id else {}, 
        "users": users_for_dropdown,
        "priorities": Notification.PRIORITY_CHOICES,
        "user_is_organizer": request.user.is_organizer,
    }
    return render(request, "app/notification/notification_form.html", context)

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
