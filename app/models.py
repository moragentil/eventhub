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
        ("LOW", "Low"),
        ("MEDIUM", "Medium"),
        ("HIGH", "High"),
    ]

    user = models.ManyToManyField(User, on_delete=models.CASCADE, related_name="notifications")
    title = models.CharField(max_length=200)
    message = models.TextField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)
    priority = models.CharField(
        max_length=6,
        choices=PRIORITY_CHOICES,
        default="LOW",
    )
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"Notification for {self.title} - {self.priority} by {self.user.username}"
    
    @classmethod
    def validate(cls, title, message):
        errors = {}

        if title == "":
            errors["title"] = "Por favor ingrese un titulo"

        if message == "":
            errors["message"] = "Por favor ingrese un mensaje"

        return errors

    @classmethod
    def new(cls, users, title, message, priority="LOW"):
        errors = Notification.validate(title, message)

        if errors:
            return False, errors

        notification = cls.objects.create(
            title=title,
            message=message,
            created_at=timezone.now(),
            priority=priority,
            is_read=False,
        )
        
        notification.users.set(users)
        notification.save()

        return True, notification
    
    @classmethod
    def update(cls, notification_id, title=None, message=None, priority=None):
        try:
            notification = cls.objects.get(id=notification_id)
        except cls.DoesNotExist:
            return False, {"error": "Notificación no encontrada"}

        if title:
            notification.title = title
        if message:
            notification.message = message
        if priority:
            notification.priority = priority

        notification.save()
        return True, notification
    
    @classmethod
    def delete_notification(cls, notification_id):
        try:
            notification = cls.objects.get(id=notification_id)
            notification.delete()
            return True, None
        except cls.DoesNotExist:
            return False, {"error": "Notificación no encontrada"}