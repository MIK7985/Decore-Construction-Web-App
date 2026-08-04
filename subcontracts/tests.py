from decimal import Decimal
from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone
from worksites.models import Worksite
from .models import Subcontract, SubcontractCategory, SubcontractPayment, SubcontractStatus


class SubcontractModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testengineer", password="password")
        self.worksite = Worksite.objects.create(
            name="Villa Residency",
            client="Rajesh Kumar",
            location="Kochi",
            budget=Decimal("500000.00"),
            start_date=timezone.now().date()
        )

    def test_subcontract_creation_and_balance_calculation(self):
        subcontract = Subcontract.objects.create(
            worksite=self.worksite,
            contractor_name="Apex Electricals",
            trade=SubcontractCategory.ELECTRICAL,
            title="Complete Wiring",
            contract_amount=Decimal("100000.00")
        )
        self.assertEqual(subcontract.paid_amount, Decimal("0.00"))
        self.assertEqual(subcontract.balance_amount, Decimal("100000.00"))
        self.assertEqual(subcontract.progress_percent, 0.0)

        payment = SubcontractPayment.objects.create(
            subcontract=subcontract,
            amount=Decimal("40000.00"),
            recorded_by=self.user
        )

        self.assertEqual(subcontract.paid_amount, Decimal("40000.00"))
        self.assertEqual(subcontract.balance_amount, Decimal("60000.00"))
        self.assertEqual(subcontract.progress_percent, 40.0)

        self.assertEqual(self.worksite.subcontract_cost, Decimal("40000.00"))
        self.assertEqual(self.worksite.total_spend, Decimal("40000.00"))
