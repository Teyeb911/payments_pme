import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Crée un superuser depuis les variables d\'environnement ADMIN_EMAIL et ADMIN_PASSWORD'

    def handle(self, *args, **kwargs):
        email    = os.environ.get('ADMIN_EMAIL')
        password = os.environ.get('ADMIN_PASSWORD')

        if not email or not password:
            self.stdout.write(self.style.WARNING(
                'ADMIN_EMAIL ou ADMIN_PASSWORD non défini — admin non créé.'
            ))
            return

        if User.objects.filter(email=email).exists():
            self.stdout.write(self.style.SUCCESS(f'Admin {email} existe déjà.'))
            return

        User.objects.create_superuser(email=email, password=password)
        self.stdout.write(self.style.SUCCESS(f'Superuser {email} créé avec succès.'))
