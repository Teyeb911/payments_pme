import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('comptes', '0002_transactionexterne'),
    ]

    operations = [
        migrations.CreateModel(
            name='BankSync',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('status', models.CharField(
                    choices=[('pending', 'En attente'), ('syncing', 'En cours'), ('success', 'Succès'), ('failed', 'Échoué')],
                    default='pending',
                    max_length=20,
                )),
                ('last_sync_at', models.DateTimeField(blank=True, null=True)),
                ('last_successful_sync_at', models.DateTimeField(blank=True, null=True)),
                ('error_message', models.TextField(blank=True)),
                ('next_sync_at', models.DateTimeField(blank=True, null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('compte_externe', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='bank_sync',
                    to='comptes.compteexterne',
                )),
            ],
            options={
                'verbose_name': 'Bank Sync',
                'db_table': 'bank_syncs',
            },
        ),
        migrations.CreateModel(
            name='SyncLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('action', models.CharField(
                    choices=[('fetch', 'Récupération'), ('create', 'Création'), ('update', 'Mise à jour'), ('error', 'Erreur')],
                    max_length=20,
                )),
                ('message', models.TextField()),
                ('details', models.JSONField(blank=True, default=dict)),
                ('count', models.IntegerField(default=0)),
                ('bank_sync', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='logs',
                    to='integrations.banksync',
                )),
            ],
            options={
                'verbose_name': 'Sync Log',
                'db_table': 'sync_logs',
                'ordering': ['-created_at'],
            },
        ),
    ]
