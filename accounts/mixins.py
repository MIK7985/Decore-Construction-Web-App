from django.core.exceptions import PermissionDenied


class EngineerRequiredMixin:
    """Restrict operational changes to engineers and superusers."""

    def dispatch(self, request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)
        if user.is_superuser or (hasattr(user, "profile") and user.profile.role == "engineer"):
            return super().dispatch(request, *args, **kwargs)
        raise PermissionDenied("Only engineers can make this change.")
