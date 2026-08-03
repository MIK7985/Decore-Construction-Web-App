"""
accounts views.

Phase 1 placeholder authentication views.
TODO: Wire up real authentication logic (currently uses Django's built-in
LoginView/LogoutView; no custom Engineer/Supervisor role logic is implemented
yet).
"""
from django.contrib.auth.views import LoginView as DjangoLoginView, LogoutView as DjangoLogoutView


from django.urls import reverse


class LoginView(DjangoLoginView):
    template_name = "accounts/login.html"
    redirect_authenticated_user = True

    def get_success_url(self):
        user = self.request.user
        if not user.is_superuser and hasattr(user, "profile") and user.profile.role == "supervisor":
            return reverse("attendance:sheet")
        return reverse("dashboard:index")


class LogoutView(DjangoLogoutView):
    """TODO: Add any post-logout logic (e.g. audit logging)."""
    next_page = "accounts:login"
