from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework import serializers

from .models import Collect, Payment


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "username", "first_name", "last_name", "full_name"]

    def get_full_name(self, obj):
        full_name = obj.get_full_name().strip()
        return full_name or obj.username


class PaymentSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    collect_id = serializers.IntegerField(source="collect.id", read_only=True)
    collect_title = serializers.CharField(source="collect.title", read_only=True)

    class Meta:
        model = Payment
        fields = ["id", "collect_id", "collect_title", "user", "amount", "created_at"]


class PaymentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ["amount"]

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Сумма платежа должна быть больше нуля.")
        return value


class PaymentUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ["amount"]

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Сумма платежа должна быть больше нуля.")
        return value


class CollectListSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    current_amount = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = Collect
        fields = [
            "id",
            "author",
            "title",
            "reason",
            "current_amount",
            "status",
            "end_date",
            "created_at",
        ]


class CollectDetailSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    payments = serializers.SerializerMethodField()
    current_amount = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = Collect
        fields = [
            "id",
            "author",
            "title",
            "reason",
            "description",
            "target_amount",
            "current_amount",
            "cover",
            "end_date",
            "status",
            "created_at",
            "updated_at",
            "payments",
        ]

    def get_payments(self, obj):
        queryset = obj.payments.select_related("user").order_by("-created_at")
        return PaymentSerializer(queryset, many=True).data


class CollectCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Collect
        fields = [
            "title",
            "reason",
            "description",
            "target_amount",
            "cover",
            "end_date",
            "status",
        ]

    def validate_end_date(self, value):
        if value and value <= timezone.now():
            raise serializers.ValidationError("Дата завершения должна быть в будущем.")
        return value

    def validate_target_amount(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("Сумма не может быть отрицательной.")
        return value


class CollectUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Collect
        fields = [
            "title",
            "reason",
            "description",
            "target_amount",
            "cover",
            "end_date",
            "status",
        ]

    def validate_end_date(self, value):
        if value and value <= timezone.now():
            raise serializers.ValidationError("Дата завершения должна быть в будущем.")
        return value

    def validate_target_amount(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("Сумма не может быть отрицательной.")
        return value
