from decimal import Decimal
from pathlib import Path

from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Sum
from django.db.models.signals import pre_save, post_delete
from django.dispatch import receiver
from django.utils import timezone

def validate_future_datetime(value):
    if value and value <= timezone.now():
        raise ValidationError("Дата завершения должна быть в будущем.")

class Collect(models.Model):
    REASON_CHOICES = [
        ("birthday", "День рождения"),
        ("wedding", "Свадьба"),
        ("charity", "Благотворительность"),
        ("other", "Другое"),
    ]

    STATUS_CHOICES = [
        ("active", "Активен"),
        ("completed", "Завершён"),
        ("cancelled", "Отменён"),
    ]

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="collects",
        verbose_name="Автор сбора",
    )
    title = models.CharField("Название", max_length=200)
    reason = models.CharField(
        "Повод",
        max_length=20,
        choices=REASON_CHOICES,
        default="other",
    )
    description = models.TextField("Описание", blank=True)
    target_amount = models.DecimalField(
        "Планируемая сумма",
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    current_amount = models.DecimalField(
        "Собрано",
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        editable=False,
    )
    cover = models.ImageField(
        "Обложка",
        upload_to="collects/covers/",
        null=True,
        blank=True,
    )
    end_date = models.DateTimeField(
        "Дата и время завершения",
        null=True,
        blank=True,
        validators=[validate_future_datetime],
    )
    status = models.CharField(
        "Статус",
        max_length=20,
        choices=STATUS_CHOICES,
        default="active",
    )
    created_at = models.DateTimeField("Создано", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлено", auto_now=True)

    class Meta:
        verbose_name = "Групповой сбор"
        verbose_name_plural = "Групповые сборы"
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return self.title

    def clean(self):
        super().clean()
        if self.end_date and self.end_date <= timezone.now():
            raise ValidationError({"end_date": "Дата завершения должна быть в будущем."})
        if self.target_amount is not None and self.target_amount < 0:
            raise ValidationError({"target_amount": "Сумма не может быть отрицательной."})

    def is_active(self):
        if self.status != "active":
            return False
        if self.end_date and self.end_date <= timezone.now():
            return False
        if self.target_amount is not None and self.current_amount >= self.target_amount:
            return False
        return True

    def update_current_amount(self):
        total = self.payments.aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
        Collect.objects.filter(pk=self.pk).update(current_amount=total)
        self.current_amount = total
        cache.delete(self.cache_detail_key())
        cache.delete(self.cache_list_key())
        cache.delete(self.cache_payments_key())

    def cache_detail_key(self):
        return f"collect:{self.pk}"

    def cache_payments_key(self):
        return f"collect:{self.pk}:payments"

    @staticmethod
    def cache_list_key(query_params=None):
        if not query_params:
            return "collects:list"
        status = query_params.get("status", "")
        reason = query_params.get("reason", "")
        return f"collects:list:status={status}:reason={reason}"

class Payment(models.Model):
    collect = models.ForeignKey(
        Collect,
        on_delete=models.CASCADE,
        related_name="payments",
        verbose_name="Сбор",
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="payments",
        verbose_name="Пользователь",
    )
    amount = models.DecimalField(
        "Сумма",
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    created_at = models.DateTimeField("Дата и время", auto_now_add=True)

    class Meta:
        verbose_name = "Платёж"
        verbose_name_plural = "Платежи"
        indexes = [
            models.Index(fields=["collect", "created_at"]),
            models.Index(fields=["user", "created_at"]),
        ]

    def __str__(self):
        return f"{self.user.get_full_name()} -> {self.collect.title} ({self.amount})"

    def clean(self):
        super().clean()
        if not self.collect.is_active():
            raise ValidationError({"collect": "Сбор закрыт или завершён."})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
        self.collect.update_current_amount()

    def delete(self, *args, **kwargs):
        collect = self.collect
        super().delete(*args, **kwargs)
        collect.update_current_amount()

@receiver(pre_save, sender=Collect)
def delete_old_cover_on_update(sender, instance, **kwargs):
    if not instance.pk:
        return
    try:
        old_instance = Collect.objects.get(pk=instance.pk)
    except Collect.DoesNotExist:
        return
    old_file = old_instance.cover
    new_file = instance.cover
    if old_file and old_file.name and old_file.name != getattr(new_file, "name", None):
        old_path = old_file.path
        if old_path and Path(old_path).exists():
            old_file.delete(save=False)

@receiver(post_delete, sender=Collect)
def delete_collect_cover(sender, instance, **kwargs):
    if instance.cover:
        instance.cover.delete(save=False)