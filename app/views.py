import datetime
from datetime import datetime as dt
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from decimal import Decimal
from .models import Event, User, Ticket, TicketType,Rating
from django.db.models import Count, Avg, Sum
from .decorators import organizer_required
from django.contrib import messages
from django.http import JsonResponse
from .models import Event, User, RefundRequest, Venue, Ticket, TicketType, Notification, Comment, Category, SatisfactionSurvey, Discount, Favorite



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

    if not date and not venue_id and not category_id:
        events = events.filter(scheduled_at__gte=timezone.now())

    if date:
        events = events.filter(scheduled_at__date=date)
    if venue_id:
        events = events.filter(venue_id=venue_id)
    if category_id:
        events = events.filter(category_id=category_id)

    favorite_event_ids = Favorite.objects.filter(user=request.user).values_list("event_id", flat=True)
    favorite_events = Event.objects.filter(id__in=favorite_event_ids)

    return render(request, "app/event/events.html", {
        "events": events,
        "venues": venues,
        "categories": categories,
        "user_is_organizer": request.user.is_organizer,
        "favorite_events": favorite_events,
    })


@login_required
def event_detail(request, id):
    event = get_object_or_404(Event, pk=id)
    comments = Comment.objects.filter(event=event).select_related("user").order_by("-created_at")
    time = timezone.now()
    user_is_organizer = getattr(request.user, "is_organizer", False)
    
    tickets_sold = Ticket.objects.filter(event=event).aggregate(total=Sum("quantity"))["total"] or 0
    demand_message = None
    if event.venue and event.venue.capacity:
        occupancy_rate = (tickets_sold / event.venue.capacity) * 100
        if occupancy_rate > 90:
            demand_message = "Alta demanda (más del 90% de la ocupación)"
        elif occupancy_rate < 10:
            demand_message = "Baja demanda (menos del 10% de la ocupación)"
            
    return render(request, "app/event/event_detail.html", 
        {
            "event": event, "time" : time,
            "user_is_organizer": user_is_organizer, 
            "comments": comments,
            "tickets_sold": tickets_sold,
            "demand_message": demand_message,
        },
    )


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

    if id:
        event = get_object_or_404(Event, pk=id)
        if event.state == "finalizado":
            messages.error(request, "No se pueden editar eventos finalizados.")
            return redirect("events")

    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        description = request.POST.get("description", "").strip()
        date = request.POST.get("date")
        time = request.POST.get("time")
        price_general = request.POST.get("price_general")
        price_vip = request.POST.get("price_vip")
        venue_id = request.POST.get("venue")
        category_id = request.POST.get("category")
        discount_code = request.POST.get("discount_code", "").strip()
        discount_percentage = request.POST.get("discount_percentage", "").strip()
        state = request.POST.get("state", "activo")
        original_date = request.POST.get("original_date")
        original_time = request.POST.get("original_time")

        fecha_cambiada = (
            original_date != date or original_time != time
        )

        if id and fecha_cambiada and state not in ["cancelado", "reprogramado"]:
            state = "reprogramado"


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

        discount = None
        if discount_code and discount_percentage:
            # Validar longitud y tipo
            if len(discount_code) > 10:
                errors["discount_code"] = "El código no puede tener más de 10 caracteres."
            try:
                discount_pct = int(discount_percentage)
                if discount_pct <= 0 or discount_pct > 100:
                    errors["discount_percentage"] = "El porcentaje debe estar entre 1 y 100."
            except Exception:
                errors["discount_percentage"] = "El porcentaje debe ser un número válido."
            # Crear o buscar descuento
            if not errors.get("discount_code") and not errors.get("discount_percentage"):
                discount_obj, created = Discount.objects.get_or_create(
                    code=discount_code,
                    defaults={"percentage": discount_pct}
                )
                if not created:
                    discount_obj.percentage = discount_pct
                    discount_obj.save()
                discount = discount_obj

        if id is None:
            success, validation_errors = Event.new(
                title, description, scheduled_at, user,
                price_general, price_vip, venue,
                category=category,
                discount=discount,
                state=state,
            )
            if not success:
                errors.update(validation_errors)
            else:
                messages.success(request, "Evento creado exitosamente!")
        else:
            event = get_object_or_404(Event, pk=id)
            previous_state = event.state
            success, validation_errors = event.update(
                title=title,
                description=description,
                scheduled_at=scheduled_at,
                organizer=event.organizer,
                price_general=price_general,
                price_vip=price_vip,
                venue=venue,
                category=category,
                discount=discount,
                state=state
            )
            if not success:
                errors.update(validation_errors)
            else:
                messages.success(request, "Evento actualizado exitosamente!")
        
            if state in ["cancelado"] and previous_state != state:
                users = User.objects.filter(tickets__event=event).distinct()
                if users.exists():
                    if state == "cancelado":
                        description = f"El evento {event.title} ha sido cancelado."
                    Notification.new(
                        users,
                        title = f"El evento {event.title} ha sido {state}.",
                        message=description,
                        priority="High"
                    )

        return redirect("events")

    elif id:
        event = get_object_or_404(Event, pk=id)
        state = event.state
        if event.state == "finalizado" or event.state == "cancelado":
            messages.error(request, f"No se pueden editar eventos {event.state}s.")
            return redirect("events")
    else:
        state = "activo"
        
    categories = Category.objects.filter(is_active=True)

    return render(
        request,
        "app/event/event_form.html",
        {
            "event": event,
            "venues": venues,
            "state": state,
            "errors": errors,
            "editing": id is not None,
            "user_is_organizer": user.is_organizer,
            "categories": categories
        },
    )


@login_required
def ticket_create(request, event_id):
    event = get_object_or_404(Event, pk=event_id)

    if event.state in ["agotado", "finalizado", "cancelado"]:
        messages.error(request, f"No se pueden comprar entradas para este evento porque esta {event.state}.")
        return redirect("event_detail", id=event.pk)

    if event.scheduled_at < timezone.now():
        messages.error(request, "No se puede comprar una entrada de un evento que ya pasó.")
        return redirect("event_detail", id=event.pk)

    unit_price = None
    total_amount = None
    data = {}

    if request.method == "POST":
        quantity = request.POST.get("quantity")
        type = request.POST.get("type")
        discount_code_input = request.POST.get("discount_code", "").strip()
        data = request.POST

        try:
            quantity_int = int(quantity) if quantity else 0
        except ValueError:
            quantity_int = 0

        if type == "VIP":
            unit_price = event.price_vip
        elif type == "General":
            unit_price = event.price_general

        # Aplicar descuento si corresponde
        discount_applied = False
        if unit_price is not None and discount_code_input and event.discount:
            if discount_code_input.lower() == event.discount.code.lower():
                percentage = event.discount.percentage or Decimal("0.00")
                discount_amount = unit_price * (percentage / 100)
                unit_price = max(Decimal("0.00"), unit_price - discount_amount)
                discount_applied = True
            else:
                messages.error(request, "Código de descuento inválido.")

        if unit_price is not None:
            total_amount = unit_price * quantity_int

        ticket, errors = Ticket.new(
            quantity=quantity_int,
            type=type,
            user=request.user,
            event=event,
        )
        if ticket:
            return render(
                request,
                "app/ticket/ticket_form.html",
                {
                    "event": event,
                    "data": {},
                    "unit_price": unit_price,
                    "total_amount": total_amount,
                    "mostrar_encuesta": True,
                    "ticket_id": ticket.pk,
                    "discount_applied": discount_applied,
                },
            )
        else:
            return render(
                request,
                "app/ticket/ticket_form.html",
                {
                    "errors": errors,
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
        ticket.delete()

        if 'update' in referer or f'tickets/{ticket_id}/' in referer:
            return redirect('user_ticket_list')

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
    event = ticket.event
    unit_price = event.price_vip if ticket.type == "VIP" else event.price_general
    total_amount = unit_price * ticket.quantity

    discount_applied = False
    discounted_total = None

    if event.discount and event.discount.code and event.discount.percentage:
        percentage = event.discount.percentage
        discount_amount = unit_price * (percentage / 100)
        discounted_unit_price = unit_price - discount_amount
        discounted_total = discounted_unit_price * ticket.quantity
        discount_applied = True

    return render(
        request,
        "app/ticket/ticket_detail.html",
        {
            "ticket": ticket,
            "total_amount": total_amount,
            "discount_applied": discount_applied,
            "discounted_total": discounted_total,
        },
    )


@login_required
def ticket_update(request, ticket_id):
    ticket = get_object_or_404(Ticket, pk=ticket_id)

    if request.method == "POST":
        quantity = request.POST.get("quantity")
        type = request.POST.get("type")
        used = request.POST.get("used")

        try:
            quantity_int = int(quantity)
        except (ValueError, TypeError):
            quantity_int = None

        ticket_updated, errors = Ticket.update(ticket_id, quantity=quantity_int, type=type, used=used)

        if ticket_updated:
            if request.user.is_organizer:
                return redirect("organizer_ticket_list")
            else:
                return redirect("user_ticket_list")
        else:
            return render(
                request,
                "app/ticket/ticket_update.html",
                {"errors": errors, "ticket": ticket, "data": request.POST},
            )

    return render(
        request,
        "app/ticket/ticket_update.html",
        {
            "ticket": ticket,
            "event": ticket.event,
            "ticket_types": TicketType.choices
        },
    )

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
    ticket_code_initial = request.GET.get("ticket_code") if request.method == "GET" else None

    if request.method == "POST":
        reason = request.POST.get("reason")
        ticket_code = request.POST.get("ticket_code")

        ticket = Ticket.objects.filter(ticket_code=ticket_code).first()

        if id is None:
            refund_instance, errors = RefundRequest.new(user, "pendiente", None, ticket, reason)
        else:
            if refund_request:
                success, errors = refund_request.update("pendiente", None, reason)
            else:
                success, errors = False, {"refund_request": "Solicitud de reembolso no encontrada."}


        if errors:
            for field, error in errors.items():
                messages.error(request, f"{field}: {error}")
            return render(
                request,
                "app/refund_request/refund_request_form.html",
                {
                    "refund_request": refund_request,
                    "ticket_code": ticket_code,
                }
            )

        return redirect("user_refund_requests")

    else:
        ticket_code = refund_request.ticket.ticket_code if refund_request else ticket_code_initial
        return render(
            request,
            "app/refund_request/refund_request_form.html",
            {
                "refund_request": refund_request,
                "ticket_code": ticket_code,
            },
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
    venues = Venue.objects.all()
    return render(request, "app/venue/venue.html", {"venues": venues})


@login_required
@organizer_required
def venue_form(request, id=None):
    venue_instance = get_object_or_404(Venue, pk=id) if id else None
    form_data = {}

    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        address = request.POST.get("address", "").strip()
        city = request.POST.get("city", "").strip()
        contact = request.POST.get("contact", "").strip()
        capacity_raw = request.POST.get("capacity")

        form_data = {
            "name": name,
            "address": address,
            "city": city,
            "capacity": capacity_raw,
            "contact": contact,
        }

        try:
            capacity = int(capacity_raw) if capacity_raw else None
        except ValueError:
            capacity = None
            if not capacity_raw:
                messages.error(request, "capacity: La capacidad es obligatoria.")
            else:
                messages.error(request, "capacity: La capacidad debe ser un número válido.")

        if venue_instance:
            success, errors = venue_instance.update(name, address, city, capacity, contact)
        else:
            venue_instance, errors = Venue.new(name, address, city, capacity, contact)
            success = venue_instance is not None

        if not success and errors:
            for field, error in errors.items():
                messages.error(request, f"{field}: {error}")
            return render(request, "app/venue/venue_form.html", {
                "venue": venue_instance,
                "form_data": form_data
            })

        messages.success(request, "Lugar guardado exitosamente!")
        return redirect("venue_detail", id=venue_instance.pk)

    return render(request, "app/venue/venue_form.html", {
        "venue": venue_instance,
        "form_data": form_data
    })


@login_required
@organizer_required
def venue_delete(request, id):
    venue = get_object_or_404(Venue, pk=id)

    if request.method == "POST":
        if Event.objects.filter(venue=venue).exists():
            messages.error(request, "No se puede eliminar el lugar porque tiene eventos asociados.")
        else:
            venue.delete()
            messages.success(request, "El lugar ha sido eliminado correctamente.")
        return redirect("venue")

    return render(request, "app/venue/venue_confirm_delete.html", {"venue": venue})


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
        title = request.POST.get("title", "").strip()
        text = request.POST.get("text", "").strip()
        rating_value = request.POST.get("rating")

        try:
            rating_value = int(rating_value)
        except (ValueError, TypeError):
            rating_value = None

        rating_errors = Rating.validate(title, text, rating_value, event)

        if rating_errors:
            return render(
                request,
                "app/event/event_detail.html",
                {
                    "rating_errors": rating_errors,
                    "event": event,
                    "data": {"title": title, "text": text, "rating": rating_value}
                },
            )

        success, rating = Rating.new(
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

        messages.error(request, "Ocurrió un error al crear la calificación.")
        return redirect("event_detail", id=event_id)

    return render(request, "app/rating/rating_form.html", {"event": event})


@login_required
def rating_delete(request, rating_id):
    rating = get_object_or_404(Rating, pk=rating_id)

    if request.method == "POST":
        rating.delete()
        messages.success(request, "Calificación eliminada correctamente.")
    
    return redirect("event_detail", id=rating.event.id)


@login_required
def rating_edit(request, rating_id):
    rating = get_object_or_404(Rating, pk=rating_id)

    if rating.user != request.user:
        messages.error(request, "No tenés permiso para editar esta calificación.")
        return redirect("event_detail", id=rating.event.id)

    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        text = request.POST.get("text", "").strip()
        rating_value = request.POST.get("rating")

        try:
            rating_value = int(rating_value)
        except (ValueError, TypeError):
            rating_value = None

        success, rating_errors = rating.update(title, text, rating_value)

        if success:
            messages.success(request, "Calificación actualizada correctamente.")
        else:
            messages.error(request, "Error al actualizar la calificación.")

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
            errors["title"] = "El título es obligatorio"
    
        if not message_content:
            errors["message"] = "El mensaje es obligatorio"

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
                except (User.DoesNotExist, ValueError, TypeError):
                    errors["recipient_type"] = "El usuario seleccionado no existe o no es válido"
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
                success, result = Notification.update(
                    notification_id=id,
                    title=title,
                    message=message_content,
                    priority=priority,
                    users=target_users_queryset
                )
                if not success:
                    errors = result
                else:
                    return redirect("notifications")

        if errors:
            context = {
                "notification": {
                    'title': title,
                    'message': message_content,
                },
                "users": users_for_dropdown,
                "priorities": Notification.PRIORITY_CHOICES,
                "user_is_organizer": user.is_organizer,
                "errors": errors,
                "selected_recipient_type": recipient_type,
                "selected_specific_user_id": specific_user_id,
                "selected_priority": priority,
            }
            return render(request, "app/notification/notification_form.html", context)
        
    if id:
        all_users_count = User.objects.filter(is_organizer=False).count()
        notification_users_count = notification_instance.user.count()
        
        selected_recipient_type = "all" if notification_users_count == all_users_count else "specific"
        selected_specific_user_id = notification_instance.user.first().id if notification_users_count == 1 else None
        selected_priority = notification_instance.priority
    else:
        selected_recipient_type = "all"
        selected_specific_user_id = None
        selected_priority = "low"

    if id:
        all_users_count = User.objects.filter(is_organizer=False).count()
        notification_users_count = notification_instance.user.count()
        
        selected_recipient_type = "all" if notification_users_count == all_users_count else "specific"
        selected_specific_user_id = notification_instance.user.first().id if notification_users_count == 1 else None
        selected_priority = notification_instance.priority
    else:
        selected_recipient_type = "all"
        selected_specific_user_id = None
        selected_priority = "low"

    context = {
        "notification": notification_instance if id else {},
        "users": users_for_dropdown,
        "priorities": Notification.PRIORITY_CHOICES,
        "user_is_organizer": user.is_organizer,
        "selected_recipient_type": selected_recipient_type,
        "selected_specific_user_id": selected_specific_user_id,
        "selected_priority": selected_priority,
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
        name = request.POST.get("name", "").strip()
        description = request.POST.get("description", "").strip()
        is_active = request.POST.get("is_active") == "on"

        errors = Category.validate(name, description)

        if errors:
            return render(request, "app/category/category_form.html", {
                "category": category,
                "errors": errors,
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

    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        text = request.POST.get("text", "").strip()

        errors = Comment.validate(title, text, event)

        if errors:
            return render(request, "app/event/event_detail.html",{
                "event": event,
                "comments": Comment.objects.filter(event=event),
                "errors": errors,
                "data": request.POST
            })

    Comment.objects.create(event=event, user=request.user, title=title, text=text)
    return redirect("event_detail", id=event_id)

@login_required
def comment_detail(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    return render(request, "app/comment/comment_detail.html", {"comment": comment})

@login_required
def comment_delete(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    event_id = comment.event.id

    if request.user.is_organizer:
        if comment.event.organizer != request.user:
            messages.error(request, "No tienes permiso para eliminar comentarios de eventos que no organizaste.")
            return redirect("comments_list")

    if comment.user == request.user or (request.user.is_organizer and comment.event.organizer == request.user):
        if request.method == "POST":
            comment.delete()
            if request.user.is_organizer:
                messages.success(request, "Comentario eliminado correctamente.")
                return redirect("comments_list")
            else:
                messages.success(request, "Comentario eliminado correctamente.")
                return redirect("event_detail", id=event_id)

    if request.user.is_organizer:
        return redirect("comments_list")
    else:
        messages.error(request, "No tienes permiso para eliminar este comentario.")
        return redirect("event_detail", id=event_id)

@login_required
def comment_edit(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    if comment.user != request.user:
        messages.error(request, "No tienes permiso para editar este comentario.")
        return redirect("event_detail", id=comment.event.id)

    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        text = request.POST.get("text", "").strip()

        errors = Comment.validate(title, text, comment.event)
        if errors:
            messages.error(request, "Por favor corrige los errores del formulario.")
            return redirect("event_detail", id=comment.event.id)

        comment.title = title
        comment.text = text
        comment.save()
        messages.success(request, "Comentario actualizado correctamente.")
        return redirect("event_detail", id=comment.event.id)

    return redirect("event_detail", id=comment.event.id)

@login_required
def submit_survey(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id, user=request.user)

    if hasattr(ticket, 'survey'):
        return redirect('home')

    if request.method == "POST":
        comfort = request.POST.get("comfort_rating")
        clarity = request.POST.get("clarity_rating")
        satisfaction = request.POST.get("satisfaction_rating")
        comment = request.POST.get("comment", "")

        survey, errors = SatisfactionSurvey.new(
            ticket=ticket,
            comfort_rating=comfort,
            clarity_rating=clarity,
            satisfaction_rating=satisfaction,
            comment=comment
        )

        if errors:
            return render(request, "app/satisfaction_survey/satisfaction_survey_form.html", {
                "errors": errors,
                "ticket": ticket,
                "form_data": request.POST
            })

        return redirect("events") 

    return render(request, "app/satisfaction_survey/satisfaction_survey_form.html", {"ticket": ticket})

@login_required
def survey_dashboard(request):
    if not request.user.is_organizer:
        return redirect('home')

    surveys = SatisfactionSurvey.objects.select_related("ticket__event").all()

    promedio_comfort = surveys.aggregate(prom=Avg("comfort_rating"))["prom"]
    promedio_clarity = surveys.aggregate(prom=Avg("clarity_rating"))["prom"]
    promedio_satisfaction = surveys.aggregate(prom=Avg("satisfaction_rating"))["prom"]

    return render(request, "app/satisfaction_survey/survey_dashboard.html", {
        "surveys": surveys,
        "promedio_comfort": promedio_comfort,
        "promedio_clarity": promedio_clarity,
        "promedio_satisfaction": promedio_satisfaction,
    })

@login_required
def favorite_create(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    Favorite.objects.get_or_create(user=request.user, event=event)
    return redirect("events")

@login_required
def favorite_remove(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    Favorite.objects.filter(user=request.user, event=event).delete()
    return redirect("events")

@login_required
def validate_discount(request):
    code = request.GET.get('code', '')
    event_id = request.GET.get('event_id')
    
    try:
        event = Event.objects.get(pk=event_id)
        if event.discount and event.discount.code.lower() == code.lower():
            return JsonResponse({
                'valid': True,
                'percentage': float(event.discount.percentage)
            })
    except Event.DoesNotExist:
        pass
    
    return JsonResponse({'valid': False})
