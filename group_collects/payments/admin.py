from django.contrib import admin

from .models import Collect, Payment

@admin.register(Collect)
class CollectAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "author",
        "reason",
        "status",
        "current_amount",
        "target_amount",
        "end_date",
        "created_at",
    )
    list_filter = ("status", "reason", "created_at")
    search_fields = ("title", "description", "author__username", "author__first_name", "author__last_name")
    readonly_fields = ("current_amount", "created_at", "updated_at")

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("id", "collect", "user", "amount", "created_at")
    list_filter = ("created_at",)
    search_fields = ("collect__title", "user__username", "user__first_name", "user__last_name")

