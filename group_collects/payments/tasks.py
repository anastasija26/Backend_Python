from celery import shared_task
from django.conf import settings
from django.core.mail import EmailMessage

@shared_task
def send_collect_created_email(author_email, author_name, collect_title):
    if not author_email:
        return

    subject = f"Создан сбор «{collect_title}»"
    message = (
        f"Добрый день, {author_name}.\n\n"
        f"Ваш сбор «{collect_title}» успешно создан."
    )

    email = EmailMessage(
        subject=subject,
        body=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[author_email],
    )
    email.send()

@shared_task
def send_payment_created_email(payment_user_email, payment_user_name, collect_title, amount):
    if not payment_user_email:
        return

    subject = f"Платёж в сбор «{collect_title}»"
    message = (
        f"Добрый день, {payment_user_name}.\n\n"
        f"Ваш платёж {amount} в сбор «{collect_title}» успешно создан."
    )

    email = EmailMessage(
        subject=subject,
        body=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[payment_user_email],
    )
    email.send()