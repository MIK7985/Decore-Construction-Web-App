from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from django.contrib.messages import get_messages
from accounts.models import UserProfile

class SettingsTestCase(TestCase):
    def setUp(self):
        # Create engineer user (is_superuser=True automatically triggers Engineer role in post_save)
        self.user = User.objects.create_superuser(username="engineer1", password="password123")
        self.client.login(username="engineer1", password="password123")
        self.url = reverse("settings:index")

    def test_profile_update(self):
        response = self.client.post(self.url, {
            "action": "update_profile",
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@decore.com"
        })
        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "John")
        self.assertEqual(self.user.last_name, "Doe")
        self.assertEqual(self.user.email, "john.doe@decore.com")

    def test_change_password_mismatch(self):
        response = self.client.post(self.url, {
            "action": "change_password",
            "password": "newpassword123",
            "password_confirmation": "differentpassword"
        })
        self.assertEqual(response.status_code, 302)
        
        # Verify message
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("Passwords do not match." in str(m) for m in messages))

    def test_change_password_validation_error(self):
        # Passwords too short or too common
        response = self.client.post(self.url, {
            "action": "change_password",
            "password": "short",
            "password_confirmation": "short"
        })
        self.assertEqual(response.status_code, 302)
        
        # Verify validation error is raised
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("too short" in str(m).lower() for m in messages))

    def test_change_password_success(self):
        response = self.client.post(self.url, {
            "action": "change_password",
            "password": "SecuredNewPassword123!",
            "password_confirmation": "SecuredNewPassword123!"
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("accounts:login"))
        
        # Verify user can log in with new password
        self.client.logout()
        login_success = self.client.login(username="engineer1", password="SecuredNewPassword123!")
        self.assertTrue(login_success)
