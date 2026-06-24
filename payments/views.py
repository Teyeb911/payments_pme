import random
from decimal import Decimal, InvalidOperation

import requests
from django.core.cache import cache
from django.db import transaction
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views.generic import TemplateView
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.transactions.models import Transaction
from apps.users.models import User
from apps.wallets.models import Wallet
from core.email import send_email_async
from .models import MerchantPartner, PaymentRequest, SubscriptionPlan


def get_partner_from_api_key(request):
    api_key = request.headers.get("X-API-Key")
    if not api_key:
        return None
    try:
        return MerchantPartner.objects.get(api_key=api_key)
    except MerchantPartner.DoesNotExist:
        return None


def get_wallet_for_user(user):
    wallet_field_names = {field.name for field in Wallet._meta.fields}
    if "user" in wallet_field_names:
        return Wallet.objects.get(user=user)
    return Wallet.objects.get(commercant=user)


def serialize_plan(plan):
    return {
        "id": str(plan.id),
        "name": plan.name,
        "amount": str(plan.amount),
        "period": plan.period,
        "is_active": plan.is_active,
    }


def serialize_partner_payment(payment):
    return {
        "payment_id": str(payment.id),
        "payer_email": payment.payer.email if payment.payer else None,
        "plan_name": payment.plan.name,
        "amount": str(payment.plan.amount),
        "status": payment.status,
        "reference": payment.reference,
        "created_at": str(payment.created_at),
        "paid_at": str(payment.paid_at),
    }


def parse_bool(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ("1", "true", "yes", "on")
    return bool(value)


class CreatePaymentView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        partner = get_partner_from_api_key(request)
        if partner is None:
            return Response({"error": "Invalid API key"}, status=status.HTTP_401_UNAUTHORIZED)
        if not partner.is_active:
            return Response({"error": "Partner inactive"}, status=status.HTTP_403_FORBIDDEN)

        required_fields = ["plan_id", "callback_url", "reference"]
        missing_fields = [field for field in required_fields if not request.data.get(field)]
        if missing_fields:
            return Response(
                {"error": f"Missing required fields: {', '.join(missing_fields)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            plan = SubscriptionPlan.objects.get(id=request.data["plan_id"], partner=partner)
        except (SubscriptionPlan.DoesNotExist, ValueError):
            return Response({"error": "Plan introuvable"}, status=status.HTTP_404_NOT_FOUND)

        if not plan.is_active:
            return Response({"error": "Plan inactif"}, status=status.HTTP_400_BAD_REQUEST)

        payment = PaymentRequest.objects.create(
            partner=partner,
            plan=plan,
            description=f"Abonnement {plan.name} - {plan.period}",
            callback_url=request.data["callback_url"],
            reference=request.data["reference"],
            status=PaymentRequest.Status.PENDING,
        )

        return Response(
            {
                "payment_id": str(payment.id),
                "payment_url": f"https://trackpay.mr/pay/{payment.id}",
                "plan_name": plan.name,
                "amount": str(plan.amount),
                "expires_in": 900,
            },
            status=status.HTTP_201_CREATED,
        )


class PaymentPageView(TemplateView):
    template_name = "payments/pay.html"

    def get(self, request, payment_id):
        payment = get_object_or_404(PaymentRequest, id=payment_id)
        if payment.status != PaymentRequest.Status.PENDING:
            return render(request, "payments/expired.html")
        return render(
            request,
            self.template_name,
            {
                "payment_id": payment.id,
                "amount": payment.amount,
                "description": payment.description,
                "partner_name": payment.partner.name,
            },
        )


class SendOTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, payment_id):
        payment = get_object_or_404(PaymentRequest, id=payment_id)
        if payment.status != PaymentRequest.Status.PENDING:
            return Response(
                {"error": "Payment expired or already completed"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        email = request.data.get("email")
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {
                    "error": "Aucun compte TrackPay trouvé avec cet email.",
                    "action": "Créez votre compte sur trackpay.mr",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        if str(user.kyc_status).upper() != "VERIFIED":
            return Response(
                {"error": "Vérification KYC requise pour effectuer un paiement."},
                status=status.HTTP_403_FORBIDDEN,
            )

        otp = str(random.randint(100000, 999999))
        cache.set(f"otp_{payment_id}_{email}", otp, timeout=300)

        send_email_async(
            email,
            "TrackPay — Code de confirmation de paiement",
            "Bonjour,\n\n"
            "Votre code de confirmation pour le paiement de "
            f"{payment.amount} MRU est :\n\n"
            f"{otp}\n\n"
            "Ce code est valable 5 minutes.\n"
            "Si vous n'êtes pas à l'origine de cette demande, "
            "ignorez cet email.\n\n"
            "TrackPay",
        )

        return Response({"message": "Code envoyé à votre email."}, status=status.HTTP_200_OK)


class ConfirmPaymentView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, payment_id):
        payment = get_object_or_404(PaymentRequest, id=payment_id)
        if payment.status != PaymentRequest.Status.PENDING:
            return Response(
                {"error": "Payment expired or already completed"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        email = request.data.get("email")
        otp = request.data.get("otp")
        user = get_object_or_404(User, email=email)

        cache_key = f"otp_{payment_id}_{email}"
        stored = cache.get(cache_key)
        if stored is None:
            return Response({"error": "Code expiré."}, status=status.HTTP_400_BAD_REQUEST)
        if stored != otp:
            return Response({"error": "Code incorrect."}, status=status.HTTP_400_BAD_REQUEST)

        wallet = get_wallet_for_user(user)
        if wallet.balance < payment.amount:
            return Response({"error": "Solde insuffisant."}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            wallet.balance -= payment.amount
            wallet.save()

            partner = payment.partner
            partner.wallet.balance += payment.amount
            partner.wallet.save()

            payment.status = PaymentRequest.Status.COMPLETED
            payment.payer = user
            payment.paid_at = timezone.now()
            payment.save()

            Transaction.objects.create(
                commercant=user,
                wallet_expediteur=wallet,
                wallet_recepteur=partner.wallet,
                montant=payment.amount,
                type=Transaction.Type.EXTERNE,
                statut=Transaction.Statut.SUCCESS,
                description=f"Paiement {payment.plan.name} - {payment.partner.name}",
            )
            Transaction.objects.create(
                commercant=partner.wallet.commercant,
                wallet_expediteur=wallet,
                wallet_recepteur=partner.wallet,
                montant=payment.amount,
                type=Transaction.Type.EXTERNE,
                statut=Transaction.Statut.SUCCESS,
                description=f"Abonnement {payment.plan.name} reçu de {user.email}",
            )

        cache.delete(cache_key)

        try:
            requests.post(
                payment.callback_url,
                json={
                    "payment_id": str(payment.id),
                    "status": "COMPLETED",
                    "amount": str(payment.plan.amount),
                    "reference": payment.reference,
                    "subscription_type": payment.plan.name,
                    "subscription_period": payment.plan.period,
                    "payer_email": user.email,
                    "timestamp": str(payment.paid_at),
                },
                headers={"X-Webhook-Secret": payment.partner.webhook_secret},
                timeout=5,
            )
        except requests.RequestException:
            pass

        return Response(
            {"status": "COMPLETED", "message": "Paiement effectué avec succès."},
            status=status.HTTP_200_OK,
        )


class PaymentStatusView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, payment_id):
        partner = get_partner_from_api_key(request)
        if partner is None:
            return Response({"error": "Invalid API key"}, status=status.HTTP_401_UNAUTHORIZED)

        payment = get_object_or_404(PaymentRequest, id=payment_id, partner=partner)
        return Response(
            {
                "payment_id": str(payment.id),
                "status": payment.status,
                "amount": str(payment.amount),
                "reference": payment.reference,
                "paid_at": str(payment.paid_at),
            },
            status=status.HTTP_200_OK,
        )


class PartnerDashboardView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        partner = get_partner_from_api_key(request)
        if partner is None:
            return Response({"error": "Invalid API key"}, status=status.HTTP_401_UNAUTHORIZED)

        payments = PaymentRequest.objects.filter(partner=partner).select_related("payer", "plan")
        completed_payments = [
            payment for payment in payments if payment.status == PaymentRequest.Status.COMPLETED
        ]
        recent_payments = payments.order_by("-created_at")[:5]

        return Response(
            {
                "partner_name": partner.name,
                "wallet_balance": str(partner.wallet.balance),
                "total_payments": len(completed_payments),
                "total_revenue": str(sum((payment.amount for payment in completed_payments), Decimal("0"))),
                "pending_payments": payments.filter(status=PaymentRequest.Status.PENDING).count(),
                "recent_payments": [
                    {
                        "payer_email": payment.payer.email if payment.payer else None,
                        "plan_name": payment.plan.name,
                        "amount": str(payment.amount),
                        "status": payment.status,
                        "date": str(payment.paid_at or payment.created_at),
                    }
                    for payment in recent_payments
                ],
            },
            status=status.HTTP_200_OK,
        )


class PartnerCredentialsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        partner = get_partner_from_api_key(request)
        if partner is None:
            return Response({"error": "Invalid API key"}, status=status.HTTP_401_UNAUTHORIZED)

        return Response(
            {
                "api_key": partner.api_key,
                "webhook_secret": partner.webhook_secret,
                "gateway_endpoint": "https://trackpay.mr/api/payments/create/",
            },
            status=status.HTTP_200_OK,
        )


class PartnerPlansView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        partner = get_partner_from_api_key(request)
        if partner is None:
            return Response({"error": "Invalid API key"}, status=status.HTTP_401_UNAUTHORIZED)

        plans = partner.plans.order_by("-created_at")
        return Response([serialize_plan(plan) for plan in plans], status=status.HTTP_200_OK)

    def post(self, request):
        partner = get_partner_from_api_key(request)
        if partner is None:
            return Response({"error": "Invalid API key"}, status=status.HTTP_401_UNAUTHORIZED)

        required_fields = ["name", "amount", "period"]
        missing_fields = [field for field in required_fields if not request.data.get(field)]
        if missing_fields:
            return Response(
                {"error": f"Missing required fields: {', '.join(missing_fields)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            amount = Decimal(str(request.data["amount"]))
        except (InvalidOperation, TypeError, ValueError):
            return Response({"error": "Invalid amount"}, status=status.HTTP_400_BAD_REQUEST)

        plan = SubscriptionPlan.objects.create(
            partner=partner,
            name=request.data["name"],
            amount=amount,
            period=request.data["period"],
        )
        return Response(serialize_plan(plan), status=status.HTTP_201_CREATED)


class PartnerPlanDetailView(APIView):
    permission_classes = [AllowAny]

    def put(self, request, plan_id):
        partner = get_partner_from_api_key(request)
        if partner is None:
            return Response({"error": "Invalid API key"}, status=status.HTTP_401_UNAUTHORIZED)

        plan = get_object_or_404(SubscriptionPlan, id=plan_id, partner=partner)
        if "name" in request.data:
            plan.name = request.data["name"]
        if "amount" in request.data:
            try:
                plan.amount = Decimal(str(request.data["amount"]))
            except (InvalidOperation, TypeError, ValueError):
                return Response({"error": "Invalid amount"}, status=status.HTTP_400_BAD_REQUEST)
        if "period" in request.data:
            plan.period = request.data["period"]
        if "is_active" in request.data:
            plan.is_active = parse_bool(request.data["is_active"])
        plan.save()

        return Response(serialize_plan(plan), status=status.HTTP_200_OK)

    def delete(self, request, plan_id):
        partner = get_partner_from_api_key(request)
        if partner is None:
            return Response({"error": "Invalid API key"}, status=status.HTTP_401_UNAUTHORIZED)

        plan = get_object_or_404(SubscriptionPlan, id=plan_id, partner=partner)
        plan.is_active = False
        plan.save(update_fields=["is_active"])
        return Response(serialize_plan(plan), status=status.HTTP_200_OK)


class PartnerPaymentsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        partner = get_partner_from_api_key(request)
        if partner is None:
            return Response({"error": "Invalid API key"}, status=status.HTTP_401_UNAUTHORIZED)

        payments = PaymentRequest.objects.filter(partner=partner).select_related("payer", "plan")
        payment_status = request.query_params.get("status")
        if payment_status:
            payments = payments.filter(status=payment_status)

        try:
            limit = int(request.query_params.get("limit", 20))
        except ValueError:
            limit = 20

        payments = payments.order_by("-created_at")[:limit]
        return Response(
            [serialize_partner_payment(payment) for payment in payments],
            status=status.HTTP_200_OK,
        )
