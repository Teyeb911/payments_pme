from django.db import migrations

def ajouter_plans(apps, schema_editor):
    Plan = apps.get_model('abonnements', 'Plan')
    
    plans = [
        {'type': 'gratuit', 'prix_mensuel': 0, 'description': 'Pour démarrer', 'nb_comptes_max': 1},
        {'type': 'basic', 'prix_mensuel': 99, 'description': 'Pour les petits commerces', 'nb_comptes_max': 3},
        {'type': 'pro', 'prix_mensuel': 299, 'description': 'Pour les professionnels', 'nb_comptes_max': 10},
        {'type': 'enterprise', 'prix_mensuel': 599, 'description': 'Pour les grandes entreprises', 'nb_comptes_max': 100},
    ]
    
    for plan_data in plans:
        Plan.objects.get_or_create(
            type=plan_data['type'],
            defaults=plan_data
        )

class Migration(migrations.Migration):
    dependencies = [
        ('abonnements', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(ajouter_plans),
    ]
