from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.contrib.auth.models import User
from django.contrib import messages
from django.shortcuts import redirect
from django.core.exceptions import PermissionDenied
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from accounts.mixins import EngineerRequiredMixin

class SettingsView(LoginRequiredMixin, EngineerRequiredMixin, TemplateView):
    template_name = "settings/settings.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Fetch all supervisor users
        context['supervisors'] = User.objects.filter(profile__role='supervisor')
        return context

    def post(self, request, *args, **kwargs):
        # Verify if user has Engineer role
        is_engineer = getattr(request.user, 'is_superuser', False) or (
            hasattr(request.user, 'profile') and request.user.profile.role == 'engineer'
        )
        
        action = request.POST.get('action')

        if action == 'update_profile':
            request.user.first_name = request.POST.get('first_name', '').strip()
            request.user.last_name = request.POST.get('last_name', '').strip()
            request.user.email = request.POST.get('email', '').strip()
            request.user.save(update_fields=['first_name', 'last_name', 'email'])
            messages.success(request, 'Profile updated successfully.')
            return redirect('settings:index')

        if action == 'change_password':
            password = request.POST.get('password', '')
            confirmation = request.POST.get('password_confirmation', '')
            if password != confirmation:
                messages.error(request, 'Passwords do not match.')
                return redirect('settings:index')
            try:
                validate_password(password, request.user)
            except ValidationError as error:
                messages.error(request, ' '.join(error.messages))
                return redirect('settings:index')
            request.user.set_password(password)
            request.user.save(update_fields=['password'])
            messages.success(request, 'Password updated. Please sign in again.')
            return redirect('accounts:login')
        
        if action == 'create_supervisor':
            if not is_engineer:
                raise PermissionDenied("Only engineers can register new supervisors.")
                
            username = request.POST.get('username')
            email = request.POST.get('email')
            password = request.POST.get('password')
            
            if not username or not password:
                messages.error(request, "Username and password are required.")
                return redirect('settings:index')
            try:
                validate_password(password)
            except ValidationError as error:
                messages.error(request, ' '.join(error.messages))
                return redirect('settings:index')
                
            if User.objects.filter(username=username).exists():
                messages.error(request, f"User with username '{username}' already exists.")
                return redirect('settings:index')
                
            # Create user. The post_save signal automatically configures profile to 'supervisor'.
            new_user = User.objects.create_user(username=username, email=email, password=password)
            messages.success(request, f"Supervisor '{username}' registered successfully!")
            return redirect('settings:index')
            
        messages.info(request, "Settings updated successfully!")
        return redirect('settings:index')
