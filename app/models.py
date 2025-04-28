from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.utils import timezone
import string
import secrets


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


class Event(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    scheduled_at = models.DateTimeField()
    organizer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="organized_events")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    @classmethod
    def validate(cls, title, description, scheduled_at):
        errors = {}

        if title == "":
            errors["title"] = "Por favor ingrese un titulo"

        if description == "":
            errors["description"] = "Por favor ingrese una descripcion"

        return errors

    @classmethod
    def new(cls, title, description, scheduled_at, organizer):
        errors = Event.validate(title, description, scheduled_at)

        if len(errors.keys()) > 0:
            return False, errors

        Event.objects.create(
            title=title,
            description=description,
            scheduled_at=scheduled_at,
            organizer=organizer,
        )

        return True, None

    def update(self, title, description, scheduled_at, organizer):
        self.title = title or self.title
        self.description = description or self.description
        self.scheduled_at = scheduled_at or self.scheduled_at
        self.organizer = organizer or self.organizer

        self.save()


def code_generator(length=100):
    characters = string.ascii_letters + string.digits
    while True:
        code = ''.join(secrets.choice(characters) for _ in range(length))
        if not Ticket.objects.filter(ticket_code=code).exists():
            return code

class TicketType(models.TextChoices):
    GENERAL = "General", "General"
    VIP = "Vip", "VIP"

class Ticket(models.Model):
    buy_date = models.DateField(auto_now_add=True)
    ticket_code = models.CharField(max_length=100, unique=True, default=code_generator)
    quantity = models.IntegerField(null=False, default=1)
    type = models.CharField(
        max_length=10,
        choices=TicketType.choices,
        default=TicketType.GENERAL,
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="tickets")
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="tickets")

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
    def update(cls, ticket_id, quantity=None):
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
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="refund_requests")
    approved = models.BooleanField(default=False)
    approval_date = models.DateField(null=True, blank=True)
    ticket_code = models.CharField(max_length=100)
    reason = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Refund request for {self.ticket_code} by {self.user.username}"
    
    @classmethod
    def new(cls, user, approved, approval_date, ticket_code, reason):
        created_at = timezone.now()
        RefundRequest.objects.create(
            user=user,
            approved=approved,
            approval_date=approval_date,
            ticket_code=ticket_code,
            reason=reason,
            created_at=created_at
        )
        return True, None
    
    def update(self, approved=None, approval_date=None, reason=None):
        self.approved = approved if approved is not None else self.approved
        self.approval_date = approval_date if approval_date is not None else self.approval_date
        self.reason = reason if reason is not None else self.reason
        self.save()

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