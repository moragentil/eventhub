from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from decimal import Decimal
import string
import secrets
import datetime


class User(AbstractUser):
    is_organizer = models.BooleanField(default=False)

    @classmethod
    def validate_new_user(cls, email, username, password, password_confirm):
        errors = {}

        if email is None:
            errors["email"] = "El email es requerido"
        elif User.objects.filter(email=email).exists():
            errors["email"] = "Ya existe un usuario con este email"

        if username is None:
            errors["username"] = "El username es requerido"
        elif User.objects.filter(username=username).exists():
            errors["username"] = "Ya existe un usuario con este nombre de usuario"

        if password is None or password_confirm is None:
            errors["password"] = "Las contraseñas son requeridas"
        elif password != password_confirm:
            errors["password"] = "Las contraseñas no coinciden"

        return errors


class Venue(models.Model):
    name = models.CharField(max_length=100)
    address = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    capacity = models.IntegerField()
    contact = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return f"Venue: {self.name}"

    @classmethod
    def validate(cls, name, address, city, capacity, contact=None):
        errors = {}

        if not name:
            errors["name"] = "El nombre es obligatorio."
        elif len(name) > 100:
            errors["name"] = "El nombre no puede exceder los 100 caracteres."
            
        if not address:
            errors["address"] = "La dirección es obligatoria."
        elif len(address) > 100:
            errors["address"] = "La dirección no puede exceder los 100 caracteres."
            
        if not city:
            errors["city"] = "La ciudad es obligatoria."
        elif len(city) > 100:
            errors["city"] = "La ciudad no puede exceder los 100 caracteres."
            
        if capacity is None:
            errors["capacity"] = "La capacidad es obligatoria."
        elif capacity <= 0:
            errors["capacity"] = "La capacidad debe ser un número mayor que cero."
            
        if contact and len(contact) > 100:
            errors["contact"] = "El contacto no puede exceder los 100 caracteres."

        return errors

    @classmethod
    def new(cls, name, address, city, capacity, contact=None):
        errors = cls.validate(name, address, city, capacity, contact)

        if errors:
            return None, errors

        venue = cls.objects.create(
            name=name,
            address=address,
            city=city,
            capacity=capacity,
            contact=contact,
        )
        return venue, None

    def update(self, name=None, address=None, city=None, capacity=None, contact=None):
        errors = self.validate(
            name or self.name,
            address or self.address,
            city or self.city,
            capacity or self.capacity,
            contact or self.contact
        )

        if errors:
            return False, errors

        self.name = name or self.name
        self.address = address or self.address
        self.city = city or self.city
        self.capacity = capacity or self.capacity
        self.contact = contact or self.contact
        self.save()
        return True, None


class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Category: {self.name}"


    @classmethod
    def validate(cls, name, description):
        errors = {}
        if not name or name.strip() == "":
            errors["name"] = "El nombre es requerido."
        if not description or description.strip() == "":
            errors["description"] = "La descripción es requerida."
        return errors

    @classmethod
    def new(cls, user, name, description, is_active=True):
        if not user.is_organizer:
            return False, {"permission": "Solo los organizadores pueden crear categorías."}

        errors = cls.validate(name, description)
        if errors:
            return False, errors

        category = cls.objects.create(
            name=name,
            description=description,
            is_active=is_active
        )
        return True, category

    def update(self, user, name=None, description=None, is_active=None):
        if not user.is_organizer:
            return False, {"permission": "Solo los organizadores pueden editar categorías."}

        self.name = name or self.name
        self.description = description or self.description
        self.is_active = is_active if is_active is not None else self.is_active
        self.save()
        return True, None

    @classmethod
    def delete_category(cls, user, category_id):
        if not user.is_organizer:
            return False, {"permission": "Solo los organizadores pueden eliminar categorías."}
        try:
            category = cls.objects.get(id=category_id)
            category.delete()
            return True, category
        except cls.DoesNotExist:
            return False, {"category": "Categoría no encontrada."}


class Event(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    scheduled_at = models.DateTimeField()
    organizer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="organized_events")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    price_general = models.DecimalField(max_digits=8, decimal_places=2, null=False, default=Decimal('50.00'))
    price_vip = models.DecimalField(max_digits=8, decimal_places=2, null=False, default=Decimal('100.00'))
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE, related_name="events", null=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name="events")


    def __str__(self):
        return self.title

    @classmethod
    def validate(cls, title, description, scheduled_at, price_general, price_vip, category):
        errors = {}

        if title == "":
            errors["title"] = "Por favor ingrese un titulo"

        if description == "":
            errors["description"] = "Por favor ingrese una descripcion"

        if price_general is None:
            errors["price_general"] = "El precio general es requerido."
        elif price_general <= 0:
            errors["price_general"] = "El precio general debe ser un número mayor que cero."

        if price_vip is None:
            errors["price_vip"] = "El precio VIP es requerido."
        elif price_vip <= 0:
            errors["price_vip"] = "El precio VIP debe ser un número mayor que cero."

        if price_vip <= price_general:
            errors["price_vip"] = "El precio VIP debe ser un número mayor que el general"
            
        if category is None:
            errors["category"] = "Debe seleccionar una categoría."
        
        return errors

    @classmethod
    def new(cls, title, description, scheduled_at, organizer, price_general, price_vip, venue, category):
        errors = Event.validate(title, description, scheduled_at, price_general, price_vip, category)

        if len(errors.keys()) > 0:
            return False, errors

        Event.objects.create(
            title=title,
            description=description,
            scheduled_at=scheduled_at,
            organizer=organizer,
            price_general=price_general,
            price_vip=price_vip,
            venue=venue,
            category=category
        )

        return True, {}

    def update(self, title, description, scheduled_at, organizer, price_general, price_vip, venue, category):
        errors = self.validate(title or self.title, description or self.description,
                            scheduled_at or self.scheduled_at,
                            price_general or self.price_general,
                            price_vip or self.price_vip,
                            category or self.category)

        if errors:
            return False, errors

        if title is not None:
            self.title = title
        if description is not None:
            self.description = description
        if scheduled_at is not None:
            self.scheduled_at = scheduled_at
        if organizer is not None:
            self.organizer = organizer
        if price_general is not None:
            self.price_general = price_general
        if price_vip is not None:
            self.price_vip = price_vip
        if venue is not None:
            self.venue = venue
        if category is not None:
            self.category = category

        self.save()
        return True, None


def code_generator(length=20):
    characters = string.ascii_letters + string.digits
    while True:
        code = ''.join(secrets.choice(characters) for _ in range(length))
        if not Ticket.objects.filter(ticket_code=code).exists():
            return code


class TicketType(models.TextChoices):
    GENERAL = "General", "General"
    VIP = "VIP", "VIP"


class Ticket(models.Model):
    buy_date = models.DateTimeField(auto_now_add=True)
    ticket_code = models.CharField(max_length=20, unique=True, default=code_generator)
    quantity = models.IntegerField(null=False, default=1)
    type = models.CharField(
        max_length=10,
        choices=TicketType.choices,
        default=TicketType.GENERAL,
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="tickets")
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="tickets")
    used = models.BooleanField(default=False) 

    def __str__(self):
        return f"Ticket for {self.event.title} by {self.user.username}"

    @classmethod
    def validate(cls, quantity, type, event):
        errors = {}

        if quantity is None:
            errors["quantity"] = "La cantidad es requerida."
        elif not isinstance(quantity, int):
            errors["quantity"] = "La cantidad debe ser un número entero."
        elif quantity <= 0:
            errors["quantity"] = "La cantidad debe ser un número mayor que cero."


        if type is None:
            errors["type"] = "Debe seleccionar un tipo de Ticket."
        elif type not in TicketType.values:
            errors["type"] = "Tipo de Ticket no válido."

        if event is None:
            errors["event"] = "Debe seleccionar un Evento."


        return errors

    @classmethod
    def new(cls, quantity, type, user, event):
        errors = Ticket.validate(quantity, type, event)

        if errors:
            return False, errors

        ticket = cls.objects.create(
            buy_date = timezone.now(),
            ticket_code = code_generator(),
            quantity = quantity,
            type = type,
            user = user,
            event = event
        )

        return True, ticket

    @classmethod
    def update(cls, ticket_id, quantity=None, type=None, used=None):
        try:
            ticket = cls.objects.get(id=ticket_id)
            
            errors = {}

            if quantity is not None:
                if not isinstance(quantity, int):
                    errors["quantity"] = "La cantidad debe ser un número entero."
                elif quantity <= 0:
                    errors["quantity"] = "La cantidad debe ser un número mayor a cero."
                else:
                    ticket.quantity = quantity
            

            if type is not None:
                if type not in TicketType.values:
                    errors["type"] = "Tipo de Ticket no válido."
                else:
                    ticket.type = type


            if used is not None:
                if isinstance(used, str):
                    used = used.lower() == "true"
                elif not isinstance(used, bool):
                    used = False  
                ticket.used = used

            if errors:
                return False, errors
            
            ticket.save()
            return True, ticket

        except cls.DoesNotExist:
            return False, {"ticket": "Ticket no encontrado."}
        
    
    @classmethod 
    def delete_ticket(cls, ticket_id):
        try:
            ticket = cls.objects.get(id=ticket_id)
            ticket.delete()
            return True, ticket
        
        except cls.DoesNotExist:
            return False, {"ticket": "Ticket no encontrado."}


class RefundRequest(models.Model):
    STATUS_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('aprobado', 'Aprobado'),
        ('rechazado', 'Rechazado'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="refund_requests")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pendiente')
    approval_date = models.DateField(null=True, blank=True)
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="refund_requests")
    reason = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Refund request for {self.ticket.ticket_code} by {self.user.username}"
    
    @classmethod
    def validate(cls, reason, ticket, existing_instance=None):
        errors = {}

        if not reason or len(reason.strip().split()) < 1:
            errors["reason"] = "El motivo es requerido."

        if ticket is None:
            errors["ticket"] = "El ticket con el código ingresado no existe."
        else:
            if RefundRequest.objects.filter(ticket=ticket).exclude(pk=getattr(existing_instance, 'pk', None)).exists():
                errors["ticket"] = "Ya se ha solicitado un reembolso para ese ticket."
            elif ticket.used:
                errors["ticket"] = "El ticket ya ha sido usado y no puede ser reembolsado."
            elif ticket.event.scheduled_at + datetime.timedelta(days=30) < timezone.now():
                errors["ticket"] = "Han pasado más de 30 días desde el evento. No es posible solicitar reembolso."
        
        return errors
    
    @classmethod
    def new(cls, user, status, approval_date, ticket, reason):
        errors = cls.validate(reason, ticket)

        if errors:
            return None, errors

        refund = cls.objects.create(
            user=user,
            status=status,
            approval_date=approval_date,
            ticket=ticket,
            reason=reason,
            created_at=timezone.now()
        )
        return refund, None
    
    def update(self, status=None, approval_date=None, reason=None):
        errors = self.validate(reason or self.reason, self.ticket, existing_instance=self)

        if errors:
            return False, errors

        self.status = status if status is not None else self.status
        self.approval_date = approval_date if approval_date is not None else self.approval_date
        self.reason = reason if reason is not None else self.reason
        self.save()
        return True, None


class Comment(models.Model):
    title = models.CharField(max_length=200)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="comments")
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="comments")

    def __str__(self):
        return f"Comment by {self.user.username} on {self.event.title}"
    
    @classmethod
    def validate(cls, title, text, event):
        errors = {}

        if title == "":
            errors["title"] = "Por favor ingrese un titulo"

        if text == "":
            errors["text"] = "Por favor ingrese un comentario"

        if event is None:
            errors["event"] = "Debe seleccionar un Evento."

        return errors
    
    @classmethod
    def new(cls, title, text, user, event):
        errors = Comment.validate(title, text, event)

        if errors:
            return False, errors
        
        comment = cls.objects.create(
            title=title,
            text=text,
            user=user,
            event=event,
            created_at=timezone.now()
        )

        return True, comment
    

    def update(self, title=None, text=None):
        if title is not None:
            self.title = title
        if text is not None:
            self.text = text

        self.save()

    @classmethod
    def delete_comment(cls, comment_id, user):
        try:
            comment = cls.objects.get(id=comment_id)
            if comment.user == user or user.is_organizer:
                comment.delete()
                return True, comment
            else:
                return False, {"authorization": "No tienes permiso para eliminar este comentario."}
        
        except cls.DoesNotExist:
            return False, {"comment": "Comentario no encontrado."}
        

class Rating(models.Model):
    title = models.CharField(max_length=200)
    text = models.TextField()
    rating = models.IntegerField()
    created_at = models.DateTimeField()
    user =  models.ForeignKey(User, on_delete=models.CASCADE, related_name="rating")
    event =  models.ForeignKey(Event, on_delete=models.CASCADE, related_name="rating")

    def __str__(self):
        return f"Rating for {self.event.title} by {self.user.username}"
    
    @classmethod
    def validate(cls,title,text,rating,event):
        errors = {}

        if title is None:
            errors["title"] = "Por favor ingrese un titulo"
        if text is None:
            errors["text"] = "Por favor ingrese un titulo"
        if rating is None:
            errors["rating"] = "Por favor ingrese un titulo"
        if event is None:
            errors["event"] = "Por favor ingrese un titulo"

        return errors
    
    @classmethod
    def new(cls,title,text,rating,created_at,user,event):
        errors = Rating.validate(title,text,rating,event)

        if errors:
            return False,errors 
        
        rating = cls.objects.create(
            title= title,
            text= text,
            rating= rating,
            created_at= timezone.now(),
            user= user,
            event= event
        )

        return True, rating
    
    def update(self,title,text,rating):
        errors = self.validate(title, text, rating, self.event)

        if errors:
            return False, errors
        
        self.title = title
        self.text = text
        self.rating = rating
        self.save()

        return True, self
    
    @classmethod
    def delete_rating(cls,id_rating,user):
        try:
            rating = cls.objects.get(id=id_rating)
            if rating.user == user:
                rating.delete()
                return True, {"message": "Rating eliminado"}
        except cls.DoesNotExist:
            return False, {"rating": "Rating no encontrado"}

class Notification(models.Model):
    PRIORITY_CHOICES = [
        ("Low", "Baja"),
        ("Medium", "Media"),
        ("High", "Alta"),
    ]

    user = models.ManyToManyField(User, related_name="notifications")
    title = models.CharField(max_length=50)
    message = models.TextField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)
    priority = models.CharField(
        max_length=6,
        choices=PRIORITY_CHOICES,
        default="Baja",
    )
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"Notification for {self.title} - {self.priority}"
    
    @classmethod
    def validate(cls, title, message, users=None, priority=None):
        errors = {}

        if not title or title.strip() == "":
            errors["title"] = "Por favor ingrese un título"
        elif len(title.strip()) > 50:
            errors["title"] = "El título no puede tener más de 50 caracteres"

        if not message or message.strip() == "":
            errors["message"] = "Por favor ingrese un mensaje"
        elif len(message.strip()) > 500:
            errors["message"] = "El mensaje no puede tener más de 500 caracteres"

        if users is not None:
            if not users.exists():
                errors["recipient_type"] = "Debe seleccionar al menos un destinatario válido"

        if priority is not None:
            valid_priorities = [choice[0] for choice in cls.PRIORITY_CHOICES]
            if priority not in valid_priorities:
                errors["priority"] = "La prioridad seleccionada no es válida"

        return errors

    @classmethod
    def new(cls, users, title, message, priority="Low"):
        errors = cls.validate(title, message, users, priority)

        if errors:
            return False, errors

        notification = cls.objects.create(
            title=title,
            message=message,
            priority=priority,
            is_read=False,
        )
        notification.user.set(users)

        return True, notification
    
    @classmethod
    def update(cls, notification_id, title=None, message=None, priority=None, users=None):
        try:
            notification = cls.objects.get(id=notification_id)
        except cls.DoesNotExist:
            return False, {"error": "Notificación no encontrada"}

        errors = cls.validate(
            title if title is not None else notification.title,
            message if message is not None else notification.message,
            users if users is not None else notification.user.all(),
            priority if priority is not None else notification.priority,
        )

        if errors:
            return False, errors

        if title is not None:
            notification.title = title
        if message is not None:
            notification.message = message
        if priority is not None:
            notification.priority = priority
        notification.save()

        if users is not None:
            notification.user.set(users)

        return True, notification
    
    @classmethod
    def delete_notification(cls, notification_id):
        try:
            notification = cls.objects.get(id=notification_id)
            notification.delete()
            return True, None
        except cls.DoesNotExist:
            return False, {"error": "Notificación no encontrada"}
