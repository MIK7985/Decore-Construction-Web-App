"""
accounts views.

Phase 1 placeholder authentication views.
TODO: Wire up real authentication logic (currently uses Django's built-in
LoginView/LogoutView; no custom Engineer/Supervisor role logic is implemented
yet).
"""
from django.contrib.auth.views import LoginView as DjangoLoginView, LogoutView as DjangoLogoutView


class LoginView(DjangoLoginView):
    """TODO: Customize authentication form / role redirect logic."""
    template_name = "accounts/login.html"
    redirect_authenticated_user = True


class LogoutView(DjangoLogoutView):
    """TODO: Add any post-logout logic (e.g. audit logging)."""
    next_page = "accounts:login"
