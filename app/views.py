import datetime
from datetime import datetime as dt
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from decimal import Decimal
from .models import Event, User, Ticket, TicketType,Rating
from django.db.models import Count
from .decorators import organizer_required
from django.contrib import messages
from .models import Event, User, RefundRequest, Venue, Ticket, TicketType, Notification, Comment, Category


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
            return redirect("home")

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
        return redirect("home")

    return render(request, "accounts/login.html")


def home(request):
    user = request.user
    if not user.is_authenticated:
        return render(request, "home_public.html")
    if getattr(user, "is_organizer", False):
        return render(request, "home_organizer.html", {"name": user.username})
    return render(request, "home_user.html", {"name": user.username})


@login_required
def events(request):
    events = Event.objects.all()
    venues = Venue.objects.all()
    categories = Category.objects.all()

    date = request.GET.get("date")
    venue_id = request.GET.get("venue")
    category_id = request.GET.get("category")

    if date:
        events = events.filter(scheduled_at__date=date)
    if venue_id:
        events = events.filter(venue_id=venue_id)
    if category_id:
        events = events.filter(category_id=category_id)

    return render(request, "app/event/events.html", {
        "events": events,
        "venues": venues,
        "categories": categories,
        "user_is_organizer": request.user.is_organizer,
    })


@login_required
def event_detail(request, id):
    event = get_object_or_404(Event, pk=id)
    comments = Comment.objects.filter(event=event).select_related("user").order_by("-created_at")
    time = timezone.now()
    user_is_organizer = getattr(request.user, "is_organizer", False)
    return render(request, "app/event/event_detail.html", {"event": event, "time" : time,"user_is_organizer": user_is_organizer, "comments": comments})


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

    venues = Venue.objects.all()
    event = None
    errors = {}

    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        description = request.POST.get("description", "").strip()
        date = request.POST.get("date")
        time = request.POST.get("time")
        price_general = request.POST.get("price_general")
        price_vip = request.POST.get("price_vip")
        venue_id = request.POST.get("venue")
        category_id = request.POST.get("category")

        try:
            scheduled_at = timezone.make_aware(
                datetime.datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
            )
        except ValueError:
            errors["scheduled_at"] = "Fecha y hora inválidas."
            scheduled_at = None

        try:
            price_general = Decimal(price_general)
        except:
            errors["price_general"] = "Precio general inválido."

        try:
            price_vip = Decimal(price_vip)
        except:
            errors["price_vip"] = "Precio VIP inválido."

        venue = get_object_or_404(Venue, pk=venue_id)
        category = get_object_or_404(Category, pk=category_id) if category_id else None

        if id is None:
            success, validation_errors = Event.new(
                title, description, scheduled_at, user,
                price_general, price_vip, venue,
                category=category
            )
        else:
            event = get_object_or_404(Event, pk=id)
            event.title = title
            event.description = description
            if scheduled_at is not None:
                event.scheduled_at = scheduled_at
            event.organizer = request.user
            event.price_general = price_general
            event.price_vip = price_vip
            event.save()  

        return redirect("events")

    elif id:
        event = get_object_or_404(Event, pk=id)
        
    categories = Category.objects.filter(is_active=True)

    return render(
        request,
        "app/event/event_form.html",
        {
            "event": event,
            "venues": venues,
            "errors": errors,
            "editing": id is not None,
            "user_is_organizer": user.is_organizer,
            "categories": categories},
    )


@login_required
def ticket_create(request, event_id):
    event = get_object_or_404(Event, pk=event_id)

    if event.scheduled_at < timezone.now():
        messages.error(request, "No se puede comprar una entrada de un evento que ya pasó.")
        return redirect("event_detail", id=event.pk)

    unit_price = None
    total_amount = None
    data = {}

    if request.method == "POST":
        quantity = request.POST.get("quantity")
        type = request.POST.get("type")
        data = request.POST

        try:
            quantity_int = int(quantity) if quantity else 0
        except ValueError:
            quantity_int = 0

        if type == "VIP":
            unit_price = event.price_vip
        elif type == "General":
            unit_price = event.price_general

        if unit_price is not None:
            total_amount = unit_price * quantity_int

        success, result = Ticket.new(
            quantity=quantity_int,
            type=type,
            user=request.user,
            event=event,
        )

        if success:
            return redirect("user_ticket_list")
        else:
            return render(
                request,
                "app/ticket/ticket_form.html",
                {
                    "errors": result,
                    "event": event,
                    "data": data,
                    "unit_price": unit_price,
                    "total_amount": total_amount,
                },
            )

    return render(
        request,
        "app/ticket/ticket_form.html",
        {
            "event": event,
            "data": data,
            "unit_price": unit_price,
            "total_amount": total_amount,
        },
    )


@login_required
def ticket_delete(request, ticket_id):
    ticket = get_object_or_404(Ticket, pk=ticket_id)

    if request.method == "POST":
        referer = request.META.get('HTTP_REFERER', '')
        if 'update' in referer or 'tickets/{}/'.format(ticket_id) in referer:
            ticket.delete()
            return redirect('user_ticket_list')
        
        ticket.delete()
        return redirect(referer or 'event_list')

    return redirect('event_list')



@login_required
@organizer_required
def organizer_ticket_list(request):
    tickets = Ticket.objects.all()
    return render(request, "app/ticket/organizer_ticket_list.html", {"tickets": tickets})


@login_required
def ticket_detail(request, ticket_id):
    ticket = get_object_or_404(Ticket, pk=ticket_id)

    if ticket.type == 'VIP':
        total_amount = ticket.quantity * ticket.event.price_vip
    else:
        total_amount = ticket.quantity * ticket.event.price_general
    
    return render(request, 'app/ticket/ticket_detail.html', {
        'ticket': ticket,
        'total_amount': total_amount,
    })


@login_required
def ticket_update(request, ticket_id):
    ticket = get_object_or_404(Ticket, pk=ticket_id)

    if request.method == "POST":
        quantity = request.POST.get("quantity")
        type = request.POST.get("type")
        used = request.POST.get("used")

        success, result = Ticket.update(ticket_id, quantity=int(quantity), type=type, used=used)

        if success:
            if request.user.is_organizer:
                return redirect("organizer_ticket_list")
            else:
                return redirect("user_ticket_list")
        else:
            return render(
                request,
                "app/ticket/ticket_update.html",
                {"errors": result, "ticket": ticket, "data": request.POST},
            )

    return render(request, "app/ticket/ticket_update.html", {
                                                    "ticket": ticket,
                                                    "event": ticket.event,
                                                    "ticket_types": TicketType.choices
                                                    })

@login_required
def user_ticket_list(request):
    tickets = Ticket.objects.filter(user=request.user)
    return render(request, "app/ticket/user_ticket_list.html", {"tickets": tickets})


@login_required
@organizer_required
def refund_requests(request):
    refund_requests = RefundRequest.objects.all().order_by("-created_at")
    return render(
        request,
        "app/refund_request/refund_requests.html",
        {"refund_requests": refund_requests, "user_is_organizer": request.user.is_organizer},
    )


@login_required
@organizer_required
def approve_refund_request(request, refund_id):
    refund = get_object_or_404(RefundRequest, id=refund_id)
    if request.method == "POST":
        refund.status = 'aprobado'
        refund.approval_date = timezone.now()
        refund.save()
        messages.success(request, "Solicitud aprobada correctamente.")
    return redirect('refund_requests')


@login_required
@organizer_required
def reject_refund_request(request, refund_id):
    refund = get_object_or_404(RefundRequest, id=refund_id)
    if request.method == "POST":
        refund.status = 'rechazado'
        refund.approval_date = timezone.now()
        refund.save()
        messages.success(request, "Solicitud rechazada correctamente.")
    return redirect('refund_requests')


@login_required
def user_refund_requests(request):
    refund_requests = RefundRequest.objects.filter(user=request.user).order_by("-created_at")
    return render(
        request,
        "app/refund_request/user_refund_requests.html",
        {"refund_requests": refund_requests},
    )


@login_required
def refund_request_form(request, id=None):
    user = request.user    
    refund_request = get_object_or_404(RefundRequest, pk=id) if id else None
    
    if request.method == "POST":
        approved = request.POST.get("approved") is not None
        status = 'aprobado' if approved else 'pendiente'  
        
        ticket_code = request.POST.get("ticket_code")
        reason = request.POST.get("reason")
        approval_date_str = request.POST.get("approval_date")
        
        errors = []

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

        ticket = Ticket.objects.filter(ticket_code=ticket_code).first()  
        if ticket is None:
            errors.append("El ticket con el código ingresado no existe")
        elif RefundRequest.objects.filter(ticket=ticket).exists() and refund_request is None:
            errors.append("Ya se ha solicitado un reembolso para ese ticket.")
        elif ticket.used:  
            errors.append("El ticket ya ha sido usado y no puede ser reembolsado")
        elif ticket.event.scheduled_at + datetime.timedelta(days=30) < timezone.now():  
            errors.append("El ticket con el código ingresado no es válido para solicitar reembolso, han pasado más de 30 días desde el evento")

        if errors:
            for error in errors:
                messages.error(request, error)
            return render(
                request,
                "app/refund_request/refund_request_form.html",
                {"refund_request": refund_request}
            )

        if id is None:
            RefundRequest.new(user, status, approval_date, ticket, reason)
        else:
            if refund_request:
                refund_request.update(status, approval_date, reason)

        return redirect("user_refund_requests")

    return render(
        request,
        "app/refund_request/refund_request_form.html",
        {"refund_request": refund_request},
    )



@login_required
def refund_request_delete(request, id):
    user = request.user
    refund_request = get_object_or_404(RefundRequest, pk=id)
    
    if request.method == "POST":
        refund_request.delete()
    return redirect("user_refund_requests")

@login_required
def refund_request_detail(request, id):
    user = request.user
    refund_request = get_object_or_404(RefundRequest, pk=id)
    return render(request, "app/refund_request/refund_request_detail.html", {"refund_request": refund_request})

@login_required
def venue(request):
    venues = Venue.objects.all().order_by("name")
    return render(
        request,
        "app/venue/venue.html",
        {"venues": venues, "user_is_organizer": request.user.is_organizer},
    )

@login_required
def venue_form(request, id=None):
    user = request.user
    if not user.is_organizer:
        return redirect("events")
    
    if request.method == "POST":
        name = request.POST.get("name")
        address = request.POST.get("address")
        city = request.POST.get("city")
        contact = request.POST.get("contact")

        capacity_raw = request.POST.get("capacity")
        try:
            capacity = int(capacity_raw)
        except (TypeError, ValueError):
            capacity = None

        if id is None:
            success, errors = Venue.new(name, address, city, capacity, contact)
            if not success:
                if errors:
                    for field, error in errors.items():
                        messages.error(request, f"{field}: {error}")
                    return render(request, "app/venue/venue_form.html", {
                        "venue": None,
                })
        else:
            venue = get_object_or_404(Venue, pk=id)
            success, errors = venue.update(name, address, city, capacity, contact)
            if not success:
                if errors:
                    for field, error in errors.items():
                        messages.error(request, f"{field}: {error}")
                    return render(request, "app/venue/venue_form.html", {
                        "venue": venue,
                    })

        return redirect("venue")

    return render(
        request,
        "app/venue/venue_form.html",
        {"venue": get_object_or_404(Venue, pk=id) if id else None},
    )

@login_required
def venue_delete(request, id):
    user = request.user
    if not user.is_organizer:
        return redirect("events")
    
    if request.method == "POST":
        venue = get_object_or_404(Venue, pk=id)
        if not Event.objects.filter(venue=venue).exists():
            venue.delete()
            messages.success(request, "El lugar ha sido eliminado correctamente.")
        else:
            messages.error(request, "No se puede eliminar el lugar porque tiene eventos asociados.")
            return render(
                request,
                "app/venue/venue.html",
                {"error": "No se puede eliminar el lugar porque tiene eventos asociados."}
            )
        
    return redirect("venue")

@login_required
def venue_detail(request, id):
    venue = get_object_or_404(Venue, pk=id)
    return render(request, "app/venue/venue_detail.html", {"venue": venue})

@login_required
def rating_create(request, event_id):
    event = get_object_or_404(Event, pk=event_id)

    has_ticket = Ticket.objects.filter(event=event, user=request.user).exists()
    if not has_ticket:
        messages.error(request, "Debes comprar una entrada para calificar este evento.")
        return redirect("event_detail", id=event_id)

    if request.method == "POST":
        title = request.POST.get("title")
        text = request.POST.get("text")
        rating_value = request.POST.get("rating")

        try:
            rating_value = int(rating_value)
        except ValueError:
            rating_value = None


        if rating_value is None or rating_value < 1 or rating_value > 10:
            messages.error(request, "La calificación debe estar entre 1 y 10.")
            return render(request, "app/rating/rating_form.html", {"event": event, "data": request.POST})

        success, result = Rating.new(
            title=title,
            text=text,
            rating=rating_value,
            created_at=timezone.now(),
            user=request.user,
            event=event,
        )

        if success:
            messages.success(request, "Calificación creada exitosamente.")
            return redirect("event_detail", id=event_id)
        else:
            return render(
                request,
                "app/rating/rating_form.html",
                {"errors": result, "event": event, "data": request.POST},
            )
    return render(request, "app/rating/rating_form.html", {"event": event})

@login_required
def rating_delete(request, rating_id):
    rating = get_object_or_404(Rating, pk=rating_id)

    if request.method == "POST":
        rating.delete()
        messages.success(request, "Calificacion eliminada correctamente")
        return redirect("event_detail", id=rating.event.id)
    
    return redirect("event_detail", id=rating.event.id)

@login_required
def rating_edit(request, rating_id):
    rating = get_object_or_404(Rating, pk=rating_id)

    if rating.user != request.user:
        messages.error(request, "No tenés permiso para editar esta calificación.")
        return redirect("event_detail", id=rating.event.id)

    if request.method == "POST":
        title = request.POST.get("title")
        text = request.POST.get("text")
        rating_value = request.POST.get("rating")

        try:
            rating_value = int(rating_value)
        except (ValueError, TypeError):
            rating_value = None

        success, result = rating.update(title, text, rating_value)

        if success:
            messages.success(request, "Calificación actualizada correctamente.")
        else:
            messages.error(request, "Error al actualizar la calificación.")

        return redirect("event_detail", id=rating.event.id)

    return redirect("event_detail", id=rating.event.id)

@login_required
def user_rating_list(request):
    ratings = Rating.objects.filter(user=request.user)
    return render(request, "app/rating/rating_list.html", {"ratings": ratings})


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
                if notification_instance:
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
@login_required
@organizer_required


def category_list(request):
    categories = Category.objects.all()
    return render(
        request,
        "app/category/categories.html",
        {"categories": categories}
    )


@login_required
@organizer_required
def category_form(request, id=None):
    category = get_object_or_404(Category, pk=id) if id else None

    if request.method == "POST":
        name = request.POST.get("name")
        description = request.POST.get("description")
        is_active = request.POST.get("is_active") == "on"

        errors = {}

        if not name:
            errors["name"] = "El nombre es requerido."
        if not description:
            errors["description"] = "La descripción es requerida."

        if errors:
            for field, error in errors.items():
                messages.error(request, f"{field}: {error}")
            return render(request, "app/category/category_form.html", {
                "category": category,
            })

        if category is None:
            Category.objects.create(
                name=name,
                description=description,
                is_active=is_active
            )
        else:
            category.name = name
            category.description = description
            category.is_active = is_active
            category.save()

        return redirect("category_list")

    return render(
        request,
        "app/category/category_form.html",
        {"category": category}
    )


@login_required
@organizer_required
def category_delete(request, id):
    if request.method == "POST":
        category = get_object_or_404(Category, pk=id)

        if Event.objects.filter(category=category).exists():
            messages.error(request, "No se puede eliminar la categoría porque tiene eventos asociados.")
            return redirect("category_list")

        category.delete()
        messages.success(request, "Categoría eliminada correctamente.")

    return redirect("category_list")


@login_required
@organizer_required
def category_detail(request, id):
    category = get_object_or_404(Category, pk=id)

    return render(request, "app/category/category_detail.html", {
        "category": category,
    })

@login_required
def comments_list(request):
    comments = Comment.objects.select_related("event", "user").order_by("-created_at")
    return render(request, "app/comment/comments_list.html", {"comments": comments})

@login_required
def comment_create(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    title = request.POST.get("title")
    text = request.POST.get("text")
    if title and text:
        Comment.objects.create(event=event, user=request.user, title=title, text=text)
    return redirect("event_detail", id=event_id)

@login_required
def comment_detail(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    return render(request, "app/comment/comment_detail.html", {"comment": comment})

@login_required
def comment_delete(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)

    if comment.user == request.user or request.user.is_organizer:
        if request.method == "POST":
            comment.delete()
            return redirect("comments_list")

    return redirect("comments_list")
