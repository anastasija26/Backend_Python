from decimal import Decimal

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from payments.models import Collect, Payment

class Command(BaseCommand):
    help = "Наполняет БД тестовыми данными (сборы и платежи)."

    def add_arguments(self, parser):
        parser.add_argument("--users", type=int, default=10)
        parser.add_argument("--collects", type=int, default=50)
        parser.add_argument("--payments", type=int, default=2000)

    def handle(self, *args, **options):
        users_count = options["users"]
        collects_count = options["collects"]
        payments_count = options["payments"]

        self.stdout.write("Создание тестовых пользователей")
        users = []
        for i in range(users_count):
            username = f"user_{i}"
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    "email": f"{username}@example.com",
                    "first_name": f"Имя{i}",
                    "last_name": f"Фамилия{i}",
                },
            )
            if created:
                user.set_password("testpass123")
                user.save()
            users.append(user)

        self.stdout.write("Создание тестовых сборов")
        collects = []
        end_date = timezone.now() + timezone.timedelta(days=365)

        for i in range(collects_count):
            title = f"Сбор {i}"
            collect, created = Collect.objects.get_or_create(
                title=title,
                defaults={
                    "author": users[i % len(users)],
                    "reason": "birthday",
                    "description": f"Описание сбора {i}",
                    "target_amount": Decimal("10000.00"),
                    "end_date": end_date,
                    "status": "active",
                },
            )
            collects.append(collect)

        if not collects:
            self.stdout.write(self.style.WARNING("Сборы не созданы, платежи не будут добавлены."))
            return

        self.stdout.write("Создание тестовых платежей...")
        for i in range(payments_count):
            collect = collects[i % len(collects)]
            user = users[i % len(users)]
            Payment.objects.create(
                collect=collect,
                user=user,
                amount=Decimal("100.00"),
            )

        self.stdout.write(self.style.SUCCESS("Тестовые данные созданы."))