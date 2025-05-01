import datetime
from datetime import datetime as dt
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from decimal import Decimal

from .models import Event, User, Ticket, TicketType,Rating
from .decorators import organizer_required
from django.contrib import messages
from .models import Event, User, RefundRequest, Venue, Ticket, TicketType


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
        "app/event/events.html",
        {"events": events, "user_is_organizer": request.user.is_organizer},
    )


@login_required
def event_detail(request, id):
    event = get_object_or_404(Event, pk=id)
    time = timezone.now()
    return render(request, "app/event/event_detail.html", {"event": event, "time" : time})


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
        price_general = request.POST.get("price_general")
        price_vip = request.POST.get("price_vip")

        [year, month, day] = date.split("-")
        [hour, minutes] = time.split(":")

        scheduled_at = timezone.make_aware(
            datetime.datetime(int(year), int(month), int(day), int(hour), int(minutes))
        )

        price_general = Decimal(price_general)
        price_vip = Decimal(price_vip)

        if id is None:
            Event.objects.create(
                title=title, 
                description=description, 
                scheduled_at=scheduled_at, 
                organizer=request.user, 
                price_general=price_general, 
                price_vip=price_vip
            )
        else:
            event = get_object_or_404(Event, pk=id)
            event.title = title
            event.description = description
            event.scheduled_at = scheduled_at
            event.organizer = request.user
            event.price_general = price_general
            event.price_vip = price_vip
            event.save()  

        return redirect("events")

    event = {}
    if id is not None:
        event = get_object_or_404(Event, pk=id)

    return render(
        request,
        "app/event/event_form.html",
        {"event": event, "user_is_organizer": request.user.is_organizer},
    )


@login_required
def ticket_create(request, event_id):
    event = get_object_or_404(Event, pk=event_id)

    if event.scheduled_at < timezone.now():
        messages.error(request, "No se puede comprar una entrada de un evento que ya pasó.")
        return redirect("event_detail", id=event.pk)

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
            return redirect("user_ticket_list")
        else:
            return render(
                request,
                "app/ticket/ticket_form.html",
                {"errors": result, "event": event, "data": request.POST},
            )

    return render(request, "app/ticket/ticket_form.html", {"event": event})


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

        success, result = Ticket.update(ticket_id, quantity=int(quantity), type=type)

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
    return render(request, "app/refund_request_detail.html", {"refund_request": refund_request})

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
    if request.method == "POST":
        title = request.POST.get("title")
        text = request.POST.get("text")
        rating_value = request.POST.get("rating")
        
        try:
            rating_value = int(rating_value)
        except ValueError:
            rating_value = None
        
        success,result = Rating.new(
            title=title,
            text=text,
            rating=rating_value,
            created_at=timezone.now(),
            user=request.user,
            event=event,
        )

        if success:
            messages.success(request, "Calificación creada exitosamente")
            return redirect("event_detail", id=event_id)
        else:
            return render(
                request,
                "app/rating/rating_form.html",
                {"errors": result, "event": event, "data": request.POST},
            )
    return render(request, "app/rating/rating_form.html",{"event":event})

@login_required
def rating_delete(request, rating_id):
    rating = get_object_or_404(Rating, pk=rating_id)

    if request.method == "POST":
        rating.delete()
        messages.success(request, "Calificacion eliminada correctamente")
        return redirect('events')
    
    return redirect('events')

@login_required
def user_rating_list(request):
    ratings = Rating.objects.filter(user=request.user)
    return render(request, "app/rating/rating_list.html", {"ratings": ratings})
