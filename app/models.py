from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


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