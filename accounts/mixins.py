from django.shortcuts import redirect
from django.urls import reverse


class EngineerRequiredMixin:
    """Restrict operational views and management to engineers and superusers. Redirect supervisors to attendance."""

    def dispatch(self, request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)
        if user.is_superuser or (hasattr(user, "profile") and user.profile.role == "engineer"):
            return super().dispatch(request, *args, **kwargs)
        # Supervisors are strictly limited to Attendance
        return redirect(reverse("attendance:sheet"))

