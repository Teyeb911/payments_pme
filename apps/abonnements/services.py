from datetime import date
from dateutil.relativedelta import relativedelta
from django.core.exceptions import ValidationError

from .models import Abonnement, Plan


class AbonnementService:

    @staticmethod
    def souscrire(commercant, plan_type: str, auto_renouvellement: bool = True) -> Abonnement:
        plan = Plan.objects.get(type=plan_type, is_actif=True)
        
        # ✅ التحقق من الرصيد
        if commercant.wallet.balance < plan.prix_mensuel:
            raise ValidationError("Solde insuffisant.")
        
        # ✅ خصم من المستخدم
        commercant.wallet.balance -= plan.prix_mensuel
        commercant.wallet.save()
        
        # ✅ إضافة إلى الأدمن (إذا وجد)
        try:
            from apps.users.models import User
            admin = User.objects.filter(role='admin').first()
            if admin:
                admin.wallet.balance += plan.prix_mensuel
                admin.wallet.save()
        except Exception as e:
            print(f"⚠️ لم نتمكن من إضافة المبلغ للأدمن: {e}")
        
        # ✅ إنشاء الاشتراك (نفس الكود الأصلي)
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
        
        try:
            from apps.users.models import User
            admin = User.objects.filter(role='admin').first()
            if admin:
                admin.wallet.balance += plan.prix_mensuel
                admin.wallet.save()
        except Exception as e:
            print(f"⚠️ لم نتمكن من إضافة المبلغ للأدمن: {e}")
        
        abonnement.statut = Abonnement.Statut.ACTIF
        abonnement.date_expiration = date.today() + relativedelta(months=1)
        abonnement.save(update_fields=['statut', 'date_expiration', 'updated_at'])
        return abonnement
