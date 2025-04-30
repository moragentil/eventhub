from django.core.exceptions import PermissionDenied

def organizer_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not getattr(request.user, 'is_organizer', False):
            raise PermissionDenied()
        return view_func(request, *args, **kwargs)
    return wrapper