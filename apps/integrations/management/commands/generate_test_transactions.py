from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
import random

from apps.comptes.models import CompteExterne, TransactionExterne


class Command(BaseCommand):
    help = 'Générer des transactions de test pour un compte externe'

    def add_arguments(self, parser):
        parser.add_argument(
            '--compte-id',
            type=int,
            required=True,
            help='ID du compte externe'
        )
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Nombre de jours à remplir (défaut: 30)'
        )
        parser.add_argument(
            '--count',
            type=int,
            default=50,
            help='Nombre de transactions à générer (défaut: 50)'
        )

    def handle(self, *args, **options):
        compte_id = options['compte_id']
        days = options['days']
        count = options['count']

        try:
            compte = CompteExterne.objects.get(id=compte_id)
        except CompteExterne.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Compte {compte_id} not found'))
            return

        now = timezone.now()
        descriptions = [
            'Vente produits électroniques',
            'Paiement client - Service professionnel',
            'Versement client',
            'Paiement facture client',
            'Commande en ligne',
            'Frais bancaires',
            'Frais de transaction',
            'Retrait espèces',
            'Achat stock',
            'Paiement fournisseur',
            'Versement commercial',
            'Paiement international reçu',
            'Paiement précompte mobilier',
            'Remboursement',
            'Dividendes',
        ]

        created = 0
        for i in range(count):
            days_ago = random.randint(0, days)
            is_credit = random.choice([True, False])
            montant = random.randint(5000, 200000)

            ref_num = str(i + 1).zfill(4)
            reference = f'{compte.type_compte.upper()}-{compte_id}-{ref_num}'

            tx, created_flag = TransactionExterne.objects.get_or_create(
                reference=reference,
                defaults={
                    'compte_externe': compte,
                    'montant': montant,
                    'type_transaction': 'credit' if is_credit else 'debit',
                    'description': random.choice(descriptions),
                    'date': now - timedelta(days=days_ago, hours=random.randint(0, 23), minutes=random.randint(0, 59)),
                    'statut': random.choice(['completed', 'completed', 'completed', 'pending']),  # 75% completed
                }
            )

            if created_flag:
                created += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'✓ {created} transactions générées pour {compte.nom_banque} ({compte.numero_compte})'
            )
        )
