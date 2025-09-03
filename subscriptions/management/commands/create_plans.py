from django.core.management.base import BaseCommand
from subscriptions.models import SubscriptionPlan

class Command(BaseCommand):
    help = 'Create subscription plans'

    def handle(self, *args, **options):
        plans = [
            {'name': 'monthly', 'price': 5.00, 'duration_days': 30},
            {'name': '6months', 'price': 20.00, 'duration_days': 180},
            {'name': 'yearly', 'price': 50.00, 'duration_days': 365},
        ]
        
        for plan_data in plans:
            plan, created = SubscriptionPlan.objects.get_or_create(
                name=plan_data['name'],
                defaults={
                    'price': plan_data['price'],
                    'duration_days': plan_data['duration_days']
                }
            )
            if created:
                self.stdout.write(f'Created plan: {plan.name}')
            else:
                self.stdout.write(f'Plan already exists: {plan.name}')