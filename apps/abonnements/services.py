from datetime import date
from dateutil.relativedelta import relativedelta
from django.core.exceptions import ValidationError  # ✅ أضف هذا

from .models import Abonnement, Plan
from apps.wallets.models import Wallet
from apps.users.models import User


class AbonnementService:

    @staticmethod
    def souscrire(commercant, plan_type: str, auto_renouvellement: bool = True) -> Abonnement:
        plan = Plan.objects.get(type=plan_type, is_actif=True)
        
        # ✅ التحقق من الرصيد
        if commercant.wallet.balance < plan.prix_mensuel:
            raise ValidationError(f"Solde insuffisant. Vous avez {commercant.wallet.balance} MRU, besoin de {plan.prix_mensuel} MRU.")
        
        # ✅ خصم من المستخدم
        commercant.wallet.balance -= plan.prix_mensuel
        commercant.wallet.save()
        
        # ✅ إضافة إلى الأدمن
        admin = User.objects.filter(role='admin').first()
        if admin:
            admin.wallet.balance += plan.prix_mensuel
            admin.wallet.save()
        
        # ✅ إنشاء الاشتراك
        abonnement, created = Abonnement.objects.update_or_create(
            commercant=commercant,
            defaults={
                'plan': plan,
                'statut': Abonnement.Statut.ACTIF,
                'date_expiration': date.today() + relativedelta(months=1),
                'auto_renouvellement': auto_renouvellement,
            },
        )
        return abonnement

    @staticmethod
    def resilier(abonnement: Abonnement) -> Abonnement:
        abonnement.statut = Abonnement.Statut.RESILIÉ
        abonnement.auto_renouvellement = False
        abonnement.save(update_fields=['statut', 'auto_renouvellement', 'updated_at'])
        return abonnement

    @staticmethod
    def renouveler(abonnement: Abonnement) -> Abonnement:
        plan = abonnement.plan
        commercant = abonnement.commercant
        
        if commercant.wallet.balance < plan.prix_mensuel:
            raise ValidationError("Solde insuffisant pour le renouvellement.")
        
        commercant.wallet.balance -= plan.prix_mensuel
        commercant.wallet.save()
        
        admin = User.objects.filter(role='admin').first()
        if admin:
            admin.wallet.balance += plan.prix_mensuel
            admin.wallet.save()
        
        abonnement.statut = Abonnement.Statut.ACTIF
        abonnement.date_expiration = date.today() + relativedelta(months=1)
        abonnement.save(update_fields=['statut', 'date_expiration', 'updated_at'])
        return abonnement
