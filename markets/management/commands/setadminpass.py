from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password

class Command(BaseCommand):
    help = 'Set default password for admin user'

    def handle(self, *args, **options):
        admin = User.objects.filter(username='admin').first()
        if admin:
            admin.password = make_password('admin123')
            admin.save()
            self.stdout.write(self.style.SUCCESS('Successfully set password for admin user'))
        else:
            admin = User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
            self.stdout.write(self.style.SUCCESS('Successfully created admin user'))
