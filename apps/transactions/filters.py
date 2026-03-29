import django_filters
from .models import Transaction


class TransactionFilter(django_filters.FilterSet):
    date_debut = django_filters.DateFilter(field_name='created_at', lookup_expr='date__gte')
    date_fin   = django_filters.DateFilter(field_name='created_at', lookup_expr='date__lte')
    type       = django_filters.ChoiceFilter(choices=Transaction.Type.choices)
    statut     = django_filters.ChoiceFilter(choices=Transaction.Statut.choices)
    montant_min = django_filters.NumberFilter(field_name='montant', lookup_expr='gte')
    montant_max = django_filters.NumberFilter(field_name='montant', lookup_expr='lte')

    class Meta:
        model  = Transaction
        fields = ['type', 'statut', 'date_debut', 'date_fin', 'montant_min', 'montant_max']
