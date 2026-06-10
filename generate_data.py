#!/usr/bin/env python
import os
import sys
import django
from datetime import timedelta
import random

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, '/home/projects')
django.setup()

from django.utils import timezone
from apps.comptes.models import CompteExterne, TransactionExterne

# Paramètres
COMPTE_ID = 1
DAYS = 30
COUNT = 20

try:
    compte = CompteExterne.objects.get(id=COMPTE_ID)
    print(f"✓ Compte trouvé : {compte.nom_banque} ({compte.numero_compte})")
except CompteExterne.DoesNotExist:
    print(f"✗ Compte {COMPTE_ID} introuvable")
    sys.exit(1)

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
]

created = 0
for i in range(COUNT):
    days_ago = random.randint(0, DAYS)
    is_credit = random.choice([True, False])
    montant = random.randint(5000, 200000)

    ref_num = str(i + 1).zfill(4)
    reference = f'TEST-{COMPTE_ID}-{ref_num}'

    tx, created_flag = TransactionExterne.objects.get_or_create(
        reference=reference,
        defaults={
            'compte_externe': compte,
            'montant': montant,
            'type_transaction': 'credit' if is_credit else 'debit',
            'description': random.choice(descriptions),
            'date': now - timedelta(days=days_ago, hours=random.randint(0, 23), minutes=random.randint(0, 59)),
            'statut': random.choice(['completed', 'completed', 'completed', 'pending']),
        }
    )

    if created_flag:
        created += 1
        print(f"  ✓ TX {i+1}/{COUNT} : {reference} — {montant} UM ({tx.type_transaction})")

print(f"\n✓✓✓ {created} transactions générées pour {compte.nom_banque}")
