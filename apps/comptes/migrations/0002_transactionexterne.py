import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('comptes', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='TransactionExterne',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('montant', models.DecimalField(decimal_places=2, max_digits=12)),
                ('type_transaction', models.CharField(
                    choices=[('credit', 'Crédit'), ('debit', 'Débit')],
                    max_length=10,
                )),
                ('description', models.CharField(max_length=255)),
                ('date', models.DateTimeField()),
                ('statut', models.CharField(
                    choices=[('completed', 'Complétée'), ('pending', 'En attente'), ('failed', 'Échouée')],
                    db_index=True,
                    default='completed',
                    max_length=20,
                )),
                ('reference', models.CharField(db_index=True, max_length=100, unique=True)),
                ('compte_externe', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='transactions_externes',
                    to='comptes.compteexterne',
                )),
            ],
            options={
                'verbose_name': 'Transaction Externe',
                'db_table': 'transactions_externes',
                'ordering': ['-date'],
            },
        ),
    ]
