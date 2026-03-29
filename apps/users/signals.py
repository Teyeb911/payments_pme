from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model

User = get_user_model()


@receiver(post_save, sender=User)
def setup_commercant(sender, instance: User, created: bool, **kwargs):
    """
    À la création d'un commerçant :
      1. Crée son Wallet  (balance = 0)
      2. Souscrit au plan GRATUIT par défaut
    """
    if not created or not instance.is_commercant:
        return

    from apps.wallets.models import Wallet
    from apps.abonnements.models import Plan
    from apps.abonnements.services import AbonnementService

    Wallet.objects.create(commercant=instance)

    try:
        AbonnementService.souscrire(
            commercant=instance,
            plan_type='gratuit',
            auto_renouvellement=False,
        )
    except Plan.DoesNotExist:
        pass  # fixture pas encore chargée — ignoré
