from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.comptes.models import CompteExterne, TransactionExterne
from core.permissions import IsCommerçant
from core.utils import success_response
from .models import BankSync, SyncLog
from .serializers import BankSyncSerializer, SyncLogSerializer
from .services import SyncOrchestrator, SyncError


class SyncAccountView(APIView):
    """
    POST /api/v1/integrations/comptes/{id}/sync/
    Déclencher un sync manuel pour un compte externe.
    """
    permission_classes = [IsAuthenticated, IsCommerçant]

    def post(self, request, pk):
        compte = get_object_or_404(
            CompteExterne,
            id=pk,
            commercant=request.user,
        )

        try:
            result = SyncOrchestrator.sync_account(compte)
            return Response(
                success_response(
                    data=result,
                    message=f'{result["created"]} créées, {result["updated"]} mises à jour.',
                ),
                status=status.HTTP_200_OK,
            )
        except SyncError as e:
            return Response(
                {
                    'success': False,
                    'error': str(e),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )


class BankSyncStatusView(generics.RetrieveAPIView):
    """
    GET /api/v1/integrations/comptes/{id}/sync-status/
    État du dernier sync d'un compte.
    """
    serializer_class = BankSyncSerializer
    permission_classes = [IsAuthenticated, IsCommerçant]

    def get_object(self):
        compte = get_object_or_404(
            CompteExterne,
            id=self.kwargs['pk'],
            commercant=self.request.user,
        )
        return get_object_or_404(BankSync, compte_externe=compte)


class SyncLogListView(generics.ListAPIView):
    """
    GET /api/v1/integrations/comptes/{id}/sync-logs/
    Historique des syncs pour un compte.
    """
    serializer_class = SyncLogSerializer
    permission_classes = [IsAuthenticated, IsCommerçant]

    def get_queryset(self):
        compte = get_object_or_404(
            CompteExterne,
            id=self.kwargs['pk'],
            commercant=self.request.user,
        )
        bank_sync = get_object_or_404(BankSync, compte_externe=compte)
        return bank_sync.logs.all()


class ImportTransactionsView(APIView):
    """
    POST /api/v1/integrations/comptes/{id}/import/
    Importer des transactions depuis un fichier CSV.

    Format CSV attendu:
    reference,montant,type_transaction,description,date,statut
    REF-001,50000,credit,Vente produits,2026-06-01T10:00:00Z,completed
    """
    permission_classes = [IsAuthenticated, IsCommerçant]

    def post(self, request, pk):
        compte = get_object_or_404(
            CompteExterne,
            id=pk,
            commercant=request.user,
        )

        csv_file = request.FILES.get('file')
        if not csv_file:
            return Response(
                {'success': False, 'error': 'Aucun fichier fourni.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            import csv
            from io import TextIOWrapper
            from datetime import datetime

            created_count = 0
            error_rows = []

            # Lire le CSV
            text_file = TextIOWrapper(csv_file.file, encoding='utf-8')
            reader = csv.DictReader(text_file)

            for row_num, row in enumerate(reader, start=2):  # start=2 (skip header)
                try:
                    # Valider les champs requis
                    required = ['reference', 'montant', 'type_transaction', 'description', 'date', 'statut']
                    for field in required:
                        if field not in row or not row[field].strip():
                            error_rows.append({
                                'row': row_num,
                                'error': f'Champ manquant: {field}'
                            })
                            continue

                    # Parser les données
                    reference = row['reference'].strip()
                    montant = float(row['montant'])
                    type_tx = row['type_transaction'].strip()
                    description = row['description'].strip()
                    date_str = row['date'].strip()
                    statut = row['statut'].strip()

                    # Valider les enums
                    if type_tx not in ['credit', 'debit']:
                        error_rows.append({
                            'row': row_num,
                            'error': 'type_transaction doit être credit ou debit'
                        })
                        continue

                    if statut not in ['completed', 'pending', 'failed']:
                        error_rows.append({
                            'row': row_num,
                            'error': 'statut doit être completed, pending ou failed'
                        })
                        continue

                    # Parser la date
                    if 'T' in date_str:
                        tx_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    else:
                        tx_date = datetime.fromisoformat(date_str)

                    # Créer la transaction
                    _, created = TransactionExterne.objects.get_or_create(
                        reference=reference,
                        defaults={
                            'compte_externe': compte,
                            'montant': montant,
                            'type_transaction': type_tx,
                            'description': description,
                            'date': tx_date,
                            'statut': statut,
                        }
                    )

                    if created:
                        created_count += 1

                except (ValueError, KeyError) as e:
                    error_rows.append({
                        'row': row_num,
                        'error': str(e)
                    })

            return Response(
                success_response(
                    data={
                        'imported': created_count,
                        'errors': error_rows,
                    },
                    message=f'{created_count} transactions importées.' +
                            (f' {len(error_rows)} erreurs.' if error_rows else '')
                ),
                status=status.HTTP_200_OK if created_count > 0 else status.HTTP_400_BAD_REQUEST,
            )

        except Exception as e:
            return Response(
                {'success': False, 'error': f'Erreur CSV: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST,
            )
