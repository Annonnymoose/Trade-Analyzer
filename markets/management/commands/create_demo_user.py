from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Create demo user'

    def handle(self, *args, **options):
        # Create demo user
        demo_user, created = User.objects.get_or_create(
            username='demo',
            defaults={
                'email': 'demo@example.com',
                'is_staff': False,
                'is_superuser': False
            }
        )
        demo_user.set_password('demo123')
        demo_user.save()
        
        if created:
            self.stdout.write(self.style.SUCCESS('Successfully created demo user'))
        else:
            self.stdout.write(self.style.SUCCESS('Demo user already exists'))
            
        self.stdout.write(f'Username: demo')
        self.stdout.write(f'Password: demo123')
