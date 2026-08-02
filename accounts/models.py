from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class UserRole(models.TextChoices):
    ENGINEER = "engineer", "Engineer"
    SUPERVISOR = "supervisor", "Supervisor"

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    role = models.CharField(
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.ENGINEER
    )

    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        role = UserRole.ENGINEER if instance.is_superuser else UserRole.SUPERVISOR
        UserProfile.objects.get_or_create(user=instance, defaults={'role': role})

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if not hasattr(instance, 'profile'):
        role = UserRole.ENGINEER if instance.is_superuser else UserRole.SUPERVISOR
        UserProfile.objects.create(user=instance, role=role)
    else:
        instance.profile.save()
