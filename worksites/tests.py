from datetime import date

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from employees.models import Employee
from .models import Worksite, WorksiteStatus


class WorksiteWorkflowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("engineer", password="test-password")
        self.user.profile.role = "engineer"
        self.user.profile.save(update_fields=["role"])
        self.client.force_login(self.user)

    def payload(self, **overrides):
        data = {
            "name": "Riverside Apartments",
            "client": "Riverside Developers",
            "location": "Pune, Maharashtra",
            "supervisor": str(self.user.pk),
            "budget": "2500000.00",
            "start_date": "2026-07-01",
            "status": WorksiteStatus.ACTIVE,
            "progress": "15",
        }
        data.update(overrides)
        return data

    def test_authenticated_user_can_create_and_update_worksite(self):
        response = self.client.post(reverse("worksites:create"), self.payload())
        self.assertRedirects(response, reverse("worksites:list"))
        site = Worksite.objects.get(name="Riverside Apartments")
        self.assertEqual(site.progress, 15)
        self.assertEqual(site.supervisor, self.user)

        response = self.client.post(
            reverse("worksites:edit", args=[site.pk]),
            self.payload(progress="100", status=WorksiteStatus.COMPLETED),
        )
        self.assertRedirects(response, reverse("worksites:list"))
        site.refresh_from_db()
        self.assertEqual(site.status, WorksiteStatus.COMPLETED)
        self.assertEqual(site.progress, 100)

    def test_deleting_worksite_unassigns_its_employees(self):
        site = Worksite.objects.create(
            name="Oak Plaza", client="Oak Ltd", location="Delhi", budget=1000,
            start_date=date(2026, 1, 1),
        )
        employee = Employee.objects.create(
            name="Asha Singh", role="Mason", worksite=site, phone="9999999999",
            email="asha@example.com", wage=500,
        )
        response = self.client.post(reverse("worksites:delete", args=[site.pk]))
        self.assertRedirects(response, reverse("worksites:list"))
        employee.refresh_from_db()
        self.assertIsNone(employee.worksite)
