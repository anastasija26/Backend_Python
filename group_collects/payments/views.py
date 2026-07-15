from django.core.cache import cache
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import Collect, Payment
from .permissions import IsAuthorOrReadOnly, IsPaymentOwnerOrReadOnly
from .serializers import (
    CollectCreateSerializer,
    CollectDetailSerializer,
    CollectListSerializer,
    CollectUpdateSerializer,
    PaymentCreateSerializer,
    PaymentSerializer,
    PaymentUpdateSerializer,
)
from .tasks import send_collect_created_email, send_payment_created_email


class CollectListCreateAPIView(generics.ListCreateAPIView):
    permission_classes = [AllowAny]

    def get_queryset(self):
        queryset = (
            Collect.objects.select_related("author")
            .prefetch_related("payments__user")
            .order_by("-created_at")
        )

        status_param = self.request.query_params.get("status")
        if status_param:
            queryset = queryset.filter(status=status_param)

        reason_param = self.request.query_params.get("reason")
        if reason_param:
            queryset = queryset.filter(reason=reason_param)

        return queryset

    def get_serializer_class(self):
        if self.request.method == "POST":
            return CollectCreateSerializer
        return CollectListSerializer

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated()]
        return [AllowAny()]

    def list(self, request, *args, **kwargs):
        cache_key = Collect.cache_list_key(request.query_params)
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return Response(cached_data)

        response = super().list(request, *args, **kwargs)
        cache.set(cache_key, response.data, timeout=60)
        return response

    def perform_create(self, serializer):
        collect = serializer.save(author=self.request.user)
        author = collect.author

        send_collect_created_email.delay(
            author.email,
            author.get_full_name() or author.username,
            collect.title,
        )

        cache.delete(Collect.cache_list_key())
        self._created_collect = collect

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        return Response(
            CollectDetailSerializer(self._created_collect).data,
            status=status.HTTP_201_CREATED,
        )


class CollectDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Collect.objects.select_related("author").prefetch_related("payments__user").all()
    permission_classes = [AllowAny]

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return CollectUpdateSerializer
        return CollectDetailSerializer

    def get_permissions(self):
        if self.request.method in ("PUT", "PATCH", "DELETE"):
            return [IsAuthenticated(), IsAuthorOrReadOnly()]
        return [AllowAny()]

    def retrieve(self, request, *args, **kwargs):
        collect = self.get_object()
        cache_key = collect.cache_detail_key()
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return Response(cached_data)

        response = super().retrieve(request, *args, **kwargs)
        cache.set(cache_key, response.data, timeout=60)
        return response

    def perform_update(self, serializer):
        old_instance = self.get_object()
        serializer.save()
        cache.delete(old_instance.cache_detail_key())
        cache.delete(Collect.cache_list_key())

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        self.check_object_permissions(request, instance)

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        updated = self.get_object()
        return Response(CollectDetailSerializer(updated).data)

    def destroy(self, request, *args, **kwargs):
        collect = self.get_object()
        self.check_object_permissions(request, collect)
        response = super().destroy(request, *args, **kwargs)

        cache.delete(collect.cache_detail_key())
        cache.delete(Collect.cache_list_key())
        cache.delete(collect.cache_payments_key())
        return response


class PaymentListCreateAPIView(generics.ListCreateAPIView):
    permission_classes = [AllowAny]

    def get_queryset(self):
        collect_id = self.kwargs["collect_id"]
        return (
            Payment.objects.filter(collect_id=collect_id)
            .select_related("user", "collect")
            .order_by("-created_at")
        )

    def get_serializer_class(self):
        if self.request.method == "POST":
            return PaymentCreateSerializer
        return PaymentSerializer

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated()]
        return [AllowAny()]

    def list(self, request, *args, **kwargs):
        collect = get_object_or_404(Collect, pk=self.kwargs["collect_id"])
        cache_key = collect.cache_payments_key()
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return Response(cached_data)

        response = super().list(request, *args, **kwargs)
        cache.set(cache_key, response.data, timeout=60)
        return response

    def perform_create(self, serializer):
        collect = get_object_or_404(Collect, pk=self.kwargs["collect_id"])

        payment = Payment.objects.create(
            collect=collect,
            user=self.request.user,
            amount=serializer.validated_data["amount"],
        )

        user = self.request.user
        send_payment_created_email.delay(
            user.email,
            user.get_full_name() or user.username,
            collect.title,
            str(payment.amount),
        )

        collect.update_current_amount()
        cache.delete(collect.cache_payments_key())
        cache.delete(collect.cache_detail_key())
        cache.delete(Collect.cache_list_key())

        self._created_payment = payment

    def create(self, request, *args, **kwargs):
        get_object_or_404(Collect, pk=self.kwargs["collect_id"])
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        self.perform_create(serializer)

        return Response(
            PaymentSerializer(self._created_payment).data,
            status=status.HTTP_201_CREATED,
        )


class PaymentDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Payment.objects.select_related("user", "collect").all()
    serializer_class = PaymentSerializer
    permission_classes = [AllowAny]

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return PaymentUpdateSerializer
        return PaymentSerializer

    def get_permissions(self):
        if self.request.method in ("PUT", "PATCH", "DELETE"):
            return [IsAuthenticated(), IsPaymentOwnerOrReadOnly()]
        return [AllowAny()]

    def update(self, request, *args, **kwargs):
        payment = self.get_object()
        self.check_object_permissions(request, payment)

        response = super().update(request, *args, **kwargs)

        payment.refresh_from_db()
        collect = payment.collect
        collect.update_current_amount()
        cache.delete(collect.cache_detail_key())
        cache.delete(collect.cache_payments_key())
        cache.delete(Collect.cache_list_key())
        return response

    def destroy(self, request, *args, **kwargs):
        payment = self.get_object()
        self.check_object_permissions(request, payment)

        collect = payment.collect
        response = super().destroy(request, *args, **kwargs)

        collect.update_current_amount()
        cache.delete(collect.cache_detail_key())
        cache.delete(collect.cache_payments_key())
        cache.delete(Collect.cache_list_key())
        return response

