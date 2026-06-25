from decimal import Decimal, InvalidOperation

from django.db import transaction
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.transactions.models import Transaction
from apps.users.models import User
from apps.wallets.models import Wallet
from .models import InteropPartner, InteropTransaction


def get_partner(request):
    partner_key = request.headers.get("X-Partner-Key")
    if not partner_key:
        return None

    try:
        return InteropPartner.objects.get(partner_key=partner_key, is_active=True)
    except InteropPartner.DoesNotExist:
        return None


def get_user_name(user):
    return getattr(user, "full_name", None) or getattr(user, "nom", "") or user.email


def create_failed_interop_transaction(partner, user, amount, sender, reference):
    try:
        InteropTransaction.objects.create(
            partner=partner,
            receiver=user,
            amount=amount,
            sender_name=sender,
            reference=reference,
            status=InteropTransaction.Status.FAILED,
        )
    except Exception:
        pass


class VerifyUserView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        partner = get_partner(request)
        if partner is None:
            return Response({"error": "Cle partenaire invalide ou inactive."}, status=401)

        email = request.query_params.get("email")
        if not email:
            return Response({"error": "Parametre email requis."}, status=400)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {
                    "exists": False,
                    "error": "Aucun compte TrackPay trouve avec cet email.",
                },
                status=200,
            )

        return Response(
            {
                "exists": True,
                "name": get_user_name(user),
                "email": user.email,
            },
            status=200,
        )


class ReceiveTransferView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        partner = get_partner(request)
        if partner is None:
            return Response({"error": "Cle partenaire invalide ou inactive."}, status=401)

        required_fields = ["email", "amount", "sender", "reference"]
        missing_fields = [field for field in required_fields if not request.data.get(field)]
        if missing_fields:
            return Response(
                {"error": f"Champs manquants: {', '.join(missing_fields)}"},
                status=400,
            )

        email = request.data["email"]
        sender = request.data["sender"]
        reference = request.data["reference"]

        if (
            InteropTransaction.objects.filter(reference=reference).exists()
            or Transaction.objects.filter(reference=reference).exists()
        ):
            return Response({"error": "Reference deja utilisee."}, status=400)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {"error": "Aucun compte TrackPay trouve avec cet email."},
                status=404,
            )

        try:
            amount = Decimal(str(request.data["amount"]))
        except (InvalidOperation, TypeError, ValueError):
            return Response({"error": "Montant invalide."}, status=400)

        if amount <= 0:
            return Response({"error": "Montant invalide."}, status=400)

        try:
            with transaction.atomic():
                wallet = Wallet.objects.select_for_update().get(commercant=user)
                wallet.balance += amount
                wallet.save(update_fields=["balance", "updated_at"])

                InteropTransaction.objects.create(
                    partner=partner,
                    receiver=user,
                    amount=amount,
                    sender_name=sender,
                    reference=reference,
                    status=InteropTransaction.Status.SUCCESS,
                )

                Transaction.objects.create(
                    commercant=user,
                    wallet_expediteur=wallet,
                    wallet_recepteur=wallet,
                    montant=amount,
                    frais=0,
                    type=Transaction.Type.INTEROP_RECEIVED,
                    statut=Transaction.Statut.SUCCESS,
                    reference=reference,
                    description=f"Recu de {sender} via {partner.name}",
                )
        except Exception:
            create_failed_interop_transaction(partner, user, amount, sender, reference)
            return Response(
                {
                    "status": "FAILED",
                    "error": "Erreur lors du traitement.",
                },
                status=500,
            )

        return Response(
            {
                "status": "SUCCESS",
                "receiver": get_user_name(user),
                "email": user.email,
                "amount": str(amount),
                "reference": reference,
            },
            status=200,
        )
