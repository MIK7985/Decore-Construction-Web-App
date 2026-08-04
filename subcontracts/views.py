import hashlib
import urllib.parse
from decimal import Decimal

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models import Sum
from django.http import JsonResponse, HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views import View
from django.views.generic import ListView

from accounts.mixins import EngineerRequiredMixin
from worksites.models import Worksite
from payments.models import Payment
from reports.pdf_generator import generate_subcontract_receipt_pdf
from .models import Subcontract, SubcontractCategory, SubcontractPayment, SubcontractStatus
import re

def validate_indian_phone(phone):
    if not phone:
        return ""
    clean_p = re.sub(r'[\s\-\+]', '', phone)
    if clean_p.startswith('91') and len(clean_p) == 12:
        clean_p = clean_p[2:]
    if not re.match(r'^[6-9]\d{9}$', clean_p):
        return None
    return clean_p


def get_subcontract_payment_token(payment_pk):
    return hashlib.sha256(f"subcontract-payment-{payment_pk}-{settings.SECRET_KEY}".encode()).hexdigest()[:16]


class SubcontractListView(LoginRequiredMixin, EngineerRequiredMixin, ListView):
    model = Subcontract
    template_name = "subcontracts/subcontract_list.html"
    context_object_name = "subcontracts"

    def get_queryset(self):
        qs = Subcontract.objects.select_related("worksite").prefetch_related("payments").all()
        
        user = self.request.user
        if hasattr(user, 'profile') and user.profile.role == 'supervisor':
            qs = qs.filter(worksite__supervisor=user)

        worksite_id = self.request.GET.get("worksite")
        trade = self.request.GET.get("trade")
        status = self.request.GET.get("status")

        if worksite_id:
            qs = qs.filter(worksite_id=worksite_id)
        if trade:
            qs = qs.filter(trade=trade)
        if status:
            qs = qs.filter(status=status)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        if hasattr(user, 'profile') and user.profile.role == 'supervisor':
            worksites = Worksite.objects.filter(supervisor=user)
        else:
            worksites = Worksite.objects.all()

        subcontracts = context["subcontracts"]
        total_contract_val = sum(s.contract_amount for s in subcontracts)
        total_paid_val = sum(s.paid_amount for s in subcontracts)
        total_pending_val = max(total_contract_val - total_paid_val, Decimal("0.00"))

        context["worksites"] = worksites
        context["trade_choices"] = SubcontractCategory.choices
        context["status_choices"] = SubcontractStatus.choices
        context["payment_method_choices"] = Payment.Method.choices
        context["stats"] = {
            "total_count": len(subcontracts),
            "total_contract_value": total_contract_val,
            "total_paid": total_paid_val,
            "total_pending": total_pending_val
        }
        return context


class SubcontractCreateView(LoginRequiredMixin, EngineerRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        worksite_id = request.POST.get("worksite_id")
        contractor_name = request.POST.get("contractor_name", "").strip()
        phone = request.POST.get("phone", "").strip()
        if phone:
            clean_phone = validate_indian_phone(phone)
            if not clean_phone:
                return JsonResponse({"success": False, "error": "Please enter a valid 10-digit Indian mobile number starting with 6, 7, 8, or 9."}, status=400)
            phone = clean_phone
        trade = request.POST.get("trade", "").strip()
        title = request.POST.get("title", "").strip()
        amount_str = request.POST.get("contract_amount", "0").strip()
        start_date_str = request.POST.get("start_date")
        completion_date_str = request.POST.get("completion_date")
        notes = request.POST.get("notes", "").strip()

        if not worksite_id or not contractor_name or not title:
            return JsonResponse({"success": False, "error": "Worksite, Contractor Name, and Title are required."}, status=400)

        try:
            clean_amt = str(amount_str).replace(',', '').replace('₹', '').strip()
            contract_amount = Decimal(clean_amt)
            if contract_amount <= 0:
                return JsonResponse({"success": False, "error": "Contract amount must be greater than zero."}, status=400)
        except Exception:
            return JsonResponse({"success": False, "error": "Invalid contract amount."}, status=400)

        worksite = get_object_or_404(Worksite, pk=worksite_id)

        start_date = None
        if start_date_str:
            try:
                start_date = timezone.datetime.strptime(start_date_str, "%Y-%m-%d").date()
            except Exception:
                pass

        completion_date = None
        if completion_date_str:
            try:
                completion_date = timezone.datetime.strptime(completion_date_str, "%Y-%m-%d").date()
            except Exception:
                pass

        subcontract = Subcontract.objects.create(
            worksite=worksite,
            contractor_name=contractor_name,
            phone=phone,
            trade=trade or SubcontractCategory.OTHER,
            title=title,
            contract_amount=contract_amount,
            status=SubcontractStatus.IN_PROGRESS,
            start_date=start_date,
            completion_date=completion_date,
            notes=notes
        )

        return JsonResponse({
            "success": True,
            "message": f'Subcontract for "{contractor_name}" (₹{contract_amount:,.2f}) created successfully!'
        })


class SubcontractUpdateView(LoginRequiredMixin, EngineerRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        subcontract = get_object_or_404(Subcontract, pk=pk)
        contractor_name = request.POST.get("contractor_name", "").strip()
        phone = request.POST.get("phone", "").strip()
        trade = request.POST.get("trade", "").strip()
        title = request.POST.get("title", "").strip()
        amount_str = request.POST.get("contract_amount", "").strip()
        status = request.POST.get("status", "").strip()
        notes = request.POST.get("notes", "").strip()

        if contractor_name:
            subcontract.contractor_name = contractor_name
        if phone:
            clean_phone = validate_indian_phone(phone)
            if not clean_phone:
                return JsonResponse({"success": False, "error": "Please enter a valid 10-digit Indian mobile number starting with 6, 7, 8, or 9."}, status=400)
            subcontract.phone = clean_phone
        else:
            subcontract.phone = ""
        if trade in [c.value for c in SubcontractCategory]:
            subcontract.trade = trade
        if title:
            subcontract.title = title
        if status in [s.value for s in SubcontractStatus]:
            subcontract.status = status
        if notes:
            subcontract.notes = notes

        if amount_str:
            try:
                clean_amt = str(amount_str).replace(',', '').replace('₹', '').strip()
                amt = Decimal(clean_amt)
                if amt > 0:
                    subcontract.contract_amount = amt
            except Exception:
                pass

        subcontract.save()
        return JsonResponse({
            "success": True,
            "message": f'Subcontract "{subcontract.title}" updated successfully!'
        })


class SubcontractDeleteView(LoginRequiredMixin, EngineerRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        subcontract = get_object_or_404(Subcontract, pk=pk)
        name = subcontract.contractor_name
        subcontract.delete()
        return JsonResponse({"success": True, "message": f'Subcontract for "{name}" deleted successfully.'})


class SubcontractPaymentCreateView(LoginRequiredMixin, EngineerRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        subcontract_id = request.POST.get("subcontract_id")
        amount_str = request.POST.get("amount", "0").strip()
        payment_date_str = request.POST.get("payment_date")
        payment_method = request.POST.get("payment_method", Payment.Method.BANK_TRANSFER)
        reference_number = request.POST.get("reference_number", "").strip()
        notes = request.POST.get("notes", "").strip()

        if not subcontract_id:
            return JsonResponse({"success": False, "error": "Subcontract ID is required."}, status=400)

        try:
            clean_amt = str(amount_str).replace(',', '').replace('₹', '').strip()
            amount = Decimal(clean_amt)
            if amount <= 0:
                return JsonResponse({"success": False, "error": "Payment amount must be greater than zero."}, status=400)
        except Exception:
            return JsonResponse({"success": False, "error": "Invalid payment amount."}, status=400)

        subcontract = get_object_or_404(Subcontract, pk=subcontract_id)

        if amount > subcontract.balance_amount:
            return JsonResponse({
                "success": False,
                "error": f"Payment amount (₹{amount:,.2f}) exceeds outstanding balance of ₹{subcontract.balance_amount:,.2f}."
            }, status=400)

        payment_date = timezone.localdate()
        if payment_date_str:
            try:
                payment_date = timezone.datetime.strptime(payment_date_str, "%Y-%m-%d").date()
            except Exception:
                pass

        payment = SubcontractPayment.objects.create(
            subcontract=subcontract,
            amount=amount,
            payment_date=payment_date,
            payment_method=payment_method,
            reference_number=reference_number,
            notes=notes,
            recorded_by=request.user
        )

        if subcontract.balance_amount <= Decimal("0.00"):
            subcontract.status = SubcontractStatus.COMPLETED
            subcontract.save(update_fields=["status"])

        # Generate WhatsApp link if phone is provided
        wa_link = None
        if subcontract.phone:
            phone_clean = "".join(filter(str.isdigit, subcontract.phone))
            if len(phone_clean) == 10:
                phone_clean = "91" + phone_clean
            if phone_clean:
                token = get_subcontract_payment_token(payment.pk)
                receipt_pdf_url = request.build_absolute_uri(
                    reverse("subcontracts:payment_pdf", kwargs={"pk": payment.pk}) + f"?token={token}"
                )
                msg_text = (
                    f"Hello {subcontract.contractor_name},\n\n"
                    f"A payment disbursement of ₹{payment.amount:,.2f} for {subcontract.get_trade_display()} ({subcontract.title}) "
                    f"on worksite '{subcontract.worksite.name}' has been processed successfully!\n\n"
                    f"• Payment Method: {payment.get_payment_method_display()}\n"
                    f"• Contract Valuation: ₹{subcontract.contract_amount:,.2f}\n"
                    f"• Total Paid to Date: ₹{subcontract.paid_amount:,.2f}\n"
                    f"• Remaining Balance: ₹{subcontract.balance_amount:,.2f}\n\n"
                    f"View Official Payment Receipt PDF:\n{receipt_pdf_url}\n\n"
                    f"Thank you,\nDecore Construction Management"
                )
                wa_link = f"https://wa.me/{phone_clean}?text={urllib.parse.quote(msg_text)}"

        return JsonResponse({
            "success": True,
            "message": f"Logged disbursement of ₹{amount:,.2f} to {subcontract.contractor_name}.",
            "whatsapp_link": wa_link
        })


class SubcontractPaymentDeleteView(LoginRequiredMixin, EngineerRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        payment = get_object_or_404(SubcontractPayment, pk=pk)
        subcontract = payment.subcontract
        amt = payment.amount
        payment.delete()
        
        if subcontract.status == SubcontractStatus.COMPLETED and subcontract.balance_amount > Decimal("0.00"):
            subcontract.status = SubcontractStatus.IN_PROGRESS
            subcontract.save(update_fields=["status"])

        return JsonResponse({"success": True, "message": f"Reversed payment of ₹{amt:,.2f} for {subcontract.contractor_name}."})


class SubcontractPaymentReceiptPdfView(View):
    def get(self, request, pk, *args, **kwargs):
        if not request.user.is_authenticated:
            token = request.GET.get('token')
            expected_token = get_subcontract_payment_token(pk)
            if not token or token != expected_token:
                return HttpResponseForbidden("Access Denied: Invalid or missing secure receipt token.")

        payment = get_object_or_404(SubcontractPayment.objects.select_related("subcontract", "subcontract__worksite"), pk=pk)
        subcontract = payment.subcontract

        data = {
            'contractor_name': subcontract.contractor_name,
            'trade_display': subcontract.get_trade_display(),
            'title': subcontract.title,
            'phone': subcontract.phone,
            'worksite_name': subcontract.worksite.name,
            'payment_date': payment.payment_date.strftime("%d %b %Y"),
            'disbursed_amount': float(payment.amount),
            'payment_method': payment.get_payment_method_display(),
            'reference_number': payment.reference_number,
            'contract_amount': float(subcontract.contract_amount),
            'paid_amount': float(subcontract.paid_amount),
            'balance_amount': float(subcontract.balance_amount),
            'notes': payment.notes
        }

        pdf = generate_subcontract_receipt_pdf(data)
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="Subcontract_Receipt_{subcontract.contractor_name}_{payment.payment_date}.pdf"'
        return response
